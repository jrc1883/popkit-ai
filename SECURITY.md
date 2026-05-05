# Security Policy

## Supported Versions

PopKit is currently in beta. Security updates are provided for the latest beta version.

| Version        | Supported              |
| -------------- | ---------------------- |
| 1.0.0-beta.x   | ✅ Active support      |
| < 1.0.0-beta.1 | ❌ No longer supported |

## Security Features

PopKit implements multiple layers of security:

- **Secret Scanning**: GitHub secret scanning with push protection enabled
- **Dependency Monitoring**: Dependabot alerts and automatic security updates
- **Code Analysis**: CodeQL security scanning for vulnerabilities
- **IP Leak Prevention**: Automated scanning to prevent accidental exposure of proprietary code
- **Workflow Security**: Restricted GitHub Actions permissions (read-only by default)

## Reporting a Vulnerability

**We take security seriously.** If you discover a security vulnerability, please report it responsibly.

### Preferred Method: Private Vulnerability Reporting

Use GitHub's private vulnerability reporting feature:

1. Go to the [Security tab](https://github.com/jrc1883/popkit-ai/security)
2. Click "Report a vulnerability"
3. Fill out the vulnerability details
4. Submit privately to maintainers

**Do not** open a public issue for security vulnerabilities.

### Alternative Method: Email

If you cannot use private reporting, email security concerns to:

📧 **joseph@thehouseofdeals.com**

Subject line: `[SECURITY] PopKit Vulnerability Report`

### What to Include

Please provide:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)
- Your contact information for follow-up

## Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies by severity
  - Critical: 1-7 days
  - High: 7-30 days
  - Medium: 30-90 days
  - Low: Next release cycle

## Security Best Practices for Users

### Plugin Installation

1. **Verify Source**: Only install PopKit from official sources
   - GitHub: https://github.com/jrc1883/popkit-ai
   - Claude Code Marketplace: `@popkit-ai`

2. **Check Integrity**: Review `plugin.json` and hook scripts before installation

3. **Monitor Permissions**: PopKit hooks use restricted tool permissions by design

### Hook Security

PopKit hooks follow strict security guidelines:

- Use `${CLAUDE_PLUGIN_ROOT}` for portability
- No arbitrary command execution
- JSON stdin/stdout protocol
- Explicit tool whitelisting

### API Keys (Optional Enhancement Features)

If using PopKit Cloud features:

- **Never commit** API keys to repositories
- Store in `.env` files (gitignored)
- Use environment variables in CI/CD
- Rotate keys regularly

## Known Security Considerations

### Issue #20: Command Injection Vulnerabilities (In Progress)

- **Status**: Active remediation
- **Impact**: Some utility functions use `subprocess.run(shell=True)`
- **Timeline**: Fix targeted for v1.0.0 release
- **Tracking**: https://github.com/jrc1883/popkit-ai/issues/20

### Plugin Hooks

PopKit hooks execute Python scripts with Claude Code's permissions. Key protections:

- Hooks are user-installed (explicit consent)
- Source code is visible in repository
- Restricted tool permissions
- No network access by default

## Security Disclosure Policy

### Public Disclosure

After a vulnerability is fixed:

1. Security advisory published on GitHub
2. CVE requested for critical vulnerabilities
3. Fix details disclosed responsibly
4. Credit given to reporter (with permission)

### Hall of Fame

We recognize security researchers who responsibly disclose vulnerabilities:

_No vulnerabilities reported yet._

## Compliance & Standards

PopKit follows:

- OWASP Top 10 security practices
- GitHub Security Best Practices
- Principle of least privilege
- Defense in depth

## Questions?

For security questions that aren't vulnerabilities:

- Open a [GitHub Discussion](https://github.com/jrc1883/popkit-ai/discussions)
- Email: joseph@thehouseofdeals.com

---

**Last Updated**: 2026-01-08
**Security Contact**: joseph@thehouseofdeals.com
