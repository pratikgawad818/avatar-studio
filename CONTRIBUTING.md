# Contributing to Avatar Studio

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- FFmpeg
- PostgreSQL 15+
- Redis 7+

### Setup Development Environment

```bash
# Clone repo
git clone https://github.com/pratikgawad818/avatar-studio.git
cd avatar-studio

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Root setup
cd ..
cp .env.example .env
```

### Running Locally

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python main.py

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Celery (optional)
cd backend
celery -A celery_app worker --loglevel=info
```

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Run `black` for formatting
- Run `flake8` for linting

```bash
black backend/
flake8 backend/
```

### TypeScript/React
- Follow ESLint config
- Use functional components
- Use React hooks
- Use TypeScript for type safety

```bash
cd frontend
npm run lint
npm run type-check
```

## Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=.
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Commit Messages

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code style
- `refactor:` Refactoring
- `test:` Tests
- `chore:` Maintenance

## Pull Request Process

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'feat: Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request
6. Ensure all CI checks pass

## Project Structure

```
avatar-studio/
├── backend/
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── celery_app.py
│   ├── main.py
│   ├── routers/
│   ├── pipeline/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── pages/
│   │   └── index.css
│   ├── index.html
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryproject.io/)

## Questions?

Open an issue or start a discussion!
