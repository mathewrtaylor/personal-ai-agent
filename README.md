# Personal AI Agent

A portable, learning AI agent that runs on your own infrastructure with secure remote access via Tailscale.

## Features

- **Privacy-First**: Runs entirely on your hardware
- **Learning**: Adapts to your communication style and remembers personal context
- **Persistent Memory**: Maintains conversation history and extracted knowledge
- **Secure Access**: Connect from anywhere via Tailscale
- **Self-Hosted**: Use local models via Ollama or connect to external APIs

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│                 │    │                  │    │                 │
│  React Frontend │◄───┤  Python Backend  │◄───┤  Ollama/Models  │
│                 │    │   (FastAPI)      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │              │
                       │  PostgreSQL  │
                       │   Database   │
                       └──────────────┘
```

## Configuration

### Environment Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd personal-ai-agent
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Configure your settings in `.env`:
```env
# Database
POSTGRES_DB=aiagent
POSTGRES_USER=aiagent
POSTGRES_PASSWORD=your_secure_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your_secret_key_here

# AI Model Configuration
MODEL_PROVIDER=ollama  # or openai, anthropic
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama3.2:latest

# Optional: External AI APIs
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Learning Configuration
ENABLE_LEARNING=true
MAX_CONVERSATION_HISTORY=1000
LEARNING_UPDATE_INTERVAL=10  # messages
```

### Docker Compose Adjustments

For common configuration adjustments (timezone, ports, GPU support, etc.), see the [Docker Compose Configuration Guide](DOCKER_COMPOSE_CONFIG.md).

4. Start the services:
```bash
docker-compose up -d
```

5. Access the application:
- Web UI: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
personal-ai-agent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat.py
│   │   │   ├── learning.py
│   │   │   └── health.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── conversation.py
│   │   │   ├── user_profile.py
│   │   │   └── learning_data.py
│   │   ├── services/
│   │   │   ├── ai_service.py
│   │   │   ├── learning_service.py
│   │   │   └── memory_service.py
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/
│   │   │   ├── Settings/
│   │   │   └── Profile/
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── hooks/
│   │   ├── utils/
│   │   └── App.jsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Configuration

### Model Providers

**Ollama (Recommended for Privacy)**:
```env
MODEL_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:latest
```

**OpenAI**:
```env
MODEL_PROVIDER=openai
OPENAI_MODEL=gpt-4
```

**Anthropic**:
```env
MODEL_PROVIDER=anthropic
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

### Tailscale Setup (Optional)

1. Install Tailscale on your server
2. Expose your services through Tailscale:
```bash
# Add to docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

3. Configure nginx to proxy to your services
4. Access via your Tailscale hostname anywhere

## Learning Features

The agent learns from your interactions through:

- **Communication Style Analysis**: Adapts to your preferred tone, formality, and response length
- **Context Memory**: Remembers personal details, preferences, and ongoing topics
- **Conversation Patterns**: Learns from your conversation flow and topic transitions
- **Knowledge Base**: Builds a personal knowledge graph from your interactions

### Learning Data

All learning is stored locally:
- Conversation history
- Extracted personal facts
- Communication style preferences
- Topic interests and expertise areas

## API Endpoints

### Chat
- `POST /api/chat/message` - Send a message to the agent
- `GET /api/chat/history` - Retrieve conversation history
- `DELETE /api/chat/clear` - Clear conversation history

### Learning
- `GET /api/learning/profile` - Get learned user profile
- `POST /api/learning/feedback` - Provide feedback on responses
- `GET /api/learning/stats` - View learning statistics

### Health
- `GET /api/health` - Service health check
- `GET /api/health/models` - Available AI models status

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Security Considerations

- All data stays on your infrastructure
- Use strong passwords in `.env`
- Enable Tailscale for secure remote access
- Regular backups of conversation data
- Consider encryption at rest for sensitive data

## Roadmap

- [ ] ESP32 hardware client
- [ ] Voice interface
- [ ] Mobile app
- [ ] Advanced learning algorithms
- [ ] Multi-user support
- [ ] Plugin system
- [ ] Fine-tuning capabilities

## Credits

### Development

This Personal AI Agent was developed collaboratively with **Claude (Anthropic)** during an extensive development session. The architecture, implementation, and troubleshooting were the result of iterative problem-solving and code generation.

**Key Contributions:**
- Complete full-stack architecture design (Python FastAPI + React + PostgreSQL + Ollama)
- Advanced learning algorithms for communication style adaptation
- Comprehensive error handling and debugging solutions
- Docker containerization and deployment configuration
- Production-ready security and monitoring implementations

### Technical Stack

**Backend:**
- FastAPI (Python) - High-performance API framework
- SQLAlchemy - Database ORM with PostgreSQL
- Pydantic - Data validation and serialization
- Ollama - Local AI model hosting and management

**Frontend:**
- React 18 - Modern web interface with hooks and components
- Axios - HTTP client for API communication
- Custom CSS - Responsive design with animations and accessibility features

**Infrastructure:**
- Docker & Docker Compose - Containerized deployment
- PostgreSQL - Persistent data storage
- Nginx - Production-ready reverse proxy (optional)
- Tailscale - Secure remote access integration ready

**AI & Learning:**
- Ollama (Local LLaMA models) - Privacy-focused AI inference
- OpenAI API support - Cloud AI option
- Anthropic API support - Cloud AI alternative
- Custom learning algorithms - Communication style adaptation and memory consolidation

### Special Recognition

Thanks to **Mathew** (@mathew) for:
- Thorough testing and debugging feedback
- Identifying critical issues (CORS, SQLAlchemy metadata conflicts, dependency injection problems)
- Patience during the iterative development process
- Valuable suggestions for improving the setup experience

### Open Source Libraries

This project builds upon the excellent work of many open-source contributors:
- **FastAPI** - Sebastian Ramirez and contributors
- **React** - Meta and the React team
- **SQLAlchemy** - Mike Bayer and contributors
- **Ollama** - Ollama team for local AI model hosting
- **PostgreSQL** - PostgreSQL Global Development Group

### Future Development

The architecture is designed to be extensible and welcomes contributions. Planned features include ESP32 hardware integration, advanced learning algorithms, and multi-user support.

---

*Built with privacy, learning, and portability in mind. Your conversations stay on your infrastructure.*