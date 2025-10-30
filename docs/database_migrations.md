# Database Migration System

This document explains how to use the database migration system to safely update your database schema over time.

## Overview

The migration system allows you to:
- ✅ Track schema changes with version numbers
- ✅ Apply updates incrementally without data loss
- ✅ Prevent duplicate migrations from being applied
- ✅ See migration history and status
- ✅ Keep schema changes in version control

## Quick Start

### Check Current Status

```bash
python migrate.py status
```

This shows:
- Current database version
- Applied migrations
- Pending migrations

### Apply Migrations

```bash
python migrate.py apply
```

This applies all pending migrations to bring your database up to date.

### Check Version

```bash
python migrate.py version
```

Shows the current database schema version number.

### View History

```bash
python migrate.py history
```

Shows all migrations that have been applied, with timestamps.

## How It Works

### Migration Tracking

The system creates a `schema_migrations` table in your database:

```sql
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
)
```

Each time a migration is applied, a record is inserted here to prevent re-application.

### Migration Files

Migrations are defined in `database/updates.py` in the `MIGRATIONS` list:

```python
MIGRATIONS = [
    {
        'version': 1,
        'description': 'Add language preference to users table',
        'sql': [
            "ALTER TABLE users ADD COLUMN language VARCHAR(10) DEFAULT 'en'"
        ]
    },
    # More migrations...
]
```

## Creating New Migrations

### Step 1: Edit `database/updates.py`

Add a new migration to the `MIGRATIONS` list at the bottom:

```python
MIGRATIONS = [
    # ... existing migrations ...
    
    {
        'version': 5,  # Increment from the last version
        'description': 'Add email_verified column to users',
        'sql': [
            "ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0"
        ]
    },
]
```

### Step 2: Test the Migration

```bash
# Check status first
python migrate.py status

# Apply the migration
python migrate.py apply
```

### Step 3: Verify Success

```bash
# Check version was incremented
python migrate.py version

# View history
python migrate.py history
```

## Migration Examples

### Example 1: Add a Column

```python
{
    'version': 1,
    'description': 'Add phone_verified column to users',
    'sql': [
        "ALTER TABLE users ADD COLUMN phone_verified BOOLEAN DEFAULT 0"
    ]
}
```

### Example 2: Create a New Table

```python
{
    'version': 2,
    'description': 'Create user_sessions table',
    'sql': [
        """CREATE TABLE user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT REFERENCES users(id),
            session_token VARCHAR(255) UNIQUE,
            expires_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )"""
    ]
}
```

### Example 3: Add an Index

```python
{
    'version': 3,
    'description': 'Add index on messages timestamp',
    'sql': [
        "CREATE INDEX idx_messages_timestamp ON messages(timestamp DESC)"
    ]
}
```

### Example 4: Update Existing Data

```python
{
    'version': 4,
    'description': 'Set default handler for existing users',
    'sql': [
        "UPDATE users SET handler = 'ai_bot' WHERE handler IS NULL OR handler = ''"
    ]
}
```

### Example 5: Multiple SQL Statements

```python
{
    'version': 5,
    'description': 'Add user preferences and default values',
    'sql': [
        "ALTER TABLE users ADD COLUMN timezone VARCHAR(50) DEFAULT 'UTC'",
        "ALTER TABLE users ADD COLUMN notification_enabled BOOLEAN DEFAULT 1",
        "UPDATE users SET notification_enabled = 1 WHERE notification_enabled IS NULL"
    ]
}
```

### Example 6: Create a Junction Table

```python
{
    'version': 6,
    'description': 'Create user_tags junction table for many-to-many relationship',
    'sql': [
        """CREATE TABLE user_tags (
            user_id TEXT REFERENCES users(id),
            tag VARCHAR(50),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, tag)
        )""",
        "CREATE INDEX idx_user_tags_tag ON user_tags(tag)"
    ]
}
```

## SQLite Limitations

⚠️ **Important**: SQLite has some limitations compared to other databases:

### Cannot Do:
- `DROP COLUMN` - Cannot remove columns
- `ALTER COLUMN` type - Cannot change column types
- Add foreign key constraints to existing tables

### Workarounds:

**To remove a column** (requires recreating the table):

```python
{
    'version': 7,
    'description': 'Remove deprecated column from users',
    'sql': [
        # Create new table without the column
        """CREATE TABLE users_new (
            id PRIMARY KEY,
            gender VARCHAR(20),
            age_range VARCHAR(20),
            handler VARCHAR(100)
            -- old_column removed
        )""",
        
        # Copy data
        "INSERT INTO users_new SELECT id, gender, age_range, handler FROM users",
        
        # Drop old table
        "DROP TABLE users",
        
        # Rename new table
        "ALTER TABLE users_new RENAME TO users"
    ]
}
```

