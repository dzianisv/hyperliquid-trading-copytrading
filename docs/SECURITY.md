# Security Policy

## Supported Versions

We actively maintain and provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | ✅ |
| 1.x.x   | ❌ |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability, please follow these guidelines:

### 🔒 Private Disclosure

**DO NOT** create public GitHub issues for security vulnerabilities. Instead, please:

1. **Email us directly** at: [security@hyperliquid-copytrader.com](mailto:security@hyperliquid-copytrader.com)
2. **Include detailed information** about the vulnerability
3. **Provide steps to reproduce** if possible
4. **Wait for our response** before making any public disclosure

### 📝 What to Include

When reporting a vulnerability, please include:

- **Description** of the vulnerability
- **Steps to reproduce** the issue
- **Potential impact** assessment
- **Suggested fix** (if you have one)
- **Your contact information** for follow-up

### ⏱️ Response Timeline

- **Initial Response**: Within 48 hours
- **Detailed Assessment**: Within 1 week
- **Fix Development**: 2-4 weeks (depending on complexity)
- **Public Disclosure**: After fix is released

### 🛡️ Security Best Practices

To help keep your deployment secure:

#### API Security
- **Never share** your HyperLiquid API private keys
- **Use read-only keys** when possible
- **Rotate keys regularly** (monthly recommended)
- **Monitor API usage** for unusual activity

#### Server Security
- **Keep your VPS updated** with latest security patches
- **Use SSH key authentication** instead of passwords
- **Enable fail2ban** or similar intrusion prevention
- **Monitor logs** for suspicious activity
- **Use a firewall** to restrict unnecessary ports

#### Application Security
- **Run with minimal privileges** (don't use root)
- **Keep dependencies updated** regularly
- **Use secure networks** (avoid public WiFi)
- **Enable logging** for audit trails
- **Backup configurations** securely

#### Trading Security
- **Start with small amounts** to test functionality
- **Set reasonable trade limits** to minimize exposure
- **Monitor positions** regularly
- **Have emergency stop procedures** ready
- **Keep offline backups** of important data

### 🚨 Known Security Considerations

#### Network Exposure
- The application connects to remote servers via SSH
- API keys are transmitted to HyperLiquid servers
- Consider using VPN for additional network security

#### Data Storage
- Credentials are stored in system keyring
- Logs may contain sensitive trading information
- Configuration files should have restricted permissions

#### Dependencies
- We regularly audit third-party dependencies
- Automatic updates may introduce vulnerabilities
- Consider pinning dependency versions in production

### 🔍 Security Auditing

#### Self-Assessment Checklist

Before deploying, verify:

- [ ] API keys have minimal required permissions
- [ ] SSH access is properly secured
- [ ] Server is hardened and updated
- [ ] Monitoring and alerting is configured
- [ ] Backup and recovery procedures are tested
- [ ] Trade limits are appropriately set
- [ ] Network connections are secured

#### Professional Audit

For production deployments with significant capital:

- Consider professional security auditing
- Implement additional monitoring solutions
- Use multi-signature wallets where possible
- Implement circuit breakers for unusual activity

### 📞 Emergency Contact

If you discover an active exploit or urgent security issue:

- **Immediate**: Email [security@hyperliquid-copytrader.com](mailto:security@hyperliquid-copytrader.com)
- **Critical**: Contact project maintainers directly via GitHub
- **Public Safety**: If user funds are at immediate risk, consider responsible public disclosure

### 🏆 Recognition

We appreciate security researchers who help keep our project safe:

- **Acknowledgment** in our security advisory (if desired)
- **Attribution** in release notes
- **Direct communication** with development team
- **Consideration for bug bounty** (if program is active)

### 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CryptoCurrency Security Standard](https://cryptoconsortium.github.io/CCSS/)
- [API Security Best Practices](https://owasp.org/www-project-api-security/)
- [SSH Hardening Guide](https://www.ssh.com/academy/ssh/security)

---

**Remember**: Security is a shared responsibility. While we work hard to make our software secure, proper configuration and operational security are equally important for protecting your assets.
