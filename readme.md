# LangChain Autonomous Task Processor

## New Feature: Azure OpenAI Chat Page

You can now chat directly with your configured Azure OpenAI instance! After setting up your API credentials in the sidebar, navigate to the new Chat page to interact with your LLM in a conversational interface. This is useful for quick Q&A, brainstorming, or testing your model setup.

---

# Existing Features

A comprehensive Streamlit application that uses LangChain framework to perform autonomous task completion using uploaded context documents.

## Features

- 📁 **File Upload**: Accept only Markdown (`.md`) files as context/knowledge base
- 📝 **Task Input**: Single task or bulk task processing
- 🤖 **Agentic Reasoning**: LangChain agent with memory, tool usage, and multi-step reasoning
- 🔧 **LLM API Selection**: Currently supports Azure OpenAI (with framework for other providers)
- 🚀 **Batch Optimization**: Automatically groups similar tasks for efficient processing
- 📊 **Results Dashboard**: Comprehensive results display with confidence scores and metadata
- 💾 **Export Functionality**: Export results in markdown format

## Architecture

### Core Components

1. **main.py**: Main Streamlit application with UI components
2. **llm_config.py**: LLM configuration and factory pattern for different providers
3. **agent_system.py**: LangChain agent system with tools and memory
4. **utils.py**: Utility functions for file validation, task batching, and text processing

### Key Features

#### Intelligent Agent System

- **Context Retrieval**: Uses FAISS vector store for semantic search
- **Multi-step Reasoning**: Breaks down complex problems into logical steps
- **Memory Management**: Maintains conversation history for context
- **Tool Integration**: Custom tools for analysis and reasoning

#### Batch Processing

- **Similarity Detection**: Groups similar tasks automatically
- **Efficiency Optimization**: Reduces API calls and processing time
- **Parallel Processing**: Handles multiple tasks efficiently

#### Advanced Analytics

- **Confidence Scoring**: Heuristic-based confidence calculation
- **Source Extraction**: Identifies and tracks information sources
- **Reasoning Steps**: Extracts step-by-step reasoning from responses
- **Performance Metrics**: Tracks tokens used and processing time

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd reasonable
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the application:

```bash
streamlit run main.py
```

## Configuration

Configuration is now handled via a `llm_config.json` file in the project root. The old `.env` file is no longer used.

### Example `llm_config.json`
```json
{
  "PROVIDER": "azure_openai",
  "AZURE_OPENAI_API_KEY": "your-api-key",
  "AZURE_OPENAI_ENDPOINT": "https://your-endpoint.openai.azure.com/",
  "AZURE_OPENAI_DEPLOYMENT_NAME": "your-deployment-name",
  "AZURE_OPENAI_API_VERSION": "2025-01-01-preview",
  "TEMPERATURE": "0.7",
  "MAX_TOKENS": "4000"
}
```

You can edit this file manually or use the sidebar in the app to update your configuration.

### Azure OpenAI Setup

1. **API Key**: Your Azure OpenAI API key
2. **Endpoint**: Azure OpenAI endpoint URL (e.g., `https://your-resource.openai.azure.com/`)
3. **Deployment Name**: Name of your GPT model deployment
4. **API Version**: Azure OpenAI API version (default: `2024-02-01`)

### Required Azure Deployments

- **Chat Model**: GPT-4 or GPT-3.5-turbo deployment
- **Embeddings**: `text-embedding-ada-002` deployment (for vector search)

## Usage

### 1. Configure LLM

- Open the sidebar
- Select "Azure OpenAI" as provider
- Enter your API credentials
- Click "Configure LLM"

### 2. Upload Context

- Upload one or more markdown files
- Files serve as knowledge base for answering questions
- Preview uploaded content in the expandable section

### 3. Input Tasks

- Choose between single task or bulk input
- For bulk input, enter one task per line
- Enable batch optimization for similar tasks

### 4. Process and Review

- Click "Process Tasks" to start
- Monitor progress with real-time status updates
- Review detailed results with confidence scores
- Export results if needed

## Advanced Features

### Task Categorization

The system automatically categorizes tasks into:

- **Questions**: What, where, when, why, how queries
- **Analysis**: Analyze, examine, evaluate requests
- **Summary**: Summarize, overview requests
- **Extraction**: Find, identify, list requests
- **Creation**: Generate, create, develop requests

### Complexity Assessment

Tasks are rated as:

- **Simple**: Short, straightforward queries
- **Medium**: Moderate complexity with some analysis
- **Complex**: Multi-part questions requiring detailed reasoning

### Context Optimization

- Automatically extracts relevant context sections
- Prioritizes content based on task keywords
- Maintains context length within model limits

## File Structure

```
langchain-task-processor/
├── main.py                 # Main Streamlit application
├── llm_config.py          # LLM configuration and factory
├── agent_system.py        # LangChain agent implementation
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Future Enhancements

### Planned Features

- **Multi-Provider Support**: OpenAI, Gemini, Anthropic integration
- **Advanced Export**: PDF, Word, JSON export formats
- **Collaboration**: Multi-user support and sharing
- **Templates**: Pre-built task templates
- **Analytics**: Advanced usage analytics and insights

### API Integrations

- **OpenAI**: Direct OpenAI API support
- **Google Gemini**: Gemini Pro integration
- **Anthropic Claude**: Claude API integration
- **Local Models**: Ollama and local model support

## Troubleshooting

### Common Issues

1. **Configuration Errors**

   - Verify API key and endpoint are correct
   - Ensure deployment names match your Azure setup
   - Check API version compatibility

2. **File Upload Issues**

   - Only `.md` files are supported
   - File size limit is 10MB
   - Ensure files are UTF-8 encoded

3. **Processing Errors**
   - Check internet connectivity
   - Verify Azure OpenAI quotas
   - Reduce task complexity if needed

### Performance Tips

1. **Context Optimization**

   - Use focused, relevant markdown files
   - Break large documents into smaller sections
   - Remove unnecessary formatting

2. **Task Design**

   - Be specific in task descriptions
   - Use clear, actionable language
   - Group related tasks together

3. **Batch Processing**
   - Enable batch optimization for similar tasks
   - Process complex tasks individually
   - Monitor token usage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

- Create an issue in the repository
- Check the troubleshooting section
- Review LangChain documentation for advanced configurations