**To change column type** (same approach - recreate table):

```python
{
    'version': 8,
    'description': 'Change age_range to integer type',
    'sql': [
        """CREATE TABLE users_new (
            id PRIMARY KEY,
            gender VARCHAR(20),
            age_range INTEGER,  -- Changed from VARCHAR
            handler VARCHAR(100)
        )""",
        "INSERT INTO users_new SELECT id, gender, CAST(age_range AS INTEGER), handler FROM users",
        "DROP TABLE users",
        "ALTER TABLE users_new RENAME TO users"
    ]
}
```

## Best Practices

### 1. Always Test Migrations

Test on a copy of your database first:

```bash
# Backup your database
cp chatbot.db chatbot_backup.db

# Test the migration
python migrate.py apply

# If it fails, restore from backup
mv chatbot_backup.db chatbot.db
```

### 2. Sequential Version Numbers

Always increment version numbers sequentially:
- ✅ Good: 1, 2, 3, 4, 5
- ❌ Bad: 1, 3, 5, 10, 15

### 3. One Purpose Per Migration

Keep migrations focused on one logical change:
- ✅ Good: One migration adds user preferences
- ❌ Bad: One migration adds preferences, creates tags table, and updates old data

### 4. Descriptive Descriptions

Write clear descriptions that explain what the migration does:
- ✅ Good: "Add email_verified column to track email verification status"
- ❌ Bad: "Update users"

### 5. Test Data Migrations

If your migration updates existing data, test it thoroughly:

```python
{
    'version': 10,
    'description': 'Normalize user gender values',
    'sql': [
        # Be explicit about transformations
        "UPDATE users SET gender = 'male' WHERE LOWER(gender) IN ('m', 'man', 'male')",
        "UPDATE users SET gender = 'female' WHERE LOWER(gender) IN ('f', 'woman', 'female')",
        "UPDATE users SET gender = 'other' WHERE gender NOT IN ('male', 'female', 'other')"
    ]
}
```

### 6. Add Indexes for Performance

Create indexes on frequently queried columns:

```python
{
    'version': 11,
    'description': 'Add performance indexes',
    'sql': [
        "CREATE INDEX idx_messages_user_timestamp ON messages(_from, timestamp)",
        "CREATE INDEX idx_tickets_status ON tickets(status)",
        "CREATE INDEX idx_tickets_user ON tickets(user)"
    ]
}
```

## Integration with Application

### Automatic Migrations on Startup

Migrations are automatically applied when you run `init_db()`:

```python
from database.db import init_db

# This will create tables AND apply pending migrations
init_db()
```

### Manual Migration Check

You can also check and apply migrations manually in your code:

```python
from database.updates import apply_all_migrations, get_current_version

# Check version
version = get_current_version()
print(f"Current database version: {version}")

# Apply migrations
apply_all_migrations()
```

## Troubleshooting

### Migration Fails

If a migration fails:

1. **Check the error message** - it will tell you what went wrong
2. **The migration is NOT recorded** - it won't be marked as applied
3. **Fix the SQL** - update the migration in `updates.py`
4. **Try again** - run `python migrate.py apply` again

### Reset Migration Tracking

If you need to reset (⚠️ use with caution):

```python
# In Python console or script
from database.db import connect_db, close_db

conn = connect_db()
cur = conn.cursor()
cur.execute("DROP TABLE schema_migrations")
conn.commit()
close_db(conn)
```

Then run migrations again:

```bash
python migrate.py apply
```

### Check Which Migrations Were Applied

```bash
python migrate.py history
```

This shows all applied migrations with timestamps.

## Command Reference

```bash
# Show migration status (default)
python migrate.py
python migrate.py status

# Apply all pending migrations
python migrate.py apply

# Show current version
python migrate.py version

# Show migration history
python migrate.py history

# Show help
python migrate.py help
```

## Example Workflow

Here's a typical workflow for adding a new feature that requires schema changes:

```bash
# 1. Check current state
python migrate.py status

# 2. Edit database/updates.py - add new migration
# (see examples above)

# 3. Test on a backup
cp chatbot.db chatbot_backup.db
python migrate.py apply

# 4. If successful, commit to version control
git add database/updates.py
git commit -m "Add user_preferences table migration"

# 5. On production, just run:
python migrate.py apply
```

## Notes

- ✅ Migrations are applied in order by version number
- ✅ Each migration runs in a transaction (all or nothing)
- ✅ Failed migrations don't get recorded
- ✅ You can run `apply` multiple times safely
- ⚠️ No automatic rollback - backup your database first
- ⚠️ Be careful with data-changing migrations on production

## Support

If you encounter issues:
1. Check the logs in `chatbot_log.log`
2. Run `python migrate.py status` to see what's pending
3. Review the migration SQL for syntax errors
4. Test on a database backup first
