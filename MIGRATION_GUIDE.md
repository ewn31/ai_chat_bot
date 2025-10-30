# Database Migration Quick Reference

## Common Commands

```bash
# Check migration status
python migrate.py status

# Apply all pending migrations
python migrate.py apply

# Check current version
python migrate.py version

# View migration history
python migrate.py history
```

## Adding a New Migration

1. **Edit `database/updates.py`**
2. **Add to the `MIGRATIONS` list:**

```python
MIGRATIONS = [
    # ... existing migrations ...
    
    {
        'version': 3,  # Next version number
        'description': 'Your description here',
        'sql': [
            "YOUR SQL STATEMENT HERE"
        ]
    },
]
```

3. **Apply the migration:**

```bash
python migrate.py apply
```

## Common Migration Patterns

### Add a Column
```python
{
    'version': X,
    'description': 'Add column_name to table_name',
    'sql': [
        "ALTER TABLE table_name ADD COLUMN column_name VARCHAR(50) DEFAULT 'value'"
    ]
}
```

### Create a Table
```python
{
    'version': X,
    'description': 'Create new_table',
    'sql': [
        """CREATE TABLE new_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column1 VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    ]
}
```

### Add an Index
```python
{
    'version': X,
    'description': 'Add index on column',
    'sql': [
        "CREATE INDEX idx_table_column ON table_name(column_name)"
    ]
}
```

### Update Data
```python
{
    'version': X,
    'description': 'Update existing data',
    'sql': [
        "UPDATE table_name SET column = 'value' WHERE condition"
    ]
}
```

## Important Notes

- ✅ Always backup database before migrations
- ✅ Test migrations on a copy first
- ✅ Use sequential version numbers (1, 2, 3...)
- ✅ One logical change per migration
- ⚠️ SQLite cannot DROP COLUMN - requires table recreation
- ⚠️ Migrations run in a transaction (all or nothing)

## Troubleshooting

**Migration fails?**
- Check the error message
- Fix the SQL in `updates.py`
- Run `python migrate.py apply` again

**Need to see what's pending?**
```bash
python migrate.py status
```

**Want to see what was applied?**
```bash
python migrate.py history
```

For detailed documentation, see: `docs/database_migrations.md`
