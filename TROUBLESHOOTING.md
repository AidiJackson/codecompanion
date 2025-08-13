# CodeCompanion Troubleshooting Guide

## Quick Diagnostic Commands

Before diving into specific issues, run these diagnostic commands to gather system information:

```bash
# System health check
codecompanion --check

# Verify installation
python -c "import codecompanion; print('✅ CodeCompanion installed successfully')"

# Check API connectivity
curl -s http://localhost:8000/health | jq '.'

# View recent logs
journalctl -u codecompanion -n 50 --no-pager
```

## Installation Issues

### Installation Fails with Permission Errors

**Symptoms:**
- `Permission denied` errors during installation
- `sudo: command not found` on some systems

**Solutions:**
```bash
# Method 1: User-level installation
pip install --user git+https://github.com/your-repo/codecompanion.git

# Method 2: Virtual environment
python -m venv codecompanion-env
source codecompanion-env/bin/activate
pip install git+https://github.com/your-repo/codecompanion.git

# Method 3: System-level with proper sudo
sudo -H pip install git+https://github.com/your-repo/codecompanion.git
```

### "Command not found: codecompanion"

**Symptoms:**
- Installation appears successful but command not available

**Solutions:**
```bash
# Check if installed in user directory
export PATH="$HOME/.local/bin:$PATH"
codecompanion --check

# For virtual environment installations
source codecompanion-env/bin/activate
codecompanion --check

# Verify installation location
pip show codecompanion
which codecompanion
```

### Dependency Conflicts

**Symptoms:**
- Version conflicts during installation
- `ModuleNotFoundError` after installation

**Diagnostic:**
```bash
# Check for conflicts
pip check

# Show dependency tree
pip-tree codecompanion
```

**Solutions:**
```bash
# Clean installation
pip uninstall codecompanion
pip cache purge
pip install git+https://github.com/your-repo/codecompanion.git

# Use constraints file
pip install -c constraints.txt git+https://github.com/your-repo/codecompanion.git
```

## API Key Issues

### "API Key not found" Errors

**Symptoms:**
- Agents fail with authentication errors
- `ANTHROPIC_API_KEY not set` warnings

**Diagnostic:**
```bash
# Check environment variables
env | grep -E "(ANTHROPIC|OPENAI|GEMINI)_API_KEY"

# Verify key format
echo $ANTHROPIC_API_KEY | grep -E "^sk-ant-"
echo $OPENAI_API_KEY | grep -E "^sk-"
echo $GEMINI_API_KEY | grep -E "^AIza"
```

**Solutions:**

**For Replit:**
```bash
# Set in Replit Secrets tab
ANTHROPIC_API_KEY=sk-ant-your-key
OPENAI_API_KEY=sk-your-key
GEMINI_API_KEY=AIza-your-key
```

**For Local Development:**
```bash
# Create .env file
cat > .env << EOF
ANTHROPIC_API_KEY=sk-ant-your-key
OPENAI_API_KEY=sk-your-key
GEMINI_API_KEY=AIza-your-key
EOF

# Load environment
source .env
```

**For Production:**
```bash
# System environment
sudo systemctl edit codecompanion
# Add:
[Service]
Environment=ANTHROPIC_API_KEY=sk-ant-your-key
Environment=OPENAI_API_KEY=sk-your-key
Environment=GEMINI_API_KEY=AIza-your-key
```

### API Rate Limiting

**Symptoms:**
- `429 Too Many Requests` errors
- Agents timeout or fail intermittently

**Diagnostic:**
```bash
# Check API usage
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/usage

# Monitor rate limits
tail -f /var/log/codecompanion/app.log | grep -i "rate.limit"
```

**Solutions:**
- Reduce concurrent agent executions
- Implement exponential backoff
- Upgrade to higher tier API plans
- Use multiple API keys with load balancing

## Runtime Errors

### "Agent execution failed"

**Symptoms:**
- Agents start but fail to complete
- Generic "execution failed" messages

**Diagnostic:**
```bash
# Run single agent with verbose logging
codecompanion --run Analyzer --verbose

# Check agent logs
ls -la .cc/logs/
cat .cc/logs/analyzer.log

# Test specific agent
python -c "
from agents.analyzer import AnalyzerAgent
agent = AnalyzerAgent()
result = agent.execute({'project_type': 'python'})
print(result)
"
```

**Common Solutions:**
```bash
# Update to latest version
pip install --upgrade git+https://github.com/your-repo/codecompanion.git

# Clear agent cache
rm -rf .cc/cache/
codecompanion --run Analyzer

# Reset agent configuration
rm .codecompanion.json
codecompanion --detect
```

### WebSocket Connection Failures

**Symptoms:**
- Real-time updates not working
- `WebSocket connection failed` errors

**Diagnostic:**
```bash
# Test WebSocket connection
wscat -c ws://localhost:8000/ws

# Check port availability
netstat -tuln | grep :8000

# Test connectivity
curl -I http://localhost:8000/health
```

**Solutions:**
```bash
# Check firewall settings
sudo ufw status
sudo ufw allow 8000

# Restart service
sudo systemctl restart codecompanion

# Check reverse proxy configuration
nginx -t
sudo systemctl reload nginx
```

## Database Issues

### Database Connection Errors

**Symptoms:**
- `Database connection failed` in health check
- SQLite database locked errors

**Diagnostic:**
```bash
# Test database connection
sqlite3 codecompanion.db "SELECT COUNT(*) FROM sqlite_master;"

# Check database file permissions
ls -la codecompanion.db

# Check for file locks
lsof codecompanion.db
```

**Solutions:**
```bash
# Fix permissions
chmod 664 codecompanion.db
chown codecompanion:codecompanion codecompanion.db

# Clear locks
pkill -f codecompanion
rm -f codecompanion.db-wal codecompanion.db-shm

# Restart service
sudo systemctl restart codecompanion
```

### Database Corruption

**Symptoms:**
- `database disk image is malformed` errors
- Inconsistent data retrieval

**Recovery:**
```bash
# Backup current database
cp codecompanion.db codecompanion.db.backup

# Check integrity
sqlite3 codecompanion.db "PRAGMA integrity_check;"

# Attempt repair
sqlite3 codecompanion.db "VACUUM;"

# If severely corrupted, rebuild from backup
sqlite3 codecompanion.db.backup ".dump" | sqlite3 codecompanion_new.db
mv codecompanion_new.db codecompanion.db
```

## Performance Issues

### High Memory Usage

**Symptoms:**
- System slowdown
- Out of memory errors
- Process killed by system

**Diagnostic:**
```bash
# Monitor memory usage
top -p $(pgrep -f codecompanion)

# Check memory leaks
valgrind --tool=memcheck python -m codecompanion.cli --check

# Profile memory usage
python -m memory_profiler codecompanion
```

**Solutions:**
```bash
# Restart service to clear memory
sudo systemctl restart codecompanion

# Reduce concurrent agents
export CC_MAX_CONCURRENT_AGENTS=2

# Add memory limits
systemctl edit codecompanion
# Add:
[Service]
MemoryMax=1G
MemoryHigh=800M
```

### Slow Response Times

**Symptoms:**
- API endpoints timing out
- Agent executions taking too long

**Diagnostic:**
```bash
# Profile API response times
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8000/health

# Check system resources
iostat -x 1 5
sar -u 1 5

# Monitor database queries
sqlite3 codecompanion.db "PRAGMA optimize;"
```

**Solutions:**
```bash
# Optimize database
sqlite3 codecompanion.db "VACUUM; ANALYZE;"

# Increase worker processes
export CC_WORKERS=4

# Enable caching
export CC_CACHE_ENABLED=true

# Upgrade hardware resources
```

## Network Issues

### Service Not Accessible Externally

**Symptoms:**
- Health check works locally but not remotely
- External API calls fail

**Diagnostic:**
```bash
# Check listening ports
netstat -tuln | grep :8000

# Test local connectivity
curl -v http://127.0.0.1:8000/health

# Test external connectivity
curl -v http://your-server:8000/health
```

**Solutions:**
```bash
# Check bind address
# Ensure service binds to 0.0.0.0:8000, not 127.0.0.1:8000

# Configure reverse proxy
sudo nginx -t
sudo systemctl reload nginx

# Update firewall rules
sudo ufw allow 8000/tcp
```

### SSL/TLS Certificate Issues

**Symptoms:**
- HTTPS connections failing
- Certificate validation errors

**Diagnostic:**
```bash
# Test SSL certificate
openssl s_client -connect your-domain:443 -servername your-domain

# Check certificate validity
curl -vI https://your-domain/health

# Check certificate files
ls -la /etc/letsencrypt/live/your-domain/
```

**Solutions:**
```bash
# Renew certificates
sudo certbot renew

# Update Nginx configuration
sudo nginx -t
sudo systemctl reload nginx

# Force certificate refresh
sudo certbot renew --force-renewal
```

## Agent-Specific Issues

### Analyzer Agent Failures

**Common Issues:**
- Code parsing errors
- Large file handling problems

**Solutions:**
```bash
# Increase memory limits
export CC_ANALYZER_MEMORY_LIMIT=2GB

# Skip problematic files
echo "*.min.js" >> .ccignore
echo "node_modules/" >> .ccignore

# Update file size limits
export CC_MAX_FILE_SIZE=1MB
```

### Fixer Agent Patch Failures

**Common Issues:**
- Git apply failures
- Patch conflicts

**Solutions:**
```bash
# Check git status
git status

# Clean working directory
git stash push -m "pre-fixer-cleanup"

# Apply patches manually
git apply --check patch.diff
git apply patch.diff

# Reset if needed
git reset --hard HEAD
```

## Logging and Debug Mode

### Enable Debug Logging

```bash
# Environment variable
export CC_LOG_LEVEL=DEBUG

# Command line flag
codecompanion --run Analyzer --debug

# Configuration file
echo '{"log_level": "DEBUG"}' > .codecompanion.json
```

### Log File Locations

```bash
# Application logs
/var/log/codecompanion/app.log

# Agent-specific logs
.cc/logs/installer.log
.cc/logs/analyzer.log
.cc/logs/fixer.log

# System logs
journalctl -u codecompanion
```

## Emergency Procedures

### Service Recovery

```bash
#!/bin/bash
# emergency-recovery.sh

echo "🚨 Starting emergency recovery procedure..."

# Stop service
sudo systemctl stop codecompanion

# Backup current state
cp -r .cc/ .cc.backup.$(date +%s)/
cp codecompanion.db codecompanion.db.backup.$(date +%s)

# Clear problematic state
rm -rf .cc/cache/
rm -rf .cc/temp/

# Reset to known good configuration
git checkout HEAD -- .codecompanion.json

# Restart service
sudo systemctl start codecompanion

# Wait and check
sleep 10
./health-check.sh

echo "✅ Emergency recovery completed"
```

### Complete Reinstallation

```bash
#!/bin/bash
# complete-reinstall.sh

# Backup data
./backup-database.sh
./backup-config.sh

# Uninstall
pip uninstall -y codecompanion
rm -rf .cc/
rm .codecompanion.json

# Clean installation
pip install git+https://github.com/your-repo/codecompanion.git

# Restore configuration
tar -xzf config_backup.tar.gz

# Verify installation
codecompanion --check

echo "✅ Complete reinstallation finished"
```

## Getting Help

### Information to Collect

When seeking support, gather this information:

```bash
# System information
uname -a
python --version
pip --version

# CodeCompanion version
codecompanion --version

# Configuration
cat .codecompanion.json

# Recent logs
tail -n 100 /var/log/codecompanion/app.log

# Environment variables (sanitized)
env | grep -E "CC_|ANTHROPIC|OPENAI|GEMINI" | sed 's/=.*$/=***/'
```

### Support Channels

1. **Documentation Review**: Check all documentation files thoroughly
2. **Issue Search**: Search existing GitHub issues
3. **Community Forums**: Check community discussions
4. **Professional Support**: Contact for enterprise support

### Reporting Bugs

Include in bug reports:
- Exact error messages
- Steps to reproduce
- System information
- Configuration files (sanitized)
- Relevant log entries

Remember: Most issues have simple solutions. Work through this guide systematically, and don't hesitate to ask for help when needed.