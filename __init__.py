"""
Fantasy Premier League Assistant Package
A chatbot that provides FPL player stats, comparisons, and OpenAI fallback.
"""

from .fpl_client import FPLClient
from .chatbot import gpt_fallback, print_help
from .main import main

__version__ = "1.0.0"
__all__ = ["FPLClient", "gpt_fallback", "print_help", "main"]