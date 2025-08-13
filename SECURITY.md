# CodeCompanion Security Best Practices

## Production Security Guidelines

CodeCompanion is designed for production deployment with multiple security layers. Follow these guidelines to ensure secure operation.

## API Key Management

### Environment Variables
Store all API keys in environment variables, never in code:

```bash
# Required for full functionality
ANTHROPIC_API_KEY=sk-ant-...    # Claude API access
OPENAI_API_KEY=sk-...           # GPT-4 API access  
GEMINI_API_KEY=AIza...          # Gemini API access

# Optional production settings
CC_TOKEN=your-secure-token      # API authentication token
REDIS_URL=redis://...           # Event bus (production)
DATABASE_URL=postgres://...     # Database (production)
```

### Key Rotation Policy
- Rotate API keys every 90 days
- Use different keys for development/staging/production
- Monitor key usage through provider dashboards
- Immediately revoke compromised keys

### Key Security
- Never log API keys in application logs
- Use secrets management systems (AWS Secrets Manager, HashiCorp Vault)
- Encrypt keys at rest in configuration management
- Limit key permissions to minimum required scope

## Network Security

### HTTPS/TLS
- Always use HTTPS in production
- Enable HTTP Strict Transport Security (HSTS)
- Use TLS 1.2 or higher
- Implement proper certificate management

### Firewall Configuration
```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH (restrict source IPs)
ufw allow 443/tcp   # HTTPS
ufw allow 80/tcp    # HTTP (redirect to HTTPS)
ufw deny 8000/tcp   # Block direct API access
```

### Rate Limiting
Implement rate limiting to prevent abuse:

```nginx
# Nginx rate limiting example
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=install:1m rate=1r/s;

location /api/ {
    limit_req zone=api burst=20 nodelay;
}

location /install {
    limit_req zone=install burst=3 nodelay;
}
```

## Authentication & Authorization

### API Token Authentication
Enable token-based authentication for production:

```python
# Set in environment
CC_TOKEN=your-256-bit-secure-random-token

# API calls require header
Authorization: Bearer your-256-bit-secure-random-token
```

### Token Generation
```bash
# Generate secure tokens
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Access Control
- Implement IP whitelisting for sensitive endpoints
- Use role-based access control (RBAC) for multi-user deployments
- Log all authentication attempts
- Implement session timeout policies

## Input Validation & Sanitization

### Request Validation
- Validate all input parameters
- Sanitize user-provided data
- Implement request size limits
- Use schema validation for JSON payloads

### Code Injection Prevention
- Never execute user-provided code directly
- Use sandboxed execution environments
- Validate file paths and prevent directory traversal
- Implement content security policies (CSP)

## Database Security

### Connection Security
```python
# Use encrypted connections
DATABASE_URL=postgres://user:pass@host:5432/db?sslmode=require

# Connection pooling with limits
SQLALCHEMY_POOL_SIZE=10
SQLALCHEMY_MAX_OVERFLOW=20
```

### Data Protection
- Encrypt sensitive data at rest
- Use parameterized queries to prevent SQL injection
- Implement database access logging
- Regular security updates for database software

## Logging & Monitoring

### Security Logging
Log security-relevant events:
- Authentication attempts (success/failure)
- API key usage and failures
- Rate limiting triggers
- Suspicious request patterns

### Log Protection
```bash
# Secure log file permissions
chmod 640 /var/log/codecompanion/*.log
chown codecompanion:codecompanion /var/log/codecompanion/

# Rotate logs regularly
logrotate -f /etc/logrotate.d/codecompanion
```

### Monitoring Alerts
Set up alerts for:
- Multiple authentication failures
- Unusual API usage patterns
- High error rates
- Performance anomalies

## Container Security (Docker)

### Base Image Security
```dockerfile
# Use minimal, security-updated base images
FROM python:3.11-slim-bullseye

# Run as non-root user
RUN groupadd -r codecompanion && useradd -r -g codecompanion codecompanion
USER codecompanion

# Remove unnecessary packages
RUN apt-get purge -y --auto-remove
```

### Runtime Security
```bash
# Run with security options
docker run --security-opt=no-new-privileges \
           --cap-drop=ALL \
           --read-only \
           --tmpfs /tmp:rw,noexec,nosuid,size=100m \
           codecompanion:latest
```

## Cloud Deployment Security

### AWS Security
- Use IAM roles with least privilege
- Enable CloudTrail for audit logging
- Use VPC with private subnets
- Enable AWS Config for compliance monitoring

### Environment Variables
```bash
# AWS Parameter Store
aws ssm put-parameter --name "/codecompanion/prod/anthropic-key" \
                      --value "sk-ant-..." \
                      --type "SecureString"
```

### Load Balancer Configuration
- Enable AWS WAF for application firewall
- Configure SSL/TLS termination
- Implement health checks
- Use multiple availability zones

## Incident Response

### Preparation
1. Create incident response playbook
2. Establish communication channels
3. Prepare forensics tools
4. Document recovery procedures

### Response Procedures
1. **Identify** - Detect and analyze security incidents
2. **Contain** - Isolate affected systems
3. **Eradicate** - Remove threats from environment
4. **Recover** - Restore systems to normal operation
5. **Learn** - Document lessons and improve security

### Emergency Contacts
```bash
# Emergency shutdown
docker stop $(docker ps -q --filter ancestor=codecompanion)

# Revoke API keys immediately
# Check provider documentation for emergency revocation
```

## Compliance & Auditing

### Security Audits
- Regular penetration testing
- Code security reviews
- Dependency vulnerability scanning
- Infrastructure security assessment

### Compliance Requirements
- Document security controls
- Maintain audit trails
- Implement data retention policies
- Regular compliance assessments

## Security Testing

### Automated Security Scanning
```bash
# Dependency vulnerability scanning
pip install safety
safety check

# Container image scanning
docker scan codecompanion:latest

# Code security analysis
bandit -r . -f json -o security-report.json
```

### Security Test Integration
```yaml
# GitHub Actions security testing
- name: Security Scan
  run: |
    pip install safety bandit
    safety check
    bandit -r . -f json -o bandit-report.json
```

## Best Practices Summary

1. **Never expose API keys** in code, logs, or public repositories
2. **Use HTTPS everywhere** with proper certificate management
3. **Implement defense in depth** with multiple security layers
4. **Monitor and log** all security-relevant events
5. **Keep dependencies updated** with automated vulnerability scanning
6. **Use least privilege principle** for all access controls
7. **Encrypt data** at rest and in transit
8. **Regular security testing** and vulnerability assessments
9. **Incident response plan** with clear procedures
10. **Security awareness training** for all team members

## Support

For security issues or questions:
- Review this documentation thoroughly
- Check provider security documentation
- Consider professional security consultation
- Report security vulnerabilities responsibly

Remember: Security is a continuous process, not a one-time setup. Regularly review and update these practices as your deployment evolves.