# Security policy

## Supported versions

Security fixes are applied to the latest revision on the default branch. This beta playground does
not currently maintain multiple supported release lines.

## Reporting a vulnerability

Do not open a public issue for a vulnerability that could expose secrets, enable remote abuse, or
affect users of a deployed instance.

Use the repository's private GitHub vulnerability-reporting or Security Advisory feature. Include:

- Affected component and version or commit
- Reproduction steps or a minimal proof of concept
- Expected impact
- Suggested mitigation, if known

If private reporting is not enabled, contact a listed repository maintainer privately and ask for a
secure reporting channel without including sensitive details in the first message.

The maintainers will acknowledge a complete report, assess impact, coordinate a fix, and credit the
reporter when requested and appropriate. No fixed response-time service level is promised.

## Security model

This project is an unauthenticated interoperability playground, not a production multi-tenant
service. The built-in rate limiter protects model budget only; it is not an authorization or
distributed abuse-prevention mechanism.

Review [deployment security](docs/deployment.md#security-boundary) before exposing any endpoint.
Never commit NVIDIA credentials or send personal, payment, or confidential data to a demo instance.
