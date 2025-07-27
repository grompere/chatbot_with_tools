# Chatbot with Tools

A conversational AI assistant built with LangChain and LangGraph that can search Google for real-time information. The chatbot maintains conversation memory and provides clean, summarized responses.

## Features

- 🤖 **Conversational Memory**: Remembers the entire conversation history
- 🔍 **Google Search Integration**: Can search for current information using Google Custom Search API
- 📝 **Smart Summarization**: Automatically summarizes search results to remove redundancy and verbosity
- 📊 **LangSmith Tracing**: Built-in observability and debugging with LangSmith
- 🔒 **Secure API Key Management**: Uses `.env` files for secure credential storage
- ⚡ **Interactive Mode**: Run as an interactive chatbot or single-query mode

## Demo

Watch a short demo of the chatbot in action here: [Chatbot with Tools Demo](https://streamable.com/isye3q)

- 🤖 **Conversational Memory**: Remembers the entire conversation history
- 🔍 **Google Search Integration**: Can search for current information using Google Custom Search API

## Prerequisites

- Python 3.9+
- Google API Key (for Gemini)
- Google Custom Search Engine ID
- LangSmith API Key (optional, for tracing)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/grompere/chatbot_with_tools.git
   cd chatbot_with_tools
   ```

2. **Install dependencies**:
   ```bash
   pip install langchain langchain-google-genai langchain-google-community langgraph python-dotenv
   ```

3. **Set up API credentials**:
   Create a `.env` file in the project root:
   ```bash
   # .env file
   GOOGLE_API_KEY=your_google_api_key_here
   GOOGLE_CSE_ID=your_google_cse_id_here
   LANGCHAIN_API_KEY=your_langsmith_api_key_here
   
   # Optional: Customize these
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=Chatbot with Tools
   ```

## Getting API Keys

### Google API Key
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create a new API key
3. Copy the key to your `.env` file

### Google Custom Search Engine ID
1. Visit [Google Custom Search Engine](https://cse.google.com/)
2. Create a new search engine
3. Configure it to search the entire web
4. Copy the Search Engine ID to your `.env` file

### LangSmith API Key (Optional)
1. Sign up at [LangSmith](https://smith.langchain.com/)
2. Create an API key in your settings
3. Add it to your `.env` file for tracing and debugging

## Usage

### Interactive Mode
Run the chatbot in interactive mode for ongoing conversations:

```bash
python bot.py
```

**Available commands in interactive mode:**
- `quit`, `exit`, or `q` - End the conversation
- `clear` - Clear conversation memory
- `history` - View conversation history

### Single Query Mode
Run a single query from the command line:

```bash
python bot.py "How tall is the Space Needle?"
```

## Architecture

The chatbot is built using LangGraph with the following components:

- **Chatbot Node**: Main conversational agent using Google's Gemini 2.5 Pro
- **Tools Node**: Handles tool execution (Google Search)
- **Google Search Tool**: Searches Google and summarizes results
- **State Management**: Maintains conversation history using LangGraph's state system

### Workflow
1. User sends a message
2. Chatbot decides if tools are needed
3. If search is required, Google Search Tool is called
4. Search results are automatically summarized
5. Chatbot provides a final response using the summarized information

## Project Structure

```
chatbot_with_tools/
├── bot.py              # Main chatbot application
├── .env               # Environment variables (not in git)
├── .gitignore         # Git ignore file
├── LICENSE            # Apache 2.0 license
└── README.md          # This file
```

## Configuration

The chatbot can be customized by modifying parameters in `bot.py`:

- **Model**: Change from `gemini-2.5-pro` to other available models
- **Temperature**: Adjust creativity (0.0 = deterministic, 1.0 = creative)
- **Max Tokens**: Limit response length
- **Project Name**: Customize LangSmith project name

## Development

### Adding New Tools
To add new tools, create a new class inheriting from `BaseTool` and add it to the `tools` list in `create_chatbot_with_memory()`.

### Debugging
LangSmith tracing is enabled by default. View traces at [LangSmith](https://smith.langchain.com/) to debug conversation flows and tool usage.

## Troubleshooting

### Common Issues

1. **Empty search results**: Verify your Google API keys are correct and have the necessary permissions
2. **Import errors**: Ensure all dependencies are installed with the correct Python version
3. **API rate limits**: Google Search API has usage limits; check your quotas

### Error Messages
- `"Error searching Google"`: Check your Google API credentials
- `"No message found in input"`: Usually indicates a state management issue
- Import errors: Run `pip install -r requirements.txt` (if available)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [LangChain](https://langchain.com/) and [LangGraph](https://langchain-ai.github.io/langgraph/)
- Uses Google's Gemini AI for conversation
- Powered by Google Custom Search for real-time information
- Observability provided by [LangSmith](https://smith.langchain.com/) 