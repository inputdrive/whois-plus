#!/usr/bin/env python3
"""
Query utility for domain lookup history stored in SQLite database
"""
import argparse
import json
import os
import sqlite3
import sys

DB_PATH = 'domain_lookups.db'

def get_all_domains(db_path=DB_PATH):
    """Get list of all domains in database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT domain, COUNT(*) as count FROM domain_lookups GROUP BY domain ORDER BY count DESC')
    results = cursor.fetchall()
    conn.close()
    return results

def get_domain_history(domain, db_path=DB_PATH):
    """Get full history for a specific domain"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, domain, checked_at, available, registered_date, 
               expiration_date, registrar, statuses, last_changed
        FROM domain_lookups
        WHERE domain = ?
        ORDER BY checked_at DESC
    ''', (domain,))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_available_domains(db_path=DB_PATH):
    """Get all domains that were found available in latest check"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get the most recent lookup for each domain where it was available
    cursor.execute('''
        SELECT domain, checked_at, registrar
        FROM domain_lookups
        WHERE available = 1
        AND id IN (
            SELECT MAX(id) FROM domain_lookups GROUP BY domain
        )
        ORDER BY checked_at DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_expiring_soon(days=90, db_path=DB_PATH):
    """Get domains expiring within specified days"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT domain, expiration_date, registrar, checked_at
        FROM domain_lookups
        WHERE available = 0
        AND expiration_date IS NOT NULL
        AND expiration_date <= date('now', '+' || ? || ' days')
        AND id IN (
            SELECT MAX(id) FROM domain_lookups GROUP BY domain
        )
        ORDER BY expiration_date ASC
        LIMIT 50
    ''', (days,))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_recent_lookups(limit=20, db_path=DB_PATH):
    """Get most recent lookups"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT domain, checked_at, available, registrar
        FROM domain_lookups
        ORDER BY checked_at DESC
        LIMIT ?
    ''', (limit,))
    results = cursor.fetchall()
    conn.close()
    return results

def print_menu():
    """Display menu options"""
    print("\n" + "="*60)
    print("Domain Lookup History Query Tool")
    print("="*60)
    print("1. List all domains")
    print("2. View domain history")
    print("3. Show available domains")
    print("4. Show domains expiring soon")
    print("5. Show recent lookups")
    print("6. Database statistics")
    print("0. Exit")
    print("="*60)

def require_db(db_path):
    """Exit if the lookup database has not been created yet."""
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        print("Run rdap_bootstrap.py first to create lookup history.")
        sys.exit(1)

def show_all_domains(db_path=DB_PATH):
    domains = get_all_domains(db_path)
    print(f"\n📋 All Domains ({len(domains)} total)")
    print(f"{'='*60}")
    for domain, count in domains:
        print(f"  {domain} ({count} lookup{'s' if count > 1 else ''})")

def show_domain_history(domain, db_path=DB_PATH):
    history = get_domain_history(domain, db_path)
    if not history:
        print(f"\n❌ No history found for {domain}")
        return
    print(f"\n📜 History for {domain} ({len(history)} lookups)")
    print(f"{'='*60}")
    for record in history:
        status = "✓ Available" if record[3] else "✗ Registered"
        print(f"\n  {record[2]} - {status}")
        if not record[3]:  # If registered
            print(f"    Registered: {record[4]}")
            print(f"    Expires: {record[5]}")
            print(f"    Registrar: {record[6]}")
            if record[7]:
                statuses = json.loads(record[7])
                print(f"    Status: {', '.join(statuses[:3])}")

def show_available(db_path=DB_PATH):
    domains = get_available_domains(db_path)
    print(f"\n✓ Available Domains ({len(domains)} total)")
    print(f"{'='*60}")
    for domain, checked, registrar in domains:
        print(f"  {domain} (checked: {checked})")

def show_expiring(days=90, db_path=DB_PATH):
    domains = get_expiring_soon(days, db_path)
    print(f"\n⚠️  Domains Expiring Soon ({len(domains)} shown)")
    print(f"{'='*60}")
    for domain, expires, registrar, checked in domains:
        print(f"  {domain}")
        print(f"    Expires: {expires}")
        print(f"    Registrar: {registrar}")
        print(f"    Last checked: {checked}\n")

def show_recent(limit=20, db_path=DB_PATH):
    lookups = get_recent_lookups(limit, db_path)
    print(f"\n🕐 Recent Lookups ({len(lookups)} shown)")
    print(f"{'='*60}")
    for domain, checked, available, registrar in lookups:
        status = "✓ Available" if available else "✗ Registered"
        reg_info = f" ({registrar})" if registrar else ""
        print(f"  {checked} - {domain} - {status}{reg_info}")

def show_statistics(db_path=DB_PATH):
    """Show database statistics"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM domain_lookups')
    total_lookups = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT domain) FROM domain_lookups')
    unique_domains = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM domain_lookups WHERE available = 1')
    available = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM domain_lookups WHERE available = 0')
    registered = cursor.fetchone()[0]
    
    cursor.execute('SELECT MIN(checked_at), MAX(checked_at) FROM domain_lookups')
    date_range = cursor.fetchone()
    
    conn.close()
    
    print(f"\n📊 Database Statistics")
    print(f"{'='*60}")
    print(f"Total lookups: {total_lookups}")
    print(f"Unique domains: {unique_domains}")
    print(f"Available: {available}")
    print(f"Registered: {registered}")
    if date_range[0]:
        print(f"First lookup: {date_range[0]}")
        print(f"Last lookup: {date_range[1]}")

def parse_args(argv=None):
    db_parent = argparse.ArgumentParser(add_help=False)
    db_parent.add_argument(
        '--db',
        default=DB_PATH,
        metavar='PATH',
        help=f'SQLite database path (default: {DB_PATH})',
    )

    parser = argparse.ArgumentParser(
        description="Query domain lookup history stored in SQLite.",
        epilog=(
            "With no command, the interactive menu is shown.\n\n"
            "Examples:\n"
            "  python3 query_history.py\n"
            "  python3 query_history.py list\n"
            "  python3 query_history.py history example.com\n"
            "  python3 query_history.py available\n"
            "  python3 query_history.py expiring --days 30\n"
            "  python3 query_history.py recent --limit 10\n"
            "  python3 query_history.py stats --db /tmp/lookups.db\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[db_parent],
    )
    subparsers = parser.add_subparsers(dest='command', metavar='COMMAND')

    subparsers.add_parser(
        'list', parents=[db_parent], help='List all domains in the database'
    )

    hist = subparsers.add_parser(
        'history', parents=[db_parent], help='Show lookup history for a domain'
    )
    hist.add_argument('domain', help='Domain name (e.g. example.com)')

    subparsers.add_parser(
        'available', parents=[db_parent], help='Show domains available at last check'
    )

    exp = subparsers.add_parser(
        'expiring', parents=[db_parent], help='Show domains expiring soon'
    )
    exp.add_argument(
        '--days',
        type=int,
        default=90,
        help='Look-ahead window in days (default: 90)',
    )

    rec = subparsers.add_parser(
        'recent', parents=[db_parent], help='Show most recent lookups'
    )
    rec.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Number of lookups to show (default: 20)',
    )

    subparsers.add_parser(
        'stats', parents=[db_parent], help='Show database statistics'
    )

    return parser.parse_args(argv)

def run_command(args):
    if args.command == 'list':
        show_all_domains(args.db)
    elif args.command == 'history':
        domain = args.domain.strip()
        if not domain:
            print("Invalid domain name.")
            sys.exit(1)
        show_domain_history(domain, args.db)
    elif args.command == 'available':
        show_available(args.db)
    elif args.command == 'expiring':
        if args.days < 0:
            print("Invalid --days: must be a non-negative integer.")
            sys.exit(1)
        show_expiring(args.days, args.db)
    elif args.command == 'recent':
        if args.limit < 1:
            print("Invalid --limit: must be a positive integer.")
            sys.exit(1)
        show_recent(args.limit, args.db)
    elif args.command == 'stats':
        show_statistics(args.db)

def interactive_menu(db_path=DB_PATH):
    """Main interactive menu"""
    while True:
        print_menu()
        choice = input("\nEnter choice: ").strip()
        
        if choice == '0':
            print("Goodbye!")
            break
        
        elif choice == '1':
            show_all_domains(db_path)
        
        elif choice == '2':
            domain = input("Enter domain name: ").strip()
            show_domain_history(domain, db_path)
        
        elif choice == '3':
            show_available(db_path)
        
        elif choice == '4':
            show_expiring(db_path=db_path)
        
        elif choice == '5':
            show_recent(db_path=db_path)
        
        elif choice == '6':
            show_statistics(db_path)
        
        else:
            print("❌ Invalid choice. Please try again.")

def main(argv=None):
    args = parse_args(argv)
    require_db(args.db)
    if args.command:
        run_command(args)
    else:
        interactive_menu(args.db)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
