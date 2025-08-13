# CodeCompanion Docker Deployment Guide

## Docker Overview

This guide provides comprehensive Docker containerization for CodeCompanion, including multi-stage builds, production configurations, and orchestration examples.

## Quick Start

### Pull and Run Pre-built Image

```bash
# Pull latest image
docker pull codecompanion/codecompanion:latest

# Run with basic configuration
docker run -d \
  --name codecompanion \
  -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your-claude-key \
  -e OPENAI_API_KEY=your-gpt4-key \
  codecompanion/codecompanion:latest
```

### Build from Source

```bash
# Clone repository
git clone https://github.com/your-repo/codecompanion.git
cd codecompanion

# Build image
docker build -t codecompanion:local .

# Run locally built image
docker run -d \
  --name codecompanion-local \
  -p 8000:8000 \
  --env-file .env \
  codecompanion:local
```

## Dockerfile

### Production Multi-Stage Dockerfile

```dockerfile
# syntax=docker/dockerfile:1.4

# ===============================
# Build Stage
# ===============================
FROM python:3.11-slim-bullseye AS builder

# Set build arguments
ARG VERSION=main
ARG BUILD_DATE
ARG VCS_REF

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r codecompanion && useradd -r -g codecompanion codecompanion

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Install CodeCompanion
RUN pip install --no-cache-dir -e .

# ===============================
# Runtime Stage
# ===============================
FROM python:3.11-slim-bullseye AS runtime

# Set metadata labels
LABEL org.opencontainers.image.title="CodeCompanion"
LABEL org.opencontainers.image.description="Universal AI Agent System for Development"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.source="https://github.com/your-repo/codecompanion"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user and directories
RUN groupadd -r codecompanion && useradd -r -g codecompanion codecompanion
RUN mkdir -p /app /var/log/codecompanion /var/lib/codecompanion \
    && chown -R codecompanion:codecompanion /app /var/log/codecompanion /var/lib/codecompanion

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/codecompanion /usr/local/bin/codecompanion

# Copy application code
COPY --from=builder --chown=codecompanion:codecompanion /app /app

# Set work directory and user
WORKDIR /app
USER codecompanion

# Create volume for persistent data
VOLUME ["/var/lib/codecompanion", "/var/log/codecompanion"]

# Environment variables
ENV PYTHONPATH=/app
ENV CODECOMPANION_DATA_DIR=/var/lib/codecompanion
ENV CODECOMPANION_LOG_DIR=/var/log/codecompanion

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Development Dockerfile

```dockerfile
# Development image with hot reloading
FROM python:3.11-slim-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir watchdog

# Copy source code
COPY . .

# Install in development mode
RUN pip install -e .

# Development command with hot reload
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

## Environment Configuration

### Environment Variables

Create `.env` file for local development:

```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-your-claude-key
OPENAI_API_KEY=sk-your-gpt4-key
GEMINI_API_KEY=AIza-your-gemini-key

# Application Settings
CC_LOG_LEVEL=INFO
CC_MAX_CONCURRENT_AGENTS=3
CC_CACHE_ENABLED=true

# Database Configuration
DATABASE_URL=sqlite:////var/lib/codecompanion/codecompanion.db

# Event Bus Configuration
EVENT_BUS=redis
REDIS_URL=redis://redis:6379/0

# Security
CC_TOKEN=your-secure-api-token
CC_CORS_ORIGINS=https://yourdomain.com,http://localhost:3000

# Performance
CC_WORKERS=4
CC_MAX_REQUEST_SIZE=10MB
```

### Production Environment Variables

```bash
# Production-specific settings
NODE_ENV=production
CC_LOG_LEVEL=INFO
CC_DEBUG=false

# High availability settings
CC_WORKERS=8
CC_MAX_CONCURRENT_AGENTS=5
CC_REQUEST_TIMEOUT=300

# Monitoring
CC_METRICS_ENABLED=true
CC_HEALTH_CHECK_INTERVAL=30

# Security
CC_RATE_LIMIT_ENABLED=true
CC_MAX_REQUESTS_PER_MINUTE=60
```

## Docker Compose

### Development Setup

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  codecompanion:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - codecompanion_data:/var/lib/codecompanion
    environment:
      - CC_LOG_LEVEL=DEBUG
      - EVENT_BUS=redis
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      - redis
      - postgres
    networks:
      - codecompanion-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - codecompanion-network

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: codecompanion
      POSTGRES_USER: codecompanion
      POSTGRES_PASSWORD: development_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - codecompanion-network

volumes:
  codecompanion_data:
  redis_data:
  postgres_data:

networks:
  codecompanion-network:
    driver: bridge
```

### Production Setup

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  codecompanion:
    image: codecompanion/codecompanion:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - codecompanion_data:/var/lib/codecompanion
      - codecompanion_logs:/var/log/codecompanion
    environment:
      - NODE_ENV=production
      - CC_LOG_LEVEL=INFO
      - EVENT_BUS=redis
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://codecompanion:${POSTGRES_PASSWORD}@postgres:5432/codecompanion
    env_file:
      - .env.production
    depends_on:
      - redis
      - postgres
    networks:
      - codecompanion-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
      - ./redis.conf:/etc/redis/redis.conf
    command: redis-server /etc/redis/redis.conf
    networks:
      - codecompanion-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 5s
      retries: 3

  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: codecompanion
      POSTGRES_USER: codecompanion
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - codecompanion-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U codecompanion"]
      interval: 30s
      timeout: 5s
      retries: 3

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/private
      - nginx_logs:/var/log/nginx
    depends_on:
      - codecompanion
    networks:
      - codecompanion-network

volumes:
  codecompanion_data:
  codecompanion_logs:
  redis_data:
  postgres_data:
  nginx_logs:

networks:
  codecompanion-network:
    driver: bridge
```

