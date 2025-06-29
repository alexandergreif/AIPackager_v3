# Deployment Guide

This document provides instructions for deploying AIPackager v3 in various environments.

## 🚀 Quick Deployment

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd AIPackager_v3

# Setup environment
make venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
make install

# Run application
python run.py
```

Access at: http://localhost:5001

### Production Deployment

```bash
# Production setup
export FLASK_ENV=production
export DATABASE_URL=sqlite:///instance/production.db

# Install with production dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "src.app:create_app()"
```

## ☁️ Cloud Deployment

### AWS EC2

#### Prerequisites
- EC2 instance (t3.medium or larger recommended)
- Security group allowing HTTP/HTTPS traffic
- Elastic IP (optional but recommended)

#### Setup Script

```bash
#!/bin/bash
# AWS EC2 deployment script

# Update system
sudo yum update -y

# Install Python 3.12
sudo yum install -y python3.12 python3.12-pip git

# Install msitools (if available)
sudo yum install -y msitools || echo "msitools not available"

# Clone application
git clone <repository-url> /opt/aipackager
cd /opt/aipackager

# Setup virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/aipackager.service > /dev/null <<EOF
[Unit]
Description=AIPackager v3
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/opt/aipackager
Environment=PATH=/opt/aipackager/.venv/bin
Environment=FLASK_ENV=production
ExecStart=/opt/aipackager/.venv/bin/python run.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable aipackager
sudo systemctl start aipackager
```

### Azure App Service

#### app.py (Entry Point)

```python
import os
from src.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
```

#### requirements.txt (Azure)

```txt
# Include all dependencies from requirements.txt
# Plus Azure-specific packages if needed
```

#### Deployment Steps

1. Create App Service in Azure Portal
2. Configure deployment from GitHub
3. Set environment variables:
   - `FLASK_ENV=production`
   - `DATABASE_URL=sqlite:///home/site/wwwroot/instance/production.db`
4. Deploy from repository

### Google Cloud Run

#### Dockerfile (Cloud Run)

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    msitools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create instance directory
RUN mkdir -p instance/uploads

# Use Cloud Run's PORT environment variable
ENV PORT=8080
EXPOSE 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 "src.app:create_app()"
```

#### Deploy to Cloud Run

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/aipackager

# Deploy to Cloud Run
gcloud run deploy aipackager \
  --image gcr.io/PROJECT_ID/aipackager \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1
```

## 🗄️ Database Configuration

### SQLite (Default)

```python
# Default configuration
DATABASE_URL = "sqlite:///instance/aipackager.db"
```

**Pros**: Simple, no additional setup
**Cons**: Not suitable for high-traffic production

### PostgreSQL

```bash
# Install PostgreSQL adapter
pip install psycopg2-binary

# Set database URL
export DATABASE_URL="postgresql://user:password@localhost/aipackager"
```

#### Database Setup

```sql
-- Create database
CREATE DATABASE aipackager;

-- Create user
CREATE USER aipackager_user WITH PASSWORD 'secure_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE aipackager TO aipackager_user;
```

### MySQL

```bash
# Install MySQL adapter
pip install PyMySQL

# Set database URL
export DATABASE_URL="mysql+pymysql://user:password@localhost/aipackager"
```

## 🔧 Environment Configuration

### Environment Variables

```bash
# Application settings
export FLASK_ENV=production
export SECRET_KEY=your-secret-key-here

# Database
export DATABASE_URL=sqlite:///instance/production.db

# File uploads
export UPLOAD_FOLDER=instance/uploads
export MAX_CONTENT_LENGTH=209715200  # 200MB

# Logging
export LOG_LEVEL=INFO
export LOG_FILE=instance/logs/aipackager.log

# AI Integration (future)
export OPENAI_API_KEY=your-api-key
export AI_MODEL=gpt-4o
```

### Configuration File

```python
# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///instance/aipackager.db'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'instance/uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 209715200))

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class TestingConfig(Config):
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'
```

## 🔒 Security Considerations

### HTTPS Configuration

#### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # File upload size limit
    client_max_body_size 200M;
}
```

### Security Headers

```python
# In Flask app
from flask import Flask
from flask_talisman import Talisman

app = Flask(__name__)

# Add security headers
Talisman(app, {
    'force_https': True,
    'strict_transport_security': True,
    'content_security_policy': {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'",
    }
})
```

### File Upload Security

```python
# Secure file handling
ALLOWED_EXTENSIONS = {'.msi', '.exe'}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

def secure_filename_validation(filename):
    if not filename:
        return False

    # Check extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False

    # Additional security checks
    if '..' in filename or '/' in filename:
        return False

    return True
```

## 📊 Monitoring & Logging

### Application Logging

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
if not app.debug:
    file_handler = RotatingFileHandler(
        'instance/logs/aipackager.log',
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### Health Check Endpoint

The application includes a `/health` endpoint to verify its operational status.

```python
@app.route('/health')
def health_check():
    """Health check endpoint for load balancers."""
    try:
        # Check database connectivity
        db_service = get_database_service()
        session = db_service.get_session()
        session.execute('SELECT 1')
        session.close()

        return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 500
```

### Monitoring with Prometheus

```python
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Custom metrics
upload_counter = metrics.counter(
    'aipackager_uploads_total',
    'Total number of file uploads'
)

processing_time = metrics.histogram(
    'aipackager_processing_seconds',
    'Time spent processing packages'
)
```

## 🔄 Backup & Recovery

### Database Backup

```bash
#!/bin/bash
# backup.sh - Database backup script

BACKUP_DIR="/opt/backups/aipackager"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup SQLite database
cp instance/aipackager.db $BACKUP_DIR/aipackager_$DATE.db

# Backup uploaded files
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz instance/uploads/

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### Automated Backup (Cron)

```bash
# Add to crontab
0 2 * * * /opt/aipackager/backup.sh
```

## 🚦 Performance Optimization

### Gunicorn Configuration

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

### Caching

```python
from flask_caching import Cache

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/api/packages')
@cache.cached(timeout=300)  # 5 minutes
def list_packages():
    return get_all_packages()
```

## 🔧 Troubleshooting

### Common Issues

#### msitools Not Available
```bash
# Ubuntu/Debian
sudo apt-get install msitools

# CentOS/RHEL
sudo yum install msitools

# macOS
brew install msitools
```

#### Permission Issues
```bash
# Fix file permissions
sudo chown -R app:app /opt/aipackager
sudo chmod -R 755 /opt/aipackager
sudo chmod -R 777 /opt/aipackager/instance
```

#### Database Migration Issues
```bash
# Create a new migration
alembic revision --autogenerate -m "Your migration message"

# Apply the migration
alembic upgrade head
```

### Log Analysis

```bash
# Monitor application logs
tail -f instance/logs/aipackager.log

# Check for errors
grep ERROR instance/logs/aipackager.log

# Monitor system resources
htop
df -h
