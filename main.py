"""
FPL assistant + OpenAI fallback chatbot.
Flask web server for chatroom interface.
"""
import os
import re
import requests
import difflib
from datetime import timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
from openai import OpenAI
from werkzeug.security import generate_password_hash, check_password_hash
from database import (
    initialize_database,
    create_user,
    find_user,
    save_chat,
    create_chat_session,
    list_chat_sessions,
    get_chat_history,
    get_chat_session,
)

# Load environment variables
load_dotenv()

# Initialize OpenAI client (optional, for general chat mode)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: OPENAI_API_KEY not found. General chat features will be limited.")
    client = None
else:
    # client = OpenAI(api_key=api_key)
    client = None

# Initialize database using the provided token
try:
    db_connection = initialize_database(api_key)
    db_connection.close()
except RuntimeError as e:
    print(f"Database initialization warning: {e}")


def authenticate_user(username: str, password: str) -> bool:
    stored_hash = find_user(username)
    if not stored_hash:
        return False
    return check_password_hash(stored_hash, password)


def validate_password(password: str) -> str:
    """Validate password strength and return error message or empty string if valid."""
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r'[A-Z]', password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return "Password must contain at least one number."
    return ""


def register_user(username: str, password: str) -> bool:
    return create_user(username, generate_password_hash(password))

class FPLClient:
    BASE = "https://fantasy.premierleague.com/api"
    POSITION_LABELS = {
        1: 'Goalkeeper',
        2: 'Defender',
        3: 'Midfielder',
        4: 'Forward'
    }
    POSITION_KEYWORD_MAP = {
        'goalkeeper': 1,
        'keeper': 1,
        'gk': 1,
        'defender': 2,
        'defence': 2,
        'defense': 2,
        'def': 2,
        'midfielder': 3,
        'midfield': 3,
        'mid': 3,
        'forward': 4,
        'striker': 4,
        'attacker': 4,
        'fw': 4
    }

    def __init__(self):
        self.static = self._get(f"{self.BASE}/bootstrap-static/")
        self.players = self.static.get("elements", [])
        self.teams = {t["id"]: t for t in self.static.get("teams", [])}

    def _get(self, url):
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return response.json()

    def _normalize(self, text: str) -> str:
        return text.lower().strip()

    def find_player(self, name: str):
        name_key = self._normalize(name)
        candidates = [p for p in self.players if name_key in self._normalize(f"{p['first_name']} {p['second_name']}")]
        if candidates:
            return candidates[0]

        names = [f"{p['first_name']} {p['second_name']}" for p in self.players]
        best = difflib.get_close_matches(name, names, n=1, cutoff=0.6)
        if best:
            for p in self.players:
                full = f"{p['first_name']} {p['second_name']}"
                if full == best[0]:
                    return p

        return None

    def extract_player_names(self, text, max_results=2):
        text_norm = self._normalize(text)
        candidates = []
        tokens = re.findall(r"[A-Za-z']+", text)

        for n in (3, 2, 1):
            for i in range(len(tokens) - n + 1):
                phrase = " ".join(tokens[i:i + n])
                if len(phrase) < 2:
                    continue
                player = self.find_player(phrase)
                if player:
                    full_name = f"{player['first_name']} {player['second_name']}"
                    if full_name not in candidates:
                        candidates.append(full_name)
                        if len(candidates) >= max_results:
                            return candidates

        for p in self.players:
            full_name = f"{p['first_name']} {p['second_name']}"
            if full_name.lower() in text_norm or p['second_name'].lower() in text_norm:
                if full_name not in candidates:
                    candidates.append(full_name)
                    if len(candidates) >= max_results:
                        return candidates

        return candidates

    def get_history(self, player_id: int):
        return self._get(f"{self.BASE}/element-summary/{player_id}/")

    def summarize_player(self, player):
        team = self.teams.get(player.get("team"), {}).get("name", "Unknown")
        status = player.get("status", "NA")
        form = float(player.get("form", 0.0))
        now_cost = player.get("now_cost", 0) / 10

        return {
            "name": f"{player.get('first_name')} {player.get('second_name')}",
            "team": team,
            "position": player.get("element_type"),
            "status": status,
            "points": player.get("total_points"),
            "points_per_game": float(player.get("points_per_game", 0.0)),
            "form": form,
            "value": now_cost,
            "minutes": player.get("minutes"),
            "selected_by": player.get("selected_by_percent")
        }

    def compare_players(self, names):
        result = []
        for name in names:
            p = self.find_player(name)
            if not p:
                result.append({"name": name, "error": "Player not found."})
                continue
            summary = self.summarize_player(p)
            hist = self.get_history(p["id"])
            recent = hist.get("history", [])[-3:]
            summary["recent_points"] = [int(x.get("total_points", 0)) for x in recent]
            summary["recent_form"] = [float(x.get("form", 0.0)) for x in recent]
            result.append(summary)

        return result

    def best_player_by_position(self, position_name: str):
        if not position_name:
            return "Please specify a position such as goalkeeper, defender, midfielder, striker, or forward."

        position_key = position_name.lower()
        position_id = self.POSITION_KEYWORD_MAP.get(position_key)
        if position_id is None:
            return f"I couldn't recognize the position '{position_name}'. Try goalkeeper, defender, midfielder, striker, or forward."

        candidates = [p for p in self.players if p.get('element_type') == position_id]
        if not candidates:
            return f"No players were found for position '{position_name}'."

        top_players = sorted(
            candidates,
            key=lambda p: (
                int(p.get('total_points', 0)),
                float(p.get('form', 0.0)),
                int(p.get('minutes', 0))
            ),
            reverse=True
        )[:3]

        position_label = self.POSITION_LABELS.get(position_id, position_name.title())
        if position_key in ['striker', 'attacker', 'fw']:
            position_label = 'Striker'

        lines = [f"Top {len(top_players)} {position_label}s:" ]
        for idx, player in enumerate(top_players, start=1):
            summary = self.summarize_player(player)
            lines.append(
                f"{idx}. {summary['name']} ({summary['team']}) - "
                f"PTS {summary['points']}, Form {summary['form']}, PPG {summary['points_per_game']}, "
                f"£{summary['value']:.1f}m, {summary['minutes']} mins, {summary['selected_by']}% selected"
            )

        return "\n".join(lines)

    def injury_report(self, name):
        p = self.find_player(name)
        if not p:
            return f"Player '{name}' not found."

        status = p.get("status", "NA")
        now_cost = p.get("now_cost", 0) / 10
        team = self.teams.get(p.get("team"), {}).get("name", "Unknown")
        news = p.get("news", "No news available.")

        return (
            f"{p['first_name']} {p['second_name']} ({team})\n"
            f"Status: {status}\n"
            f"Injury/News: {news}\n"
            f"Price: £{now_cost:.1f}\n"
            f"Total points {p.get('total_points')} | form {p.get('form')} | minutes {p.get('minutes')}"
        )

    def form_report(self, name):
        p = self.find_player(name)
        if not p:
            return f"Player '{name}' not found."

        hist = self.get_history(p["id"]) if p else {"history": []}
        recent = hist.get("history", [])[-5:]
        if not recent:
            return "No fixture history found."

        points = [int(x.get("total_points", 0)) for x in recent]
        form_vals = [float(x.get("form", 0.0)) for x in recent]
        avg_points = sum(points) / len(points)
        avg_form = sum(form_vals) / len(form_vals)

        return (
            f"{p['first_name']} {p['second_name']} form summary:\n"
            f"Recent match points: {points}\n"
            f"Recent form values: {form_vals}\n"
            f"Average points (last {len(points)}): {avg_points:.2f}\n"
            f"Average form (last {len(form_vals)}): {avg_form:.2f}\n"
            f"Overall form stat: {p.get('form', '0.0')}"
        )

    def team_suggestions(self, top_n=5):
        eligible = sorted(self.players, key=lambda p: float(p.get("form", 0.0)), reverse=True)
        top = eligible[:top_n]

        lines = []
        for p in top:
            lines.append(
                f"{p['first_name']} {p['second_name']} - {p.get('now_cost', 0)/10:.1f}m - "
                f"{p.get('total_points', 0)} pts - form {p.get('form', '0.0')}"
            )

        return "\n".join(lines)


def parse_message_intent(text):
    normalized = text.lower().strip()
    if not normalized:
        return "help", None

    if normalized in ["help", "commands"]:
        return "help", None

    if normalized.startswith("compare ") or " who is better " in normalized or " vs " in normalized or " versus " in normalized or " compare " in normalized:
        names = fpl.extract_player_names(text, max_results=2)
        return "compare", names

    if any(keyword in normalized for keyword in ["injury", "injuries", "injured", "status", "fit", "out", "doubt"]):
        names = fpl.extract_player_names(text, max_results=1)
        return "injuries", names

    if any(keyword in normalized for keyword in ["form", "playing", "performance", "recent", "ppg", "points"]) and "suggest" not in normalized:
        names = fpl.extract_player_names(text, max_results=1)
        return "form", names

    if any(keyword in normalized for keyword in ["suggest", "recommend", "best pick", "top players", "who should i", "transfer", "buy", "sell", "pick"]):
        digit = re.search(r"\b(\d+)\b", normalized)
        top_n = int(digit.group(1)) if digit else 5
        return "suggest", top_n

    position_keywords = [
        'goalkeeper', 'keeper', 'gk',
        'defender', 'defence', 'defense', 'def',
        'midfielder', 'midfield', 'mid',
        'forward', 'striker', 'attacker', 'fw'
    ]
    if any(keyword in normalized for keyword in ["best", "top"]) and any(pos in normalized for pos in position_keywords):
        for pos in position_keywords:
            if pos in normalized:
                return "best_position", pos

    if normalized.startswith("chat "):
        return "chat", text[len("chat "):].strip()

    return "chat", text


def gpt_fallback(user_message: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}],
            max_tokens=250,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"OpenAI fallback failed: {e}"


def print_help():
    return """Fantasy Premier League assistant help:
  Ask naturally like: "Compare Salah and Mane" or "How is Haaland playing?"
  compare <name1>,<name2> - Compare two players by stats
  best <position> - Find the top 3 players in a role (striker, midfielder, defender, goalkeeper)
  injuries <name> - Check injury/status/news for a player
  form <name> - Show recent form for a player
  suggest <N> - Top N players by current form
  chat <text> - Ask general questions (OpenAI fallback)
  help - Show this help text
  quit / exit - Close the bot"""


def process_command(text):
    """Process a command or natural language query and return a response."""
    if not text:
        return "Please enter a message."

    cmd = text.split()[0].lower()
    args = text[len(cmd):].strip()

    if cmd in ["quit", "exit", "q"]:
        return "Goodbye and best of luck this gameweek!"

    if cmd == "help":
        return print_help()

    if cmd == "compare":
        names = [n.strip() for n in args.split(",") if n.strip()]
        if len(names) < 2:
            return "Usage: compare <name1>,<name2>"

        table = fpl.compare_players(names[:2])
        responses = []
        for row in table:
            if "error" in row:
                responses.append(row["error"])
                continue
            responses.append(
                f"\n{row['name']} ({row['team']})"
                f"\n  Total points: {row['points']}, PPG: {row['points_per_game']}, form: {row['form']}"
                f"\n  Recent points: {row['recent_points']}, recent form: {row['recent_form']}"
            )
        return "\n".join(responses)

    if cmd == "injuries":
        if not args:
            return "Usage: injuries <player name>"
        return fpl.injury_report(args)

    if cmd == "form":
        if not args:
            return "Usage: form <player name>"
        return fpl.form_report(args)

    if cmd == "suggest":
        top_n = 5
        if args.isdigit():
            top_n = int(args)
        return f"Top suggestions by current FPL form:\n{fpl.team_suggestions(top_n)}"

    if cmd == "best":
        if not args:
            return "Usage: best <position> (e.g. striker, midfielder, defender, goalkeeper)"
        return fpl.best_player_by_position(args.strip())

    if cmd == "chat":
        query = args.strip()
        if not query:
            return "Usage: chat <question text>"
        return gpt_fallback(query)

    intent, payload = parse_message_intent(text)

    if intent == "compare":
        if not payload or len(payload) < 2:
            return "I can compare players for you. Please name two players, for example: Compare Salah and Mane."
        table = fpl.compare_players(payload[:2])
        responses = []
        for row in table:
            if "error" in row:
                responses.append(row["error"])
                continue
            responses.append(
                f"\n{row['name']} ({row['team']})"
                f"\n  Total points: {row['points']}, PPG: {row['points_per_game']}, form: {row['form']}"
                f"\n  Recent points: {row['recent_points']}, recent form: {row['recent_form']}"
            )
        return "\n".join(responses)

    if intent == "injuries":
        if not payload:
            return "Tell me the player you want injury status for, for example: Is Haaland injured?"
        return fpl.injury_report(payload[0])

    if intent == "form":
        if not payload:
            return "Tell me the player you want form information for, for example: How is Salah playing?"
        return fpl.form_report(payload[0])

    if intent == "suggest":
        top_n = payload if isinstance(payload, int) else 5
        return f"Top suggestions by current FPL form:\n{fpl.team_suggestions(top_n)}"

    if intent == "chat":
        if client is None:
            return (
                "I can answer FPL questions directly. Try asking about player form, injuries, comparisons, or suggestions. "
                "If you want full conversational AI, enable OpenAI in your .env."
            )
        return gpt_fallback(payload)

    return "Sorry, I didn't understand that. Try asking naturally about player form, injury status, or transfers."


# Flask app
app = Flask(__name__, template_folder='.', static_folder='static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecretkey123')
app.permanent_session_lifetime = timedelta(days=7)
fpl = FPLClient()

@app.route('/')
def home():
    username = session.get('username', 'guest')
    if not session.get('active_session_id'):
        existing = list_chat_sessions(username)
        if existing:
            set_active_session_id(existing[0]['id'])
        else:
            set_active_session_id(create_chat_session(username, 'New Chat'))

    return render_template('index.html', username=session.get('username'))

def get_active_session_id():
    return session.get('active_session_id')


def set_active_session_id(session_id: int):
    session['active_session_id'] = session_id


@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '').strip()
    username = session.get('username', 'guest')
    session_id = data.get('session_id') or get_active_session_id()

    if not message:
        return jsonify({'response': 'Please enter a message.'})

    if not session_id:
        return jsonify({'response': 'No active chat session. Create a new chat first.'}), 400

    save_chat(session_id, username, 'user', message)
    try:
        response = process_command(message)
        save_chat(session_id, username, 'bot', response)
        return jsonify({'response': response})
    except Exception as e:
        error_message = f'Error: {str(e)}'
        save_chat(session_id, username, 'bot', error_message)
        return jsonify({'response': error_message})


@app.route('/sessions', methods=['GET', 'POST'])
def sessions():
    username = session.get('username', 'guest')
    if request.method == 'GET':
        sessions = list_chat_sessions(username)
        return jsonify({
            'sessions': sessions,
            'active_session_id': get_active_session_id()
        })

    data = request.get_json() or {}
    name = data.get('name', 'New Chat').strip() or 'New Chat'
    session_id = create_chat_session(username, name)
    set_active_session_id(session_id)
    return jsonify({'session_id': session_id, 'name': name})


@app.route('/sessions/<int:session_id>/history', methods=['GET'])
def session_history(session_id):
    username = session.get('username', 'guest')
    session_obj = get_chat_session(session_id)
    if not session_obj:
        return jsonify({'error': 'Session not found.'}), 404

    if session_obj['username'] != username:
        return jsonify({'error': 'Forbidden'}), 403

    history = get_chat_history(session_id)
    return jsonify({'session': session_obj, 'history': history})


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        remember = request.form.get('remember') == 'on'
        if not username or not password:
            error = 'Please provide both username and password.'
        elif authenticate_user(username, password):
            session['username'] = username
            session.pop('active_session_id', None)
            session.permanent = remember
            return redirect(url_for('home'))
        else:
            error = 'Invalid username or password.'
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm', '').strip()
        if not username or not password or not confirm:
            error = 'All fields are required.'
        elif len(username) < 3:
            error = 'Username must be at least 3 characters long.'
        elif password != confirm:
            error = 'Passwords do not match.'
        else:
            password_error = validate_password(password)
            if password_error:
                error = password_error
            elif not register_user(username, password):
                error = 'That username already exists.'
            else:
                session['username'] = username
                session.pop('active_session_id', None)
                return redirect(url_for('home'))
    return render_template('register.html', error=error)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('active_session_id', None)
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)