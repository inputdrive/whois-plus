#!/usr/bin/env python3
"""
Query utility for domain lookup history stored in SQLite database
"""
import sqlite3
import json
from datetime import datetime
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
        AND id IN (
            SELECT MAX(id) FROM domain_lookups GROUP BY domain
        )
        ORDER BY expiration_date ASC
        LIMIT 50
    ''')
    
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

def main():
    """Main interactive menu"""
    while True:
        print_menu()
        choice = input("\nEnter choice: ").strip()
        
        if choice == '0':
            print("Goodbye!")
            break
        
        elif choice == '1':
            domains = get_all_domains()
            print(f"\n📋 All Domains ({len(domains)} total)")
            print(f"{'='*60}")
            for domain, count in domains:
                print(f"  {domain} ({count} lookup{'s' if count > 1 else ''})")
        
        elif choice == '2':
            domain = input("Enter domain name: ").strip()
            history = get_domain_history(domain)
            if not history:
                print(f"\n❌ No history found for {domain}")
            else:
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
        
        elif choice == '3':
            domains = get_available_domains()
            print(f"\n✓ Available Domains ({len(domains)} total)")
            print(f"{'='*60}")
            for domain, checked, registrar in domains:
                print(f"  {domain} (checked: {checked})")
        
        elif choice == '4':
            domains = get_expiring_soon()
            print(f"\n⚠️  Domains Expiring Soon ({len(domains)} shown)")
            print(f"{'='*60}")
            for domain, expires, registrar, checked in domains:
                print(f"  {domain}")
                print(f"    Expires: {expires}")
                print(f"    Registrar: {registrar}")
                print(f"    Last checked: {checked}\n")
        
        elif choice == '5':
            lookups = get_recent_lookups()
            print(f"\n🕐 Recent Lookups ({len(lookups)} shown)")
            print(f"{'='*60}")
            for domain, checked, available, registrar in lookups:
                status = "✓ Available" if available else "✗ Registered"
                reg_info = f" ({registrar})" if registrar else ""
                print(f"  {checked} - {domain} - {status}{reg_info}")
        
        elif choice == '6':
            show_statistics()
        
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
        sys.exit(0)
