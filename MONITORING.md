# CodeCompanion Monitoring & Maintenance Guide

## Production Monitoring Overview

This guide provides comprehensive monitoring, logging, and maintenance procedures for CodeCompanion in production environments.

## Health Monitoring

### Primary Health Check Endpoint

**GET /health**

Monitor system health with structured status information:

```bash
# Basic health check
curl -s http://localhost:8000/health | jq '.'

# Expected response
{
  "ok": true,
  "event_bus": "redis",
  "redis_ok": true,
  "db_ok": true,
  "version": "0.1.0",
  "uptime_seconds": 3600
}
```

### Health Check Automation
```bash
#!/bin/bash
# health-check.sh
ENDPOINT="http://localhost:8000/health"
RESPONSE=$(curl -s -w "%{http_code}" "$ENDPOINT")
HTTP_CODE="${RESPONSE: -3}"
BODY="${RESPONSE%???}"

if [[ "$HTTP_CODE" == "200" ]]; then
    echo "✅ Health check passed"
    echo "$BODY" | jq '.'
    exit 0
else
    echo "❌ Health check failed (HTTP $HTTP_CODE)"
    echo "$BODY"
    exit 1
fi
```

### Monitoring Targets

**System Health Indicators:**
- HTTP response codes (200 = healthy, 503 = degraded, 500 = error)
- Event bus connectivity (Redis or fallback to mock)
- Database connectivity (SQLite/PostgreSQL)
- Memory usage and performance metrics
- API key validation status

## Application Monitoring

### Key Metrics to Track

**Performance Metrics:**
```bash
# Response time monitoring
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8000/health

# Memory usage
ps aux | grep codecompanion | awk '{print $4"%  "$11}'

# Connection counts
netstat -an | grep :8000 | wc -l
```

**Business Metrics:**
- Agent execution success rates
- API call volumes per provider (Claude/GPT-4/Gemini)
- Project detection accuracy rates
- Installation success rates
- Error rates by component

### Prometheus Integration

**Metrics Configuration:**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'codecompanion'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
```

**Custom Metrics Export:**
```python
# Add to app.py for metrics endpoint
from prometheus_client import Counter, Histogram, Gauge, generate_latest

REQUEST_COUNT = Counter('codecompanion_requests_total', 'Total requests', ['endpoint', 'method'])
REQUEST_DURATION = Histogram('codecompanion_request_duration_seconds', 'Request duration')
AGENT_EXECUTIONS = Counter('codecompanion_agent_executions_total', 'Agent executions', ['agent_name', 'status'])
ACTIVE_CONNECTIONS = Gauge('codecompanion_active_connections', 'Active WebSocket connections')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Logging Strategy

### Log Levels and Structure
```python
# Structured logging configuration
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'module': record.module,
            'message': record.getMessage(),
            'correlation_id': getattr(record, 'correlation_id', None)
        })

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
    format='%(message)s'
)
```

### Log Categories

**Application Logs:**
- Agent execution start/completion/errors
- API calls and response times
- Authentication and authorization events
- Configuration changes and updates

**Security Logs:**
- Authentication attempts (success/failure)
- API key usage and validation failures
- Rate limiting triggers
- Suspicious request patterns

**Performance Logs:**
- Response times over thresholds
- Memory usage spikes
- Database query performance
- External API latency

### Log Management

**Log Rotation Configuration:**
```bash
# /etc/logrotate.d/codecompanion
/var/log/codecompanion/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 codecompanion codecompanion
    postrotate
        systemctl reload codecompanion
    endscript
}
```

**Log Aggregation with rsyslog:**
```bash
# /etc/rsyslog.d/50-codecompanion.conf
$ModLoad imfile
$InputFilePollInterval 10

$InputFileName /var/log/codecompanion/app.log
$InputFileTag codecompanion:
$InputFileStateFile stat-codecompanion-app
$InputRunFileMonitor

# Forward to centralized logging
*.* @@log-server:514
```

## Alerting Configuration

### Critical Alerts
Set up immediate notifications for:

```yaml
# Alertmanager rules (alerting.yml)
groups:
  - name: codecompanion.critical
    rules:
      - alert: CodeCompanionDown
        expr: up{job="codecompanion"} == 0
        for: 30s
        annotations:
          summary: "CodeCompanion service is down"
          
      - alert: HighErrorRate
        expr: rate(codecompanion_requests_total{code!="200"}[5m]) > 0.1
        for: 2m
        annotations:
          summary: "High error rate detected"
          
      - alert: APIKeyFailures
        expr: rate(codecompanion_api_key_failures[5m]) > 0.05
        for: 1m
        annotations:
          summary: "Multiple API key validation failures"
```

### Warning Alerts
Monitor degraded performance:

```yaml
  - name: codecompanion.warnings
    rules:
      - alert: HighLatency
        expr: codecompanion_request_duration_seconds{quantile="0.95"} > 2.0
        for: 5m
        annotations:
          summary: "High response latency"
          
      - alert: MemoryUsage
        expr: process_resident_memory_bytes / 1024 / 1024 > 500
        for: 10m
        annotations:
          summary: "High memory usage (>500MB)"
```

## Performance Monitoring

### System Resource Monitoring
```bash
#!/bin/bash
# system-monitor.sh

echo "=== CodeCompanion System Monitor ==="
echo "Timestamp: $(date)"
echo ""

# CPU and Memory
echo "--- Resource Usage ---"
ps aux | grep codecompanion | head -n 5

# Disk usage
echo "--- Disk Usage ---"
df -h | grep -E '(^Filesystem|/var/log|/tmp)'

# Network connections
echo "--- Network Connections ---"
netstat -tuln | grep :8000

# Log file sizes
echo "--- Log File Sizes ---"
ls -lh /var/log/codecompanion/ 2>/dev/null || echo "Log directory not found"

echo "=== End Monitor ==="
```

### Database Performance
```sql
-- PostgreSQL monitoring queries
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables 
WHERE tablename LIKE 'codecompanion%';

-- Connection monitoring
SELECT 
    client_addr,
    state,
    COUNT(*) as connections
FROM pg_stat_activity 
WHERE datname = 'codecompanion'
GROUP BY client_addr, state;
```

## Backup and Recovery

### Database Backup Strategy
```bash
#!/bin/bash
# backup-database.sh

BACKUP_DIR="/var/backups/codecompanion"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# SQLite backup
if [[ -f "codecompanion.db" ]]; then
    sqlite3 codecompanion.db ".backup $BACKUP_DIR/codecompanion_$TIMESTAMP.db"
    echo "✅ SQLite backup created: codecompanion_$TIMESTAMP.db"
fi

# PostgreSQL backup
if [[ -n "$DATABASE_URL" ]]; then
    pg_dump "$DATABASE_URL" > "$BACKUP_DIR/codecompanion_$TIMESTAMP.sql"
    echo "✅ PostgreSQL backup created: codecompanion_$TIMESTAMP.sql"
fi

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "codecompanion_*.db" -mtime +30 -delete
find "$BACKUP_DIR" -name "codecompanion_*.sql" -mtime +30 -delete
```

### Configuration Backup
```bash
#!/bin/bash
# backup-config.sh

CONFIG_BACKUP_DIR="/var/backups/codecompanion/config"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$CONFIG_BACKUP_DIR"

# Backup key configuration files
tar -czf "$CONFIG_BACKUP_DIR/config_$TIMESTAMP.tar.gz" \
    .codecompanion.json \
    .cc/ \
    /etc/systemd/system/codecompanion.service \
    /etc/nginx/sites-available/codecompanion 2>/dev/null

echo "✅ Configuration backup created: config_$TIMESTAMP.tar.gz"
```

## Maintenance Procedures

### Regular Maintenance Tasks

**Daily Tasks:**
```bash
#!/bin/bash
# daily-maintenance.sh

echo "Starting daily maintenance for CodeCompanion..."

# Health check
./health-check.sh || exit 1

# Check log file sizes
LOG_SIZE=$(du -sh /var/log/codecompanion/ | cut -f1)
echo "Log directory size: $LOG_SIZE"

# Check available disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [[ $DISK_USAGE -gt 80 ]]; then
    echo "⚠️  Warning: Disk usage is ${DISK_USAGE}%"
fi

# Backup database
./backup-database.sh

echo "Daily maintenance completed successfully"
```

**Weekly Tasks:**
```bash
#!/bin/bash
# weekly-maintenance.sh

echo "Starting weekly maintenance for CodeCompanion..."

# Update dependencies check
pip list --outdated --format=json | jq '.[]'

# Security audit
pip audit --format=json

# Performance report
echo "Performance metrics for the week:"
# Add performance analysis scripts here

# Cleanup old artifacts
find /tmp -name "codecompanion_*" -mtime +7 -delete
find /var/log/codecompanion -name "*.gz" -mtime +30 -delete

echo "Weekly maintenance completed successfully"
```

**Monthly Tasks:**
- Security dependency updates
- Performance baseline review
- Capacity planning assessment
- Backup integrity verification
- SSL certificate expiration check

### Update Procedures

**Safe Update Process:**
```bash
#!/bin/bash
# update-codecompanion.sh

# Pre-update backup
./backup-database.sh
./backup-config.sh

# Health check before update
./health-check.sh || exit 1

# Stop service
sudo systemctl stop codecompanion

# Create checkpoint
git stash push -m "pre-update-$(date +%Y%m%d)"

# Update
pip install --upgrade git+https://github.com/your-repo/codecompanion.git

# Start service
sudo systemctl start codecompanion

# Wait for startup
sleep 10

# Post-update health check
./health-check.sh || {
    echo "Update failed, rolling back..."
    sudo systemctl stop codecompanion
    git stash pop
    pip install --force-reinstall git+https://github.com/your-repo/codecompanion.git
    sudo systemctl start codecompanion
    exit 1
}

echo "✅ Update completed successfully"
```

## Troubleshooting Runbooks

### Service Won't Start
```bash
# Check service status
sudo systemctl status codecompanion

# Check logs
sudo journalctl -u codecompanion -n 50

# Check configuration
codecompanion --check

# Verify dependencies
pip check
```

### High Memory Usage
```bash
# Check memory usage
ps aux | grep codecompanion | awk '{print $4"%  "$11}'

# Check for memory leaks
valgrind --tool=memcheck python -m codecompanion.cli --check

# Restart service if necessary
sudo systemctl restart codecompanion
```

### Database Connection Issues
```bash
# Test database connectivity
python -c "
import sqlite3
try:
    conn = sqlite3.connect('codecompanion.db')
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"
```

## Monitoring Dashboard

### Grafana Dashboard Configuration
```json
{
  "dashboard": {
    "title": "CodeCompanion Production Monitoring",
    "panels": [
      {
        "title": "Health Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job='codecompanion'}",
            "legend": "Service Status"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(codecompanion_requests_total[5m])",
            "legend": "Requests/sec"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "codecompanion_request_duration_seconds",
            "legend": "Response Time"
          }
        ]
      }
    ]
  }
}
```

This monitoring guide provides comprehensive operational procedures for maintaining CodeCompanion in production environments. Regular monitoring, proper alerting, and systematic maintenance ensure reliable service delivery.