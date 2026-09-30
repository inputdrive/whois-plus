import argparse
import re
import sys
import whois
import time

# Labels only (no TLD); hyphens allowed but not at start/end
_LABEL_RE = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$')
_PARSER = getattr(whois, "parser", None)
_WHOIS_NOT_FOUND_ERRORS = tuple(
    exc for exc in (
        getattr(_PARSER, "PywhoisError", None),  # older python-whois
        getattr(_PARSER, "WhoisDomainNotFoundError", None),  # current python-whois
        getattr(whois, "WhoisError", None),
    )
    if isinstance(exc, type) and issubclass(exc, Exception)
)


def is_available(domain):
    try:
        w = whois.whois(domain)
        return w.domain_name is None
    except _WHOIS_NOT_FOUND_ERRORS:
        return True  # authoritative "not found" response


def load_tlds(filename='tlds.txt'):
    try:
        with open(filename, 'r') as f:
            tlds = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    tlds.append(line.lower())
            return tlds
    except FileNotFoundError:
        print(f"TLD list not found: {filename}")
        sys.exit(1)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Check a domain label against all TLDs via WHOIS.",
        epilog=(
            "Examples:\n"
            "  python3 lookup.py                 interactive prompt\n"
            "  python3 lookup.py mysite          check mysite across all TLDs\n"
            "  python3 lookup.py mysite --tlds custom_tlds.txt\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        'domain',
        nargs='?',
        help='Domain label without TLD (e.g. mysite). Prompts if omitted.',
    )
    parser.add_argument(
        '--tlds',
        default='tlds.txt',
        metavar='FILE',
        help='TLD list file (default: tlds.txt)',
    )
    return parser.parse_args(argv)


def validate_label(domain_name):
    if not _LABEL_RE.match(domain_name):
        print("Invalid domain label. Use only letters, digits, and hyphens.")
        sys.exit(1)


def run_lookup(domain_name, tlds_file='tlds.txt'):
    print(f"\nLoading TLD list...")
    tlds = load_tlds(tlds_file)
    print(f"Found {len(tlds)} TLDs to check.\n")

    available_domains = []
    registered_domains = []

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
                    avail_f.flush()
                else:
                    registered_domains.append(full_domain)
                    print(f"✗ {full_domain} - registered")
                    reg_f.write(f"{full_domain}\n")
                    reg_f.flush()

                if i < len(tlds):
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n\nStopped by user after checking {i} of {len(tlds)} TLDs.")
                break
            except Exception as e:
                print(f"⚠ {full_domain} - error: {str(e)}")

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
        for domain in available_domains[:20]:
            print(f"  - {domain}")
        if len(available_domains) > 20:
            print(f"  ... and {len(available_domains) - 20} more")


def read_domain_label(args):
    if args.domain is None:
        try:
            return input("Enter domain name (without TLD extension): ").strip()
        except EOFError:
            print("No domain entered.")
            sys.exit(1)
    return args.domain.strip()


def main(argv=None):
    args = parse_args(argv)
    domain_name = read_domain_label(args)
    validate_label(domain_name)
    run_lookup(domain_name, args.tlds)


if __name__ == "__main__":
    main()
