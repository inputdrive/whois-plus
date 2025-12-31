# Python WHOIS Domain Checker

A collection of Python scripts for checking domain name availability using both traditional WHOIS and modern RDAP protocols.

## Features

- **Bulk TLD Checker** (`lookup.py`) - Check domain availability across all 1,500+ TLDs
- **RDAP Lookup** (`rdap_bootstrap.py`) - Modern RDAP protocol for detailed domain information
- Automatic rate limiting to prevent server blocks
- Results saved to organized output files
- Real-time progress tracking

## Installation

### 1. Clone or navigate to the repository
```bash
cd /path/to/python-whois
```

### 2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Bulk TLD Checker (`lookup.py`)

Checks a single domain name across all available TLDs (e.g., checks "mysite" against .com, .net, .org, etc.).

```bash
python3 lookup.py
```

**Prompts:**
- Enter domain name (without TLD extension)

**Output Files:**
- `{domain_name}_available.txt` - List of available domains
- `{domain_name}_registered.txt` - List of registered domains

**Features:**
- Checks 1,500+ TLDs automatically
- 1-second rate limiting between queries
- Real-time progress with ✓/✗ indicators
- Can be interrupted with Ctrl+C (progress saved)
- Estimated time: 25-30 minutes for full scan

**Example:**
```
Enter domain name (without TLD extension): mysite

Loading TLD list...
Found 1503 TLDs to check.

Checking availability (this may take a while)...

✓ mysite.com - AVAILABLE
✗ mysite.net - registered
✓ mysite.org - AVAILABLE
...

Results saved to:
  - mysite_available.txt
  - mysite_registered.txt
```

### RDAP Lookup (`rdap_bootstrap.py`)

Uses modern RDAP protocol to check individual domains with detailed registration information.

```bash
python3 rdap_bootstrap.py
```

**Prompts:**
- Enter full domain name (e.g., example.com)

**Output Files:**
- `{domain_name}_rdap_available.txt` - Available domains (appended)
- `{domain_name}_rdap_registered.txt` - Registered domains with details (appended)

**Features:**
- Detailed registration information
- Registrar name
- Registration and expiration dates
- Domain status codes
- No rate limiting needed (single query)

**Example:**
```
Enter domain to check (e.g., example.com): google.com

Checking: google.com

Result:
{
  "available": false,
  "registered": "1997-09-15T04:00:00Z",
  "expires": "2028-09-14T04:00:00Z",
  "last_changed": "2025-12-31T18:15:21Z",
  "statuses": [
    "client delete prohibited",
    "client transfer prohibited"
  ],
  "registrar": "MarkMonitor Inc."
}

Domain saved to google_com_rdap_registered.txt
```

## Files

- `lookup.py` - Bulk domain checker using WHOIS
- `rdap_bootstrap.py` - RDAP protocol checker for detailed info
- `tlds.txt` - Official IANA TLD list (auto-downloaded)
- `requirements.txt` - Python dependencies
- Output files created during execution

## Requirements

- Python 3.7+
- Dependencies:
  - `python-whois` - WHOIS protocol client
  - `requests` - HTTP requests for RDAP
  - `python-dateutil` - Date parsing

## Rate Limiting

- **WHOIS servers** enforce rate limits (1-10 queries/second)
- `lookup.py` includes 1-second delays to prevent blocks
- Adjust `time.sleep(1)` if needed, but be cautious
- RDAP queries are typically less restrictive

## Notes

- WHOIS lookups may fail for some TLDs (server issues, restrictions)
- Some registries return different response formats
- Available status should be verified before registration
- Results are appended to files, allowing multiple runs

## License

MIT License - Free to use and modify
