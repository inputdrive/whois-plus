import whois
import time

def is_available(domain):
    try:
        w = whois.whois(domain)
        return False  # domain exists → registered
    except Exception:  # Catch all exceptions (domain not found, connection errors, etc.)
        return True   # domain not found → available

def load_tlds(filename='tlds.txt'):
    """Load TLDs from the IANA TLD list file."""
    with open(filename, 'r') as f:
        tlds = []
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                tlds.append(line.lower())
        return tlds

# Usage
domain_name = input("Enter domain name (without TLD extension): ").strip()
print(f"\nLoading TLD list...")
tlds = load_tlds()
print(f"Found {len(tlds)} TLDs to check.\n")

available_domains = []
registered_domains = []

# Open output files
available_file = f"{domain_name}_available.txt"
registered_file = f"{domain_name}_registered.txt"

with open(available_file, 'w') as avail_f, open(registered_file, 'w') as reg_f:
    avail_f.write(f"Available domains for: {domain_name}\n")
    avail_f.write(f"{'='*60}\n\n")
    reg_f.write(f"Registered domains for: {domain_name}\n")
    reg_f.write(f"{'='*60}\n\n")
    
    print("Checking availability (this may take a while)...\n")
    for i, tld in enumerate(tlds, 1):
        full_domain = f"{domain_name}.{tld}"
        try:
            is_avail = is_available(full_domain)
            if is_avail:
                available_domains.append(full_domain)
                print(f"✓ {full_domain} - AVAILABLE")
                avail_f.write(f"{full_domain}\n")
                avail_f.flush()  # Write immediately
            else:
                registered_domains.append(full_domain)
                print(f"✗ {full_domain} - registered")
                reg_f.write(f"{full_domain}\n")
                reg_f.flush()  # Write immediately
            
            # Rate limiting: wait 1 second between queries to avoid being blocked
            if i < len(tlds):  # Don't wait after the last one
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n\nStopped by user after checking {i} of {len(tlds)} TLDs.")
            break
        except Exception as e:
            print(f"⚠ {full_domain} - error: {str(e)}")

# Summary
print(f"\n{'='*60}")
print(f"SUMMARY for '{domain_name}'")
print(f"{'='*60}")
print(f"Available domains: {len(available_domains)}")
print(f"Registered domains: {len(registered_domains)}")
print(f"\nResults saved to:")
print(f"  - {available_file}")
print(f"  - {registered_file}")
if available_domains:
    print(f"\nAvailable domains:")
    for domain in available_domains[:20]:  # Show first 20
        print(f"  - {domain}")
    if len(available_domains) > 20:
        print(f"  ... and {len(available_domains) - 20} more")