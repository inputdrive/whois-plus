# Python WHOIS Domain Checker

A collection of Python scripts for checking domain name availability using both traditional WHOIS and modern RDAP protocols.

## Features

- **Bulk TLD Checker** (`lookup.py`) - Check domain availability across all 1,500+ TLDs
- **RDAP Lookup** (`rdap_bootstrap.py`) - Modern RDAP protocol for detailed domain information
- **SQLite Database** - Store all lookups with full history tracking
- **Query Tool** (`query_history.py`) - Interactive menu or CLI subcommands to view historical data
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

**Interactive** (prompts for a label when no domain is given):
```bash
python3 lookup.py
```

**Scripted:**
```bash
python3 lookup.py mysite
python3 lookup.py mysite --tlds custom_tlds.txt
python3 lookup.py --help
```

**Arguments:**
- `domain` — domain label without TLD (required for non-interactive use)
- `--tlds FILE` — TLD list file (default: `tlds.txt`)

**Output Files:**
- `{domain_name}_available.txt` - List of available domains
- `{domain_name}_registered.txt` - List of registered domains

**Features:**
- Checks 1,500+ TLDs automatically
- 1-second rate limiting between queries
- Real-time progress with ✓/✗ indicators
- Can be interrupted with Ctrl+C (progress saved)
- Estimated time: 25-30 minutes for full scan

**Example (interactive):**
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

Uses modern RDAP protocol to check individual domains with detailed registration information. **All lookups are automatically saved to SQLite database for historical tracking.**

**Interactive** (prompts for a domain when none is given):
```bash
python3 rdap_bootstrap.py
```

**Scripted:**
```bash
python3 rdap_bootstrap.py example.com
python3 rdap_bootstrap.py example.com --db /tmp/lookups.db
python3 rdap_bootstrap.py --help
```

**Arguments:**
- `domain` — full domain name such as `example.com` (required for non-interactive use)
- `--db PATH` — SQLite database path (default: `domain_lookups.db`)

**Output:**
- **SQLite Database** (`domain_lookups.db`) - All lookups stored with full history
- `{domain_name}_rdap_available.txt` - Available domains (appended)
- `{domain_name}_rdap_registered.txt` - Registered domains with details (appended)

**Features:**
- **SQLite database storage** - Full historical tracking
- Detailed registration information
- Registrar name
- Registration and expiration dates
- Domain status codes
- Historical lookup tracking (shows previous checks)
- No rate limiting needed (single query)

**Example (interactive):**
```
Database initialized: domain_lookups.db

Enter domain to check (e.g., example.com): google.com

Checking: google.com
✓ Saved to database

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

📊 Historical lookups for google.com: 3 total
  Most recent checks:
  1. 2025-12-31T18:15:21Z - Registered
  2. 2025-12-30T10:20:15Z - Registered
  3. 2025-12-29T14:05:32Z - Registered
```

### Query Historical Data (`query_history.py`)

Query the SQLite database and view historical lookup data. With no command, the interactive menu is shown. Pass a subcommand to run a single query and exit.

**Interactive:**
```bash
python3 query_history.py
```

**Scripted:**
```bash
python3 query_history.py list
python3 query_history.py history example.com
python3 query_history.py available
python3 query_history.py expiring --days 30
python3 query_history.py recent --limit 10
python3 query_history.py stats
python3 query_history.py --db /tmp/lookups.db stats
python3 query_history.py --help
```

**Commands:**
- `list` — all domains in the database
- `history DOMAIN` — complete history for one domain
- `available` — domains available at last check
- `expiring [--days N]` — domains expiring within N days (default: 90)
- `recent [--limit N]` — most recent lookups (default: 20)
- `stats` — database statistics

**Global options:**
- `--db PATH` — SQLite database path (default: `domain_lookups.db`)

**Features:**
- View all domains in database
- Show complete history for any domain
- List available domains
- Find domains expiring soon
- View recent lookups
- Database statistics

**Example Menu:**
```
============================================================
Domain Lookup History Query Tool
============================================================
1. List all domains
2. View domain history
3. Show available domains
4. Show domains expiring soon
5. Show recent lookups
6. Database statistics
0. Exit
============================================================

📊 Database Statistics
============================================================
Total lookups: 47
Unique domains: 23
Available: 12
Registered: 35
First lookup: 2025-12-30T10:15:32Z
Last lookup: 2025-12-31T18:15:21Z
```

## Files

- `lookup.py` - Bulk domain checker using WHOIS
- `rdap_bootstrap.py` - RDAP protocol checker with SQLite storage
- `query_history.py` - Interactive menu or CLI to query lookup history
- `tlds.txt` - Official IANA TLD list (auto-downloaded)
- `requirements.txt` - Python dependencies
- `domain_lookups.db` - SQLite database (auto-created)
- Output text files created during execution

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
- `lookup.py` supports both old and current `python-whois` exception names when handling "domain not found" responses
- Available status should be verified before registration
- Results are appended to files, allowing multiple runs
- **SQLite database** stores complete history for trend analysis
- Database queries show how domain status changes over time
- Useful for monitoring domains you're tracking

## License

MIT License - Free to use and modify
