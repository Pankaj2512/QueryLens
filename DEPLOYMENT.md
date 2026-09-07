# QueryLens Production Deployment Guide

## Overview

QueryLens is a full-stack application with a Next.js frontend and FastAPI backend. This guide covers production deployment strategies.

## Prerequisites

- Docker and Docker Compose (for containerized deployment)
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)
- Database: SQLite (can be replaced with PostgreSQL for production)

## Deployment Options

### Option 1: Docker Deployment (Recommended)

#### Build Docker Image

```bash
docker build -t querylens:latest .
```

#### Run with Docker

```bash
docker run -d \
  --name querylens \
  -p 8000:8000 \
  -p 3000:3000 \
  -v querylens-data:/app/data \
  -e NODE_ENV=production \
  -e LOG_LEVEL=info \
  querylens:latest
```

#### Docker Compose Deployment

```bash
docker-compose up -d
```

### Option 2: Vercel Deployment

#### Frontend Deployment

1. Push code to GitHub
2. Connect repository to Vercel
3. Set environment variables:
   - `NEXT_PUBLIC_API_URL`: Production API URL

#### Backend Deployment

Deploy backend separately to a service like:
- Railway
- Render
- AWS EC2/ECS
- Digital Ocean App Platform

### Option 3: Manual Server Deployment

#### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=sqlite:///./data/querylens.db
export LOG_LEVEL=info

# Run with Gunicorn
gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 backend.main:app
```

#### Frontend Setup

```bash
# Install dependencies
pnpm install

# Build
pnpm build

# Start production server
pnpm start
```

## Environment Variables

### Backend

```env
# Database
DATABASE_URL=sqlite:///./data/querylens.db

# API Configuration
FRONTEND_URL=https://yourdomain.com

# Logging
LOG_LEVEL=info

# LLM
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash
ALLOW_CLIENT_LLM_CONFIG=false
```

### Frontend

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

## Production Checklist

### Security

- [ ] Enable HTTPS/SSL
- [ ] Set secure CORS origins
- [ ] Enable rate limiting (already configured)
- [ ] Add security headers (already configured)
- [ ] Validate all inputs (already implemented)
- [ ] Use environment variables for secrets
- [ ] Enable CSRF protection if needed

### Performance

- [ ] Use production-grade database (PostgreSQL recommended)
- [ ] Enable database connection pooling
- [ ] Configure caching headers
- [ ] Use CDN for static assets
- [ ] Monitor API response times
- [ ] Enable gzip compression

### Monitoring

- [ ] Set up health check monitoring
- [ ] Enable application logging
- [ ] Configure error tracking (Sentry recommended)
- [ ] Monitor database performance
- [ ] Set up alerting for critical errors

### Maintenance

- [ ] Implement automated backups
- [ ] Plan database migration strategy
- [ ] Document rollback procedures
- [ ] Set up CI/CD pipeline
- [ ] Regular security updates

## Health Checks

The application provides several health check endpoints:

```bash
# Basic health check
curl http://localhost:8000/health

# Full health check
curl http://localhost:8000/health/full

# Readiness check
curl http://localhost:8000/health/ready

# Database statistics
curl http://localhost:8000/stats
```

## Scaling Considerations

### Horizontal Scaling

- Deploy multiple backend instances behind a load balancer
- Use a centralized database (PostgreSQL)
- Configure session persistence if needed

### Database Scaling

- For high volume, migrate from SQLite to PostgreSQL
- Implement read replicas for read-heavy workloads
- Use connection pooling (PgBouncer)

### Caching

- Implement Redis for query result caching
- Cache schema information
- Cache LLM responses for common queries

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Database Connection Issues

```bash
# Check database file exists
ls -la data/querylens.db

# Verify permissions
chmod 755 data/
chmod 644 data/querylens.db
```

### Rate Limiting Issues

- Check Redis connectivity (if using Redis backend)
- Verify rate limit configuration
- Check client IP headers in reverse proxy setup

## Backup and Recovery

### Backup Database

```bash
# SQLite backup
cp data/querylens.db data/querylens.db.backup

# Automated backup (cron job)
0 2 * * * cp /app/data/querylens.db /backups/querylens.db.$(date +\%Y\%m\%d)
```

### Recovery

```bash
# Restore from backup
cp data/querylens.db.backup data/querylens.db
```

## Support

For issues or questions:
- Check health check endpoints
- Review application logs
- Check database connectivity
- Verify environment variables
- Review API documentation in API.md
