# Azure AI Chat Application

This Python application provides a chat interface powered by Azure OpenAI, with ChromaDB integration for context-aware responses and SQL Server for conversation logging.

## Features

- Interactive chat interface with Azure OpenAI
- Context-aware responses using ChromaDB
- Conversation history logging to SQL Server
- Seven-day data retention policy
- Docker support for local development

## Prerequisites

- Python 3.8+
- Docker Desktop
- Azure OpenAI API access
- SQL Server Management Studio (recommended for database management)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd [repository-name]
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a .env file with your configuration:
```env
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_KEY=your_key
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
CHROMA_SERVICE_HOST=http://localhost
CHROMA_SERVICE_PORT=8000
```

## Usage

1. Start the Docker containers:
```bash
docker-compose up -d
```

2. Run the application:
```bash
python azure_ai_chat.py
```

## Project Structure

- `azure_ai_chat.py` - Main application file
- `chroma_client.py` - ChromaDB integration
- `models.py` - Database models
- `db_manager.py` - Database operations
- `docker-compose.yml` - Docker configuration
- `requirements.txt` - Python dependencies

## Database Schema

The chat history is stored in SQL Server with the following schema:

- `id` - Primary key
- `application_name` - Name of the application
- `chat_role` - Role (system, user, or assistant)
- `sequence` - Message sequence number
- `timestamp` - Message timestamp
- `message_content` - Content of the message

## Data Retention

Chat history is automatically purged after seven days to maintain system performance and manage storage.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
