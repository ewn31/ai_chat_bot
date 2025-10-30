#!/usr/bin/env python3
"""
Database Migration Management Script

This script provides a convenient command-line interface for managing
database schema migrations.

Usage:
    python migrate.py               - Show migration status
    python migrate.py apply         - Apply all pending migrations
    python migrate.py status        - Show detailed migration status
    python migrate.py version       - Show current database version
    python migrate.py history       - Show migration history

Examples:
    # Check what migrations are pending
    python migrate.py status
    
    # Apply all pending migrations
    python migrate.py apply
    
    # Check current version
    python migrate.py version
"""

import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.updates import (
    apply_all_migrations,
    show_migration_status,
    get_current_version,
    get_migration_history
)


def main():
    """Main entry point for the migration script."""
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "apply":
            print("\n🔄 Applying database migrations...\n")
            apply_all_migrations()
            
        elif command == "status":
            show_migration_status()
            
        elif command == "version":
            version = get_current_version()
            print(f"\n📊 Current database version: {version}\n")
            
        elif command == "history":
            history = get_migration_history()
            if history:
                print("\n📜 Migration History:")
                print("="*60)
                for m in history:
                    print(f"  Version {m['version']}: {m['description']}")
                    print(f"  Applied at: {m['applied_at']}")
                    print("-"*60)
            else:
                print("\n📜 No migrations applied yet.\n")
                
        elif command in ["help", "-h", "--help"]:
            print(__doc__)
            
        else:
            print(f"❌ Unknown command: {command}")
            print("\n" + "="*60)
            print("Available commands:")
            print("  apply   - Apply all pending migrations")
            print("  status  - Show migration status (default)")
            print("  version - Show current database version")
            print("  history - Show migration history")
            print("  help    - Show this help message")
            print("="*60 + "\n")
            sys.exit(1)
    else:
        # Default action: show status
        show_migration_status()


if __name__ == "__main__":
    main()
