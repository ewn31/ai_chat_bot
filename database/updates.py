"""
Database schema update and migration utilities.

This module provides a version-controlled migration system for updating the database schema.
Migrations are applied incrementally and tracked to prevent duplicate applications.

Usage:
    from database.updates import apply_all_migrations, get_current_version
    
    # Check current version
    version = get_current_version()
    print(f"Current database version: {version}")
    
    # Apply all pending migrations
    apply_all_migrations()
"""

import sqlite3
import os
import logging
from datetime import datetime

# Configure logging
logging_level = os.getenv('LOGGING_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, logging_level, logging.INFO))


def connect_db():
    """Connect to the SQLite database."""
    conn = sqlite3.connect('chatbot.db', timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def close_db(conn):
    """Close the database connection."""
    conn.close()


def init_migration_table():
    """
    Initialize the schema_migrations table to track applied migrations.
    
    This table keeps a record of which migrations have been applied and when.
    """
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                description TEXT,
                applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        logging.info("Migration tracking table initialized")
    except Exception as e:
        logging.error(f"Error initializing migration table: {e}")
        raise
    finally:
        close_db(conn)


def get_current_version():
    """
    Get the current database schema version.
    
    Returns:
        int: The highest version number from applied migrations, or 0 if none applied.
    """
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        # Check if migration table exists
        cur.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schema_migrations'
        """)
        
        if not cur.fetchone():
            return 0
        
        # Get the highest version number
        cur.execute("SELECT MAX(version) as version FROM schema_migrations")
        result = cur.fetchone()
        return result['version'] if result['version'] is not None else 0
    except Exception as e:
        logging.error(f"Error getting current version: {e}")
        return 0
    finally:
        close_db(conn)


def migration_applied(version):
    """
    Check if a specific migration version has been applied.
    
    Args:
        version (int): Migration version number to check.
        
    Returns:
        bool: True if migration has been applied, False otherwise.
    """
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "SELECT version FROM schema_migrations WHERE version = ?",
            (version,)
        )
        return cur.fetchone() is not None
    except Exception as e:
        logging.error(f"Error checking migration status: {e}")
        return False
    finally:
        close_db(conn)


def record_migration(version, description):
    """
    Record a successfully applied migration.
    
    Args:
        version (int): Migration version number.
        description (str): Description of what the migration does.
    """
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
            (version, description)
        )
        conn.commit()
        logging.info(f"Migration {version} recorded: {description}")
    except Exception as e:
        logging.error(f"Error recording migration: {e}")
        raise
    finally:
        close_db(conn)


def apply_migration(version, description, sql_statements):
    """
    Apply a single migration to the database.
    
    Args:
        version (int): Migration version number.
        description (str): Description of the migration.
        sql_statements (list): List of SQL statements to execute.
        
    Returns:
        bool: True if migration was applied successfully, False otherwise.
    """
    if migration_applied(version):
        logging.info(f"Migration {version} already applied, skipping")
        return False
    
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        logging.info(f"Applying migration {version}: {description}")
        
        # Execute all SQL statements in the migration
        for sql in sql_statements:
            if sql.strip():  # Skip empty statements
                cur.execute(sql)
        
        # Record the migration
        cur.execute(
            "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
            (version, description)
        )
        
        conn.commit()
        logging.info(f"Migration {version} applied successfully")
        print(f"✓ Applied migration {version}: {description}")
        return True
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Error applying migration {version}: {e}")
        print(f"✗ Failed to apply migration {version}: {e}")
        raise
    finally:
        close_db(conn)


# =============================================================================
# MIGRATIONS
# =============================================================================
# Add new migrations below in sequential order.
# Each migration should have a unique version number and description.

MIGRATIONS = [
    # Migration 1: Add language preference support
    {
        'version': 1,
        'description': 'Add language preference column to users table',
        'sql': [
            "ALTER TABLE users ADD COLUMN language VARCHAR(10) DEFAULT 'en'"
        ]
    },
    
    # Migration 2: Add indexes for better query performance
    {
        'version': 2,
        'description': 'Add performance indexes on frequently queried columns',
        'sql': [
            "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)",
            "CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(user)",
            "CREATE INDEX IF NOT EXISTS idx_messages_from ON messages(_from)"
        ]
    },
    
    {
        'version': 3,
        'description': 'Add chat user authentification key for users table',
        'sql': [
            "ALTER TABLE users ADD COLUMN auth_key TEXT"
        ]
        
    },
    
    {
        'version': 4,
        'description': 'Add auth_key to channel table',
        'sql': [
            "ALTER TABLE channels ADD COLUMN auth_key TEXT"
        ]
    },
    
    # Migration 5: Modify channels table - change counsellor_id to counsellor_username and add auth_key
    {
        'version': 5,
        'description': 'Modify channels table: change counsellor_id to counsellor_username and add auth_key column',
        'sql': [
            # Create new channels table with updated schema
            """CREATE TABLE channels_new (
                counsellor_username VARCHAR(50) REFERENCES counsellors(username),
                channel VARCHAR(100),
                channel_id VARCHAR(100),
                order_priority INT,
                auth_key TEXT,
                PRIMARY KEY (counsellor_username, channel)
            )""",
            
            # Copy data from old table to new table, joining with counsellors to get username
            """INSERT INTO channels_new (counsellor_username, channel, channel_id, order_priority, auth_key)
            SELECT c.username, ch.channel, ch.channel_id, ch.order_priority, ch.auth_key
            FROM channels ch
            LEFT JOIN counsellors c ON ch.counsellor_id = c.id""",
            
            # Drop old table
            "DROP TABLE channels",
            
            # Rename new table to original name
            "ALTER TABLE channels_new RENAME TO channels"
        ]
    },
    
    # Migration 6: Create system_metadata table for centralized configuration
    {
        'version': 6,
        'description': 'Create system_metadata table for storing system configuration, statistics, and health data',
        'sql': [
            """CREATE TABLE system_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category VARCHAR(50) NOT NULL,
                key VARCHAR(100) NOT NULL,
                value TEXT,
                data_type VARCHAR(20) DEFAULT 'string',
                description TEXT,
                is_editable BOOLEAN DEFAULT 1,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(category, key)
            )""",
            
            # Insert initial system configuration values
            """INSERT INTO system_metadata (category, key, value, data_type, description, is_editable) VALUES
                ('config', 'maintenance_mode', 'false', 'bool', 'System maintenance status', 1),
                ('config', 'max_concurrent_tickets', '5', 'int', 'Maximum tickets per counsellor', 1),
                ('config', 'ai_model_version', 'llama-3.1-70b', 'string', 'Current AI model in use', 1),
                ('config', 'default_language', 'en', 'string', 'Default system language', 1),
                ('stats', 'total_users', '0', 'int', 'Total registered users', 0),
                ('stats', 'total_messages', '0', 'int', 'Total messages processed', 0),
                ('stats', 'active_tickets', '0', 'int', 'Currently open tickets', 0),
                ('health', 'db_version', '6', 'int', 'Current database schema version', 0),
                ('health', 'last_backup', '', 'string', 'Last database backup timestamp', 0)
            """
        ]
    },
    
    # Migration 7: Add chat_app_admin_api_key configuration
    {
        'version': 7,
        'description': 'Add chat_app_admin_api_key configuration for admin actions on chat app platform',
        'sql': [
            """INSERT INTO system_metadata (category, key, value, data_type, description, is_editable) VALUES
                ('config', 'chat_app_admin_api_key', '', 'string', 'Admin API key for chat app platform administrative actions', 1)
            """
        ]
    },

    # Example Migration 3: Create a new table
    # {
    #     'version': 3,
    #     'description': 'Create user_preferences table',
    #     'sql': [
    #         """CREATE TABLE user_preferences (
    #             user_id TEXT PRIMARY KEY REFERENCES users(id),
    #             theme VARCHAR(20) DEFAULT 'light',
    #             notifications_enabled BOOLEAN DEFAULT 1,
    #             created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    #         )"""
    #     ]
    # },
    
    # Example Migration 4: Modify existing data
    # {
    #     'version': 4,
    #     'description': 'Set default handler for existing users',
    #     'sql': [
    #         "UPDATE users SET handler = 'ai_bot' WHERE handler IS NULL"
    #     ]
    # },
]


def apply_all_migrations():
    """
    Apply all pending migrations to the database.
    
    Initializes the migration tracking table if it doesn't exist,
    then applies all migrations that haven't been applied yet.
    
    Returns:
        tuple: (number of migrations applied, total migrations)
    """
    # Initialize migration tracking
    init_migration_table()
    
    current_version = get_current_version()
    logging.info(f"Current database version: {current_version}")
    print(f"Current database version: {current_version}")
    
    applied_count = 0
    
    # Apply each migration in order
    for migration in MIGRATIONS:
        version = migration['version']
        description = migration['description']
        sql_statements = migration['sql']
        
        if version > current_version:
            try:
                if apply_migration(version, description, sql_statements):
                    applied_count += 1
            except Exception as e:
                print(f"\n⚠ Migration {version} failed. Stopping migration process.")
                print(f"Error: {e}")
                break
    
    if applied_count == 0:
        print("✓ Database is up to date. No migrations needed.")
    else:
        print(f"\n✓ Successfully applied {applied_count} migration(s)")
    
    new_version = get_current_version()
    print(f"Database version: {current_version} → {new_version}")
    
    return applied_count, len(MIGRATIONS)


def rollback_migration(version):
    """
    Rollback a specific migration (if rollback SQL is provided).
    
    Note: This is a placeholder. Implementing rollbacks requires storing
    rollback SQL statements for each migration, which adds complexity.
    For SQLite, some operations (like DROP COLUMN) are not supported,
    making rollbacks difficult.
    
    Args:
        version (int): Migration version to rollback.
    """
    logging.warning("Rollback functionality not implemented")
    print("⚠ Rollback functionality is not yet implemented.")
    print("Consider backing up your database before applying migrations.")


def get_migration_history():
    """
    Get the history of applied migrations.
    
    Returns:
        list: List of dictionaries containing migration history.
    """
    conn = connect_db()
    cur = conn.cursor()
    
    try:
        # Check if migration table exists
        cur.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schema_migrations'
        """)
        
        if not cur.fetchone():
            return []
        
        cur.execute("""
            SELECT version, description, applied_at 
            FROM schema_migrations 
            ORDER BY version
        """)
        
        history = []
        for row in cur.fetchall():
            history.append({
                'version': row['version'],
                'description': row['description'],
                'applied_at': row['applied_at']
            })
        
        return history
        
    except Exception as e:
        logging.error(f"Error getting migration history: {e}")
        return []
    finally:
        close_db(conn)


def show_migration_status():
    """
    Display the current migration status and pending migrations.
    """
    init_migration_table()
    
    current_version = get_current_version()
    history = get_migration_history()
    
    print("\n" + "="*60)
    print("DATABASE MIGRATION STATUS")
    print("="*60)
    print(f"Current Version: {current_version}")
    print(f"Total Migrations Available: {len(MIGRATIONS)}")
    
    if history:
        print(f"\nApplied Migrations ({len(history)}):")
        print("-"*60)
        for m in history:
            print(f"  v{m['version']}: {m['description']}")
            print(f"         Applied at: {m['applied_at']}")
    else:
        print("\nNo migrations applied yet.")
    
    pending = [m for m in MIGRATIONS if m['version'] > current_version]
    if pending:
        print(f"\nPending Migrations ({len(pending)}):")
        print("-"*60)
        for m in pending:
            print(f"  v{m['version']}: {m['description']}")
    else:
        print("\n✓ All migrations are up to date!")
    
    print("="*60 + "\n")


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "apply":
            apply_all_migrations()
        elif command == "status":
            show_migration_status()
        elif command == "version":
            version = get_current_version()
            print(f"Current database version: {version}")
        elif command == "history":
            history = get_migration_history()
            if history:
                print("\nMigration History:")
                for m in history:
                    print(f"  v{m['version']}: {m['description']} (applied: {m['applied_at']})")
            else:
                print("No migrations applied yet.")
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python updates.py apply   - Apply all pending migrations")
            print("  python updates.py status  - Show migration status")
            print("  python updates.py version - Show current version")
            print("  python updates.py history - Show migration history")
    else:
        show_migration_status()