## Production Optimization

### Multi-Stage Build Optimization

```dockerfile
# Optimized production build
FROM python:3.11-slim-bullseye AS base

# Install system dependencies once
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Python dependencies stage
FROM base AS python-deps
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final runtime stage
FROM base AS runtime
COPY --from=python-deps /root/.local /root/.local
COPY . /app
WORKDIR /app
RUN pip install --no-cache-dir -e .

# Security hardening
RUN groupadd -r codecompanion && useradd -r -g codecompanion codecompanion
USER codecompanion

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Security Hardening

```dockerfile
# Security-hardened Dockerfile
FROM python:3.11-slim-bullseye

# Create non-root user early
RUN groupadd -r -g 1000 codecompanion && \
    useradd -r -u 1000 -g codecompanion codecompanion

# Install security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set security-focused file permissions
WORKDIR /app
COPY --chown=codecompanion:codecompanion . .

# Install Python packages as non-root
USER codecompanion
RUN pip install --user --no-cache-dir -e .

# Security labels
LABEL security.non-root=true
LABEL security.capabilities=none
LABEL security.no-new-privileges=true

# Run with security options
USER codecompanion
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Container Orchestration

### Kubernetes Deployment

```yaml
# kubernetes/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: codecompanion

---
# kubernetes/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: codecompanion-config
  namespace: codecompanion
data:
  CC_LOG_LEVEL: "INFO"
  EVENT_BUS: "redis"
  REDIS_URL: "redis://redis-service:6379/0"
  CC_WORKERS: "4"

---
# kubernetes/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: codecompanion-secrets
  namespace: codecompanion
type: Opaque
data:
  anthropic-api-key: <base64-encoded-key>
  openai-api-key: <base64-encoded-key>
  gemini-api-key: <base64-encoded-key>

---
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: codecompanion
  namespace: codecompanion
spec:
  replicas: 3
  selector:
    matchLabels:
      app: codecompanion
  template:
    metadata:
      labels:
        app: codecompanion
    spec:
      containers:
      - name: codecompanion
        image: codecompanion/codecompanion:latest
        ports:
        - containerPort: 8000
        env:
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: codecompanion-secrets
              key: anthropic-api-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: codecompanion-secrets
              key: openai-api-key
        envFrom:
        - configMapRef:
            name: codecompanion-config
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

---
# kubernetes/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: codecompanion-service
  namespace: codecompanion
spec:
  selector:
    app: codecompanion
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Docker Swarm

```yaml
# docker-swarm.yml
version: '3.8'

services:
  codecompanion:
    image: codecompanion/codecompanion:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    ports:
      - "8000:8000"
    environment:
      - NODE_ENV=production
      - EVENT_BUS=redis
    secrets:
      - anthropic_api_key
      - openai_api_key
    networks:
      - codecompanion-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == manager
    volumes:
      - redis_data:/data
    networks:
      - codecompanion-network

secrets:
  anthropic_api_key:
    external: true
  openai_api_key:
    external: true

volumes:
  redis_data:

networks:
  codecompanion-network:
    driver: overlay
```

## Monitoring and Logging

### Logging Configuration

```yaml
# logging/docker-compose.logging.yml
version: '3.8'

services:
  codecompanion:
    # ... existing configuration
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service,version"
    labels:
      - "service=codecompanion"
      - "version=latest"

  fluentd:
    image: fluent/fluentd:v1.14-debian-1
    volumes:
      - ./fluentd:/fluentd/etc
      - codecompanion_logs:/var/log/codecompanion
    ports:
      - "24224:24224"
    environment:
      FLUENTD_CONF: fluent.conf
    networks:
      - codecompanion-network

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - codecompanion-network

volumes:
  elasticsearch_data:
```

### Prometheus Monitoring

```yaml
# monitoring/docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - codecompanion-network

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    ports:
      - "3000:3000"
    networks:
      - codecompanion-network

volumes:
  prometheus_data:
  grafana_data:
```

## Build and Deployment Scripts

### Build Script

```bash
#!/bin/bash
# scripts/build.sh

set -e

VERSION=${1:-latest}
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VCS_REF=$(git rev-parse --short HEAD)

echo "Building CodeCompanion Docker image..."
echo "Version: $VERSION"
echo "Build Date: $BUILD_DATE"
echo "VCS Ref: $VCS_REF"

# Build production image
docker build \
  --build-arg VERSION="$VERSION" \
  --build-arg BUILD_DATE="$BUILD_DATE" \
  --build-arg VCS_REF="$VCS_REF" \
  -t codecompanion/codecompanion:"$VERSION" \
  -t codecompanion/codecompanion:latest \
  .

# Security scan
echo "Running security scan..."
docker scout cves codecompanion/codecompanion:"$VERSION"

echo "✅ Build completed successfully"
```

### Deployment Script

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=${1:-production}
VERSION=${2:-latest}

echo "Deploying CodeCompanion to $ENVIRONMENT..."

case $ENVIRONMENT in
  "development")
    docker-compose -f docker-compose.dev.yml up -d
    ;;
  "production")
    docker-compose -f docker-compose.prod.yml up -d
    ;;
  "kubernetes")
    kubectl apply -f kubernetes/
    kubectl rollout restart deployment/codecompanion -n codecompanion
    ;;
  *)
    echo "Unknown environment: $ENVIRONMENT"
    exit 1
    ;;
esac

echo "✅ Deployment completed successfully"
```

This comprehensive Docker guide provides everything needed for containerized deployment of CodeCompanion in any environment, from development to enterprise production.