# AI Chatbot Project

This is an AI chatbot powered by OpenAI's API.

## Setup

1. Create a `.env` file by copying `.env.example`:
   ```bash
   cp .env.example .env
   ```

2. Add your OpenAI API key to `.env`:
   ```
   OPENAI_API_KEY=your_actual_api_key_here
   ```

3. The dependencies are already installed in the virtual environment.

## Running the Chatbot

```bash
python main.py
```

## Project Structure

- `main.py` - Main chatbot script
- `requirements.txt` - Python dependencies
- `.env.example` - Example environment variables
- `.env` - Your local environment (not committed to git)

## Dependencies

- **openai** - Official OpenAI Python library
- **python-dotenv** - Load environment variables from .env file
- **langchain** - Framework for building LLM applications
- **langchain-openai** - LangChain OpenAI integration
- **flask** - Web framework (for future web interface)
- **requests** - HTTP library
- **pydantic** - Data validation using Python type annotations

## Next Steps

1. Get an OpenAI API key from https://platform.openai.com/api-keys
2. Add it to your `.env` file
3. Run `python main.py` to start chatting!
