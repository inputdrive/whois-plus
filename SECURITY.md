# Security Policy

## Supported Versions
- Main branch (active development)
- No LTS branches; update to the latest commit for fixes

## Reporting a Vulnerability
- Please email inputdrive@gmail.com with:
  - Detailed description and impact
  - Steps to reproduce (commands, inputs, expected vs. actual)
  - Affected files/versions (commit SHA if possible)
  - Suggested fix or mitigation if known
- Do not open public issues for security reports.
- We aim to acknowledge within 3 business days and provide a fix or mitigation timeline after triage.

## Disclosure
- Follow coordinated disclosure; please allow us time to investigate and release a fix before public disclosure.
- Once resolved, we will note the fix in commit history and release notes (if applicable).

## Hardening Guidelines for Users
- Run in an isolated virtual environment (e.g., `python -m venv venv`).
- Use the latest Python 3.x and apply OS security updates.
- Keep dependencies up to date: `pip install --upgrade -r requirements.txt`.
- Avoid running against untrusted WHOIS/RDAP endpoints.
- Store any API keys or secrets in environment variables or `.env` (already git-ignored).

## Dependencies
- See `requirements.txt` for runtime dependencies.
- If you find a vulnerability in a dependency, include the package name and version in your report.

## Data Handling
- The tool writes lookup results to local text files and `domain_lookups.db` (SQLite). Review and protect these files if they contain sensitive domains or history.
