"""
Chatbot Module
Handles OpenAI integration and fallback responses.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY must be set in .env or environment variables")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

def gpt_fallback(user_message: str) -> str:
    """Send message to OpenAI as fallback."""
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
    """Print available commands."""
    print("\nFantasy Premier League assistant commands:")
    print("  compare <name1>,<name2> - Compare two players by stats")
    print("  injuries <name> - Check injury/status/news for a player")
    print("  form <name> - Show recent form for a player")
    print("  suggest <N> - Top N players by current form")
    print("  chat <text> - Ask general questions (OpenAI fallback)")
    print("  help - Show this help text")
    print("  quit / exit - Close the bot\n")