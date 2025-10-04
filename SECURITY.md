# Security Policy

## Supported Versions

We actively support the following versions of Tskr with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | ✅ Yes             |
| 1.x.x   | ❌ No (deprecated) |

## Reporting a Vulnerability

We take the security of Tskr seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### 🚨 Please DO NOT report security vulnerabilities through public GitHub issues.

Instead, please report them via one of the following methods:

### Preferred Method: GitHub Security Advisories

1. Go to the [Tskr repository](https://github.com/tskr-dev/tskr)
2. Click on the "Security" tab
3. Click "Report a vulnerability"
4. Fill out the form with details about the vulnerability

### Alternative Method: Email

Send an email to: **security@tskr.dev** (if available)

Include the following information:
- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

## Security Considerations

### Data Storage

Tskr stores data locally in the following locations:

- **Project data**: `.tskr/` directory in your project root
- **Configuration**: User's home directory (platform-specific)

**Security implications:**
- All data is stored in plain text files
- No encryption is applied to stored data
- File permissions follow system defaults
- Sensitive information should not be stored in task descriptions

### Network Communication

Tskr is primarily an offline tool:

- **No network communication** by default
- **No telemetry** or analytics collection
- **No automatic updates** or phone-home functionality
- Git integration uses your existing git configuration

### Code Execution

Tskr does not execute arbitrary code:

- **No eval()** or similar dynamic code execution
- **No shell command injection** vulnerabilities
- **No file inclusion** vulnerabilities
- All user input is validated and sanitized

### Dependencies

We regularly monitor our dependencies for security vulnerabilities:

- Dependencies are kept up-to-date
- Security advisories are monitored via GitHub Dependabot
- Automated dependency updates where appropriate

## Vulnerability Response Process

### Timeline

1. **Acknowledgment**: Within 48 hours of report
2. **Initial Assessment**: Within 5 business days
3. **Detailed Investigation**: Within 10 business days
4. **Resolution**: Varies based on complexity
5. **Disclosure**: After fix is available

### Response Actions

1. **Confirm** the vulnerability and determine affected versions
2. **Develop** a fix for the vulnerability
3. **Prepare** security advisory and release notes
4. **Release** patched versions
5. **Publish** security advisory
6. **Credit** the reporter (if desired)

### Disclosure Policy

- We follow **coordinated disclosure**
- We will work with you to understand and resolve the issue
- We will not disclose the vulnerability until a fix is available
- We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Best Practices for Users

### General Usage

1. **Keep Tskr updated** to the latest version
2. **Review permissions** of the `.tskr/` directory
3. **Avoid storing sensitive information** in task descriptions
4. **Use appropriate file permissions** for your project directory

### In Team Environments

1. **Review task content** before committing to version control
2. **Use `.gitignore`** to exclude sensitive files if needed
3. **Be mindful of task discussions** containing sensitive information
4. **Consider access controls** for shared repositories

### CI/CD Integration

1. **Review GitHub Actions workflows** before enabling
2. **Use secrets management** for sensitive configuration
3. **Limit permissions** of automation tokens
4. **Monitor build logs** for sensitive information leakage

## Known Security Limitations

### File System Access

- Tskr requires read/write access to your project directory
- No sandboxing or access restrictions are implemented
- Users are responsible for appropriate file permissions

### Input Validation

- While we validate input, complex edge cases may exist
- Large inputs are not explicitly limited
- File path traversal protections are basic

### Multi-user Environments

- Tskr is designed for single-user or trusted team environments
- No built-in access controls or user authentication
- Concurrent access may lead to data corruption

## Security Updates

Security updates will be:

1. **Released immediately** for critical vulnerabilities
2. **Documented** in the CHANGELOG.md
3. **Announced** via GitHub releases
4. **Tagged** with security labels

## Contact Information

For security-related questions or concerns:

- **Security Reports**: Use GitHub Security Advisories
- **General Questions**: Open a GitHub Discussion
- **Documentation Issues**: Open a GitHub Issue

## Acknowledgments

We would like to thank the following individuals for responsibly disclosing security vulnerabilities:

<!-- This section will be updated as reports are received -->

*No security reports have been received yet.*

---

**Thank you for helping keep Tskr and our users safe! 🔒**
