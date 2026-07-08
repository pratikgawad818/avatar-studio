# Avatar Studio - Enterprise Deployment Guide

## Quick Start (Docker Compose)

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

# Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8002
# API Docs: http://localhost:8002/docs
```

## Production Deployment

### Prerequisites
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+
- FFmpeg

### Database Setup

```bash
# Create PostgreSQL database
psql -U postgres

CREATE DATABASE avatar_studio;
CREATE USER avatar_user WITH PASSWORD 'secure_password';
ALTER ROLE avatar_user SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE avatar_studio TO avatar_user;
```

### Environment Variables

```bash
# .env.production
DEBUG=False
DATABASE_URL=postgresql+asyncpg://avatar_user:password@db.example.com/avatar_studio
REDIS_URL=redis://:password@redis.example.com:6379/0
SECRET_KEY=your-very-long-random-secret-key-minimum-32-chars
```

### Deploy

```bash
docker-compose up -d
```

## Scaling

```bash
# Scale Celery workers
docker-compose up -d --scale celery=3
```

## Monitoring

```bash
# View logs
docker-compose logs -f backend

# Health check
curl http://localhost:8002/health
```

## Troubleshooting

- Backend won't start: `docker-compose logs backend`
- Jobs not processing: `docker-compose logs celery`
- Database issues: `docker-compose logs db`

For more details, see DEPLOYMENT.md
