import requests
import json
from urllib.parse import urljoin
from typing import Optional

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
    domain = input("Enter domain to check (e.g., example.com): ").strip()
    
    if not domain:
        print("No domain entered.")
        exit(1)
    
    print(f"\nChecking: {domain}")
    result = check_domain_rdap(domain)
    
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