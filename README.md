# 🎬 Avatar Studio - Enterprise AI Video Generation Platform

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/node.js-20+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

> Professional-grade AI video generation platform similar to HeyGen. Create stunning videos with AI avatars, voice cloning, and automatic lip-syncing.

## ✨ Features

### 🎯 Core Capabilities
- **AI Avatar Generation** - Create and customize digital avatars
- **Voice Cloning** - Clone voices or use built-in text-to-speech
- **Lip Sync** - Automatic lip-syncing with Wav2Lip
- **Batch Processing** - Generate multiple videos simultaneously
- **Background Removal** - Professional background effects
- **Subtitle Generation** - Automatic subtitle creation

### 🏗️ Architecture
- **FastAPI Backend** - High-performance async Python API
- **React Frontend** - Modern, responsive UI with TypeScript
- **PostgreSQL** - Robust data persistence
- **Redis** - Task queue and caching
- **Celery** - Distributed task processing
- **Docker** - Complete containerization

### 🔒 Security
- JWT authentication
- Password hashing with bcrypt
- Rate limiting
- CORS configuration
- Security headers

### 📊 Monitoring
- Real-time progress tracking
- Job status management
- Performance metrics
- Error handling and recovery

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Or: Python 3.11+, Node.js 20+, PostgreSQL 15+, Redis 7+

### Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/pratikgawad818/avatar-studio.git
cd avatar-studio

# Create environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Check services
docker-compose ps
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8002
- API Documentation: http://localhost:8002/docs

### Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Frontend (new terminal)
cd frontend
npm install
npm run dev

# Celery Worker (new terminal)
cd backend
celery -A celery_app worker --loglevel=info
```

## 📋 Project Structure

```
avatar-studio/
├── backend/                 # FastAPI application
│   ├── config.py           # Configuration management
│   ├── database.py         # SQLAlchemy setup
│   ├── models.py           # ORM models
│   ├── schemas.py          # Pydantic schemas
│   ├── auth.py             # JWT authentication
│   ├── celery_app.py       # Celery configuration
│   ├── main.py             # FastAPI app entry point
│   ├── routers/            # API endpoints
│   │   ├── auth.py
│   │   ├── assets.py
│   │   ├── projects.py
│   │   └── generation.py
│   ├── pipeline/           # Video generation pipeline
│   │   └── orchestrator.py
│   └── requirements.txt
├── frontend/               # React application
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   └── tsconfig.json
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile.backend      # Backend container
├── Dockerfile.frontend     # Frontend container
├── nginx.conf             # Nginx configuration
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
├── DEPLOYMENT.md         # Deployment guide
├── CONTRIBUTING.md       # Contributing guidelines
└── README.md             # This file
```

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### Assets
- `POST /api/assets/avatars/upload` - Upload avatar
- `GET /api/assets/avatars` - List avatars
- `DELETE /api/assets/avatars/{id}` - Delete avatar

### Projects
- `POST /api/projects` - Create project
- `GET /api/projects/{id}` - Get project
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

### Generation
- `POST /api/generation/generate` - Start video generation
- `GET /api/generation/jobs/{id}` - Get job status
- `GET /api/generation/jobs` - List user's jobs
- `POST /api/generation/estimate` - Estimate generation time

## 🛠️ Configuration

### Environment Variables

```bash
# App
DEBUG=False
APP_VERSION=3.0.0

# Server
HOST=0.0.0.0
PORT=8002

# Database
DATABASE_URL=sqlite:///./avatar_studio.db
# Or: postgresql+asyncpg://user:password@localhost/avatar_studio

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-minimum-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# File Storage
AVATARS_DIR=./data/avatars
VOICES_DIR=./data/voices
BACKGROUNDS_DIR=./data/backgrounds
OUTPUTS_DIR=./data/outputs
TEMP_DIR=./data/temp

# AI Models
WHISPER_MODEL=base
F5TTS_MODEL_DIR=./models/F5-TTS
WAV2LIP_CHECKPOINT=./models/Wav2Lip/checkpoints/wav2lip_gan.pth

# Feature Flags
ENABLE_VOICE_CLONING=True
ENABLE_BATCH_PROCESSING=True
ENABLE_BACKGROUND_REMOVAL=True
```

## 📦 Dependencies

### Backend
- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **Celery** - Task queue
- **Redis** - Message broker
- **Torch** - Deep learning
- **OpenAI Whisper** - Speech recognition
- **FFmpeg** - Video processing

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Material-UI** - Component library
- **React Router** - Navigation
- **Axios** - HTTP client
- **Zustand** - State management

## 📚 Documentation

- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [Contributing Guide](CONTRIBUTING.md) - Contributing guidelines
- [API Documentation](http://localhost:8002/docs) - Interactive API docs (Swagger UI)
- [API Schema](http://localhost:8002/openapi.json) - OpenAPI schema

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=.

# Frontend tests
cd frontend
npm test

# Linting
cd backend
black . && flake8 . && mypy .

cd ../frontend
npm run lint
npm run type-check
```

## 🚢 Deployment

### Docker Compose

```bash
docker-compose up -d
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

### Cloud Platforms
- AWS (ECS/EKS)
- Google Cloud (Cloud Run/GKE)
- Azure (Container Instances/AKS)
- Heroku
- DigitalOcean App Platform

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## 📈 Performance

- **API Response Time**: <100ms average
- **Video Generation**: 2-5 minutes depending on duration
- **Concurrent Jobs**: Scales horizontally with Celery workers
- **Database**: Optimized queries with indexing
- **Frontend**: Code splitting, lazy loading, CDN ready

## 🔒 Security

- ✅ JWT token authentication
- ✅ Password hashing with bcrypt
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ CORS configuration
- ✅ Security headers (X-Frame-Options, CSP, etc.)
- ✅ Rate limiting ready
- ✅ HTTPS/TLS support
- ✅ Environment variable secrets

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

### Code Standards
- Python: PEP 8, type hints, black formatting
- TypeScript: ESLint, Prettier, strict mode
- Git: Conventional commits

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [HeyGen](https://www.heygen.com/) - Inspiration
- [Wav2Lip](https://github.com/justinjohn0306/Wav2Lip) - Lip sync
- [F5-TTS](https://github.com/SWivid/F5-TTS) - Voice synthesis
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition

## 📞 Support

- 🐛 [Report Issues](https://github.com/pratikgawad818/avatar-studio/issues)
- 💬 [Discussions](https://github.com/pratikgawad818/avatar-studio/discussions)
- 📧 Email: pratikgawad818@gmail.com

## 🗺️ Roadmap

- [ ] Live avatar interactions
- [ ] Multi-language support
- [ ] Advanced emotion control
- [ ] Custom avatar training
- [ ] Webhook integrations
- [ ] API rate limiting
- [ ] Advanced analytics
- [ ] Team collaboration features

---

**Made with ❤️ by Pratik Gawad**

⭐ If you find this project useful, please consider giving it a star!
