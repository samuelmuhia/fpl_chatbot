"""
Setup file for FPL Assistant package.
"""
from setuptools import setup, find_packages

setup(
    name="fpl-assistant",
    version="1.0.0",
    author="Samuel Muhia",
    description="Fantasy Premier League Assistant Chatbot",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "fpl-assistant=main:main",
        ],
    },
)