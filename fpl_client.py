"""
FPL API Client Module
Handles all FPL data fetching and processing.
"""
import requests
import difflib

class FPLClient:
    BASE = "https://fantasy.premierleague.com/api"

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