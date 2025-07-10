# Security Policy

## Security Standards Compliance

This project follows industry-standard security guidelines and best practices to ensure the safety and integrity of the Ollama-OpenAI proxy service.

### 🔒 OWASP Compliance

We adhere to the following OWASP security standards:

- **[OWASP Top 10](https://owasp.org/www-project-top-ten/)** - Web application security risks
- **[OWASP API Security Top 10](https://owasp.org/www-project-api-security/)** - API-specific security vulnerabilities
- **[OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)** - Development guidelines

## Implemented Security Measures

### 🛡️ Input Validation

- **Pydantic Model Validation**: All API inputs are validated using strict Pydantic models with type checking
- **Request Size Limits**: Maximum request payload size enforced (configurable, default 10MB)
- **Content Type Validation**: Strict content-type checking for all endpoints
- **Parameter Sanitization**: All query parameters and path variables are validated and sanitized

```python
# Example: Strict validation in chat requests
class OpenAIChatRequest(BaseModel):
    model: str = Field(..., min_length=1, max_length=100)
    messages: List[ChatMessage] = Field(..., min_items=1, max_items=100)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=32000)
```

### 🔐 Authentication & Authorization

- **API Key Validation**: Secure validation and forwarding of API keys to backend services
- **No Credential Storage**: API keys are never logged, cached, or stored in the application
- **Environment-Based Configuration**: All secrets managed through environment variables
- **Secure Forwarding**: API keys are securely transmitted to backend services over HTTPS

### 🚨 Error Handling

- **Generic Error Messages**: Production errors provide minimal information to prevent data leakage
- **Debug Mode Controls**: Detailed error information only available in development/debug mode
- **Request ID Tracking**: Unique request IDs for correlation without exposing sensitive data
- **Structured Logging**: Security events logged with appropriate detail levels

```python
# Example: Secure error handling
try:
    response = await backend_client.request(...)
except HTTPError as e:
    # Generic error - no backend details exposed
    raise ProxyError("Request failed", status_code=502)
```

### ⚡ Rate Limiting & DoS Protection

- **Connection Pooling**: Configurable connection limits to prevent resource exhaustion
- **Request Timeouts**: Enforced timeouts for all backend requests (default 60 seconds)
- **Graceful Degradation**: Service continues operating under high load conditions
- **Circuit Breaker**: Automatic backend failure detection and recovery

### 🔍 Monitoring & Auditing

- **Request Tracking**: All requests logged with unique IDs for security auditing
- **Performance Monitoring**: Real-time monitoring of request patterns and anomalies
- **Security Metrics**: Dedicated metrics for failed authentications and suspicious activity
- **Structured Logging**: JSON-formatted logs compatible with security information systems

## Security Scanning

### 🔍 Automated Security Checks

Our CI/CD pipeline includes comprehensive security scanning:

#### Container Security
- **Trivy**: Vulnerability scanning for container images and dependencies
- **Docker Security**: Multi-stage builds with minimal attack surface
- **Non-root Execution**: Containers run as non-privileged user

#### Code Security  
- **Bandit**: Python security linting for common security issues
- **TruffleHog**: Secret detection in source code and git history
- **GitHub Security**: Automated dependency vulnerability scanning

#### Dependency Management
- **Dependabot**: Automated security updates for dependencies
- **License Compliance**: Verification of open source license compatibility
- **SBOM Generation**: Software Bill of Materials for transparency

### 📊 Security Metrics

We track the following security-related metrics:

- Authentication failure rates
- Request validation errors
- Backend connection failures
- Rate limiting activations
- Error response patterns

## Deployment Security

### 🐳 Container Security

```dockerfile
# Security-hardened Docker configuration
FROM python:3.12-slim
RUN useradd --create-home --shell /bin/bash appuser
USER appuser
WORKDIR /app
COPY --chown=appuser:appuser . .
```

### 🌐 Network Security

- **HTTPS Only**: All production deployments require TLS/SSL termination
- **Secure Headers**: Appropriate security headers for web requests
- **CORS Configuration**: Properly configured cross-origin resource sharing
- **Private Networks**: Backend communication over private networks when possible

### 🔧 Configuration Security

```bash
# Required environment variables
OPENAI_API_KEY=<secure_api_key>           # Backend authentication
OPENAI_API_BASE_URL=<https_backend_url>   # Secure backend endpoint
LOG_LEVEL=INFO                            # Appropriate logging level
```

## Vulnerability Reporting

### 🚨 Responsible Disclosure

We appreciate security researchers and users who help improve our security. Please follow responsible disclosure practices:

#### Contact Information
- **Security Email**: [Create security email address]
- **GitHub Security**: Use [GitHub Security Advisories](https://github.com/eyalrot/ollama_openai/security/advisories)
- **Response Time**: We aim to respond within 48 hours

#### Reporting Guidelines

1. **Provide Detailed Information**:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Suggested remediation (if known)

2. **Do Not**:
   - Publicly disclose the vulnerability before we've had time to address it
   - Access or modify data that doesn't belong to you
   - Perform DoS attacks or destructive testing

3. **Safe Harbor**:
   - We will not pursue legal action against security researchers who follow responsible disclosure
   - We welcome coordination on public disclosure timing

### 🏆 Recognition

We maintain a security acknowledgments section for researchers who help improve our security:

- [Future security contributors will be listed here]

## Security Checklist

### Development Security Checklist

- [ ] **No Hardcoded Credentials**: All secrets use environment variables
- [ ] **Input Validation**: All user inputs validated with Pydantic models  
- [ ] **Secure Error Handling**: Generic error messages in production
- [ ] **HTTPS Enforcement**: All external communications use TLS
- [ ] **Dependency Updates**: Regular security updates applied
- [ ] **Code Review**: Security-focused peer review process
- [ ] **Testing**: Security test cases for critical functionality

### Deployment Security Checklist

- [ ] **Environment Isolation**: Separate environments for dev/staging/prod
- [ ] **Access Controls**: Principle of least privilege for system access
- [ ] **Monitoring**: Security monitoring and alerting configured
- [ ] **Backup Security**: Secure backup and recovery procedures
- [ ] **Incident Response**: Security incident response plan documented
- [ ] **Regular Audits**: Periodic security assessments performed

### Operational Security Checklist

- [ ] **Log Monitoring**: Security events monitored and alerted
- [ ] **Performance Monitoring**: Anomaly detection for security incidents
- [ ] **Patch Management**: Timely application of security patches
- [ ] **Configuration Management**: Secure configuration baselines maintained
- [ ] **Training**: Security awareness for development team

## Compliance & Standards

### 📋 Security Standards

- **ISO 27001**: Information security management principles
- **NIST Cybersecurity Framework**: Risk-based security approach  
- **OWASP ASVS**: Application Security Verification Standard
- **CIS Controls**: Center for Internet Security guidelines

### 🔐 Data Protection

- **No Data Storage**: Proxy service does not store user data or conversations
- **Encryption in Transit**: All data encrypted during transmission
- **Minimal Data Processing**: Only necessary data processed for proxy functionality
- **Privacy by Design**: Privacy considerations built into system architecture

## Security Resources

### 📚 Additional Reading

- [OWASP Application Security](https://owasp.org/www-project-application-security-guide/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [API Security Best Practices](https://owasp.org/www-project-api-security/)
- [Container Security Guide](https://www.nist.gov/publications/application-container-security-guide)

### 🛠️ Security Tools

- [Trivy](https://trivy.dev/) - Vulnerability scanner
- [Bandit](https://bandit.readthedocs.io/) - Python security linter
- [TruffleHog](https://github.com/trufflesecurity/trufflehog) - Secret detection
- [Safety](https://github.com/pyupio/safety) - Python dependency checker

---

**Last Updated**: 2025-07-10  
**Version**: 1.0  
**Contact**: [Create security contact]

For questions about this security policy or to report security issues, please contact our security team using the channels listed in the Vulnerability Reporting section.