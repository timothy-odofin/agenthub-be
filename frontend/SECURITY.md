# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of AgentHub seriously. If you discover a security vulnerability, please follow these steps:

### Do Not
- **Do not** open a public issue on GitHub
- **Do not** disclose the vulnerability publicly before it has been addressed

### Do
1. **Email** the details to the repository owner through GitHub
2. Include:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact
   - Suggested fix (if any)

### What to Expect
- We will acknowledge receipt of your vulnerability report within 48 hours
- We will provide a more detailed response within 7 days
- We will work on a fix and keep you informed of progress
- Once the issue is resolved, we will publicly disclose the vulnerability (with your permission)

## Security Best Practices

When contributing to this project:

### Environment Variables
- Never commit `.env` files
- Use `.env.example` as a template
- Store sensitive data in environment variables

### API Keys & Secrets
- Never hardcode API keys, secrets, or tokens
- Use environment variables for configuration
- Rotate credentials regularly

### Dependencies
- Keep dependencies up to date
- Review security advisories regularly
- Run `npm audit` before deploying

### Code Review
- All pull requests require review
- Security-sensitive code requires extra scrutiny
- Test authentication and authorization changes thoroughly

## Known Security Considerations

### Authentication
- JWT tokens are stored in localStorage (consider HttpOnly cookies for production)
- Tokens should be rotated/refreshed regularly
- Implement proper logout to clear all tokens

### CORS
- Configure CORS properly in production
- Restrict allowed origins
- Use credentials only when necessary

### XSS Prevention
- React escapes values by default
- Be careful with `dangerouslySetInnerHTML`
- Sanitize user input in markdown rendering

### HTTPS
- Always use HTTPS in production
- Enable HSTS headers
- Use secure cookies

## Third-Party Dependencies

This project uses several third-party packages. We monitor them for security issues using:
- GitHub Dependabot
- npm audit
- Regular dependency updates

## Contact

For security concerns, please reach out through GitHub issues (for non-sensitive matters) or email the repository owner directly.
