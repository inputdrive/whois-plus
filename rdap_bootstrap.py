import requests
import json
from urllib.parse import urljoin
from typing import Optional
import sqlite3
from datetime import datetime

def init_database(db_path='domain_lookups.db'):
    """Initialize SQLite database with schema"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS domain_lookups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            tld TEXT,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            available BOOLEAN,
            registered_date TEXT,
            expiration_date TEXT,
            registrar TEXT,
            statuses TEXT,
            last_changed TEXT,
            raw_response TEXT
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_domain ON domain_lookups(domain)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_checked_at ON domain_lookups(checked_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_available ON domain_lookups(available)')
    
    conn.commit()
    conn.close()
    return db_path


def save_to_database(domain: str, result: dict, db_path='domain_lookups.db'):
    """Save RDAP lookup result to SQLite database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Extract TLD
    tld = domain.rsplit('.', 1)[1] if '.' in domain else None
    
    cursor.execute('''
        INSERT INTO domain_lookups 
        (domain, tld, checked_at, available, registered_date, expiration_date, 
         registrar, statuses, last_changed, raw_response)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        domain,
        tld,
        datetime.utcnow().isoformat() + 'Z',
        result.get('available'),
        result.get('registered'),
        result.get('expires'),
        result.get('registrar'),
        json.dumps(result.get('statuses', [])),
        result.get('last_changed'),
        json.dumps(result)
    ))
    
    conn.commit()
    conn.close()


def get_domain_history(domain: str, db_path='domain_lookups.db', limit=10):
    """Retrieve historical lookups for a domain"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT checked_at, available, registered_date, expiration_date, registrar
        FROM domain_lookups
        WHERE domain = ?
        ORDER BY checked_at DESC
        LIMIT ?
    ''', (domain, limit))
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            'checked_at': row[0],
            'available': row[1],
            'registered_date': row[2],
            'expiration_date': row[3],
            'registrar': row[4]
        }
        for row in results
    ]


def get_rdap_bootstrap():
    """Fetch current IANA RDAP bootstrap data for domains"""
    url = "https://data.iana.org/rdap/dns.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch IANA bootstrap: {e}")


def find_rdap_server(tld: str, bootstrap_data: dict) -> Optional[str]:
    """Find the RDAP base URL for a given TLD from bootstrap data"""
    tld = tld.lower().lstrip('.')  # Normalize
    
    for services in bootstrap_data.get("services", []):
        tlds = [t.lower() for t in services[0]]
        if tld in tlds:
            # Usually one URL, take the first one
            return services[1][0]
    return None


def check_domain_rdap(domain: str) -> dict:
    """
    Check domain registration status via RDAP.
    Returns a dict with 'available' (bool) and some basic info or error.
    """
    if '.' not in domain:
        raise ValueError("Domain must contain a TLD (e.g. example.com)")
    
    _, tld = domain.rsplit('.', 1)
    bootstrap = get_rdap_bootstrap()
    base_url = find_rdap_server(tld, bootstrap)
    
    if not base_url:
        raise ValueError(f"No RDAP server found for TLD .{tld}")
    
    query_url = urljoin(base_url.rstrip('/') + '/', f"domain/{domain.lower()}")
    
    try:
        resp = requests.get(query_url, timeout=12, headers={"Accept": "application/rdap+json"})
        
        if resp.status_code == 404:
            return {"available": True, "message": "Domain appears available (404 from RDAP)"}
        
        if resp.status_code != 200:
            return {"available": False, "error": f"HTTP {resp.status_code}", "raw": resp.text[:300]}
        
        data = resp.json()
        
        # Most registries return 200 even for available domains with special status
        # But the standard way: look for status codes
        statuses = [s.lower() for s in data.get("status", [])]
        
        if any("available" in s for s in statuses) or not data.get("events"):
            return {"available": True, "message": "Domain appears available"}
        
        # Registered domain usually has registration/expiration events
        events = {e["eventAction"]: e["eventDate"] for e in data.get("events", [])}
        
        # Extract registrar name safely
        registrar = None
        if data.get("entities"):
            for entity in data.get("entities", []):
                if "vcardArray" in entity:
                    vcard = entity["vcardArray"]
                    if len(vcard) >= 2 and isinstance(vcard[1], list):
                        for field in vcard[1]:
                            if isinstance(field, list) and len(field) >= 4:
                                if field[0] == "fn":  # Full name
                                    registrar = field[3]
                                    break
                    if registrar:
                        break
        
        result = {
            "available": False,
            "registered": events.get("registration"),
            "expires": events.get("expiration"),
            "last_changed": events.get("last update of RDAP database"),
            "statuses": data.get("status", []),
            "registrar": registrar
        }
        return result
    
    except Exception as e:
        return {"available": None, "error": str(e)}


# ──────────────────────────────────────────────
# User input and output
# ──────────────────────────────────────────────

if __name__ == "__main__":
    # Initialize database
    db_path = init_database()
    print(f"Database initialized: {db_path}\n")
    
    domain = input("Enter domain to check (e.g., example.com): ").strip()
    
    if not domain:
        print("No domain entered.")
        exit(1)
    
    print(f"\nChecking: {domain}")
    result = check_domain_rdap(domain)
    
    # Save to database
    save_to_database(domain, result, db_path)
    print(f"✓ Saved to database")
    
    # Prepare output with domain name prefix
    domain_name = domain.replace('.', '_')
    available_file = f"{domain_name}_rdap_available.txt"
    registered_file = f"{domain_name}_rdap_registered.txt"
    
    print(f"\nResult:")
    print(json.dumps(result, indent=2))
    
    # Write to files
    if result.get("available") is True:
        with open(available_file, 'a') as f:
            f.write(f"{domain}\n")
        print(f"\nDomain saved to {available_file}")
    elif result.get("available") is False:
        with open(registered_file, 'a') as f:
            f.write(f"{domain} - Registered on {result.get('registered', 'N/A')}, expires {result.get('expires', 'N/A')}\n")
        print(f"\nDomain saved to {registered_file}")
    else:
        print(f"\nUnable to determine status (error: {result.get('error', 'Unknown')})")
    
    # Show historical data if available
    history = get_domain_history(domain, db_path)
    if len(history) > 1:
        print(f"\n📊 Historical lookups for {domain}: {len(history)} total")
        print("  Most recent checks:")
        for i, record in enumerate(history[:3], 1):
            print(f"  {i}. {record['checked_at']} - {'Available' if record['available'] else 'Registered'}")