# System Metadata Usage Guide

The `system_metadata` table provides a centralized way to store and manage system configuration, statistics, and health data.

## Table Structure

The table has three main categories:
- **config**: Editable system configuration values
- **stats**: Non-editable statistics (auto-updated)
- **health**: Non-editable health monitoring data

## Available Functions

### 1. Get Configuration Value
```python
import database.db as db

# Get a config value (returns typed value)
maintenance_mode = db.get_system_config('maintenance_mode')  # Returns: False (bool)
max_tickets = db.get_system_config('max_concurrent_tickets')  # Returns: 10 (int)
ai_model = db.get_system_config('ai_model_version')  # Returns: 'llama-3.1-70b' (str)

# Get from different category
db_version = db.get_system_config('db_version', category='health')  # Returns: 6 (int)
```

### 2. Set Configuration Value
```python
# Set a config value (only works for editable values)
db.set_system_config('max_concurrent_tickets', 15)  # ✓ Success
db.set_system_config('maintenance_mode', True)  # ✓ Success

# Try to set non-editable value (fails silently)
db.set_system_config('total_users', 999, category='stats')  # ✗ Fails (not editable)
```

### 3. Get All Configurations
```python
# Get all configs organized by category
all_configs = db.get_all_system_configs()
# Returns:
# {
#   'config': {
#     'maintenance_mode': {'value': False, 'data_type': 'bool', ...},
#     'max_concurrent_tickets': {'value': 10, 'data_type': 'int', ...}
#   },
#   'stats': {...},
#   'health': {...}
# }

# Get configs for specific category only
config_values = db.get_all_system_configs(category='config')
stats_values = db.get_all_system_configs(category='stats')
```

### 4. Update System Statistics
```python
# Automatically count and update statistics
db.update_system_stats()

# This updates:
# - stats.total_users (from users table count)
# - stats.total_messages (from messages table count)
# - stats.active_tickets (from open tickets count)
```

## Current Configuration Values

### Config (Editable)
| Key | Default | Type | Description |
|-----|---------|------|-------------|
| `maintenance_mode` | `false` | bool | System maintenance status |
| `max_concurrent_tickets` | `5` | int | Max tickets per counsellor |
| `ai_model_version` | `llama-3.1-70b` | string | Current AI model in use |
| `default_language` | `en` | string | Default system language |

### Stats (Auto-Updated)
| Key | Description |
|-----|-------------|
| `total_users` | Total registered users |
| `total_messages` | Total messages processed |
| `active_tickets` | Currently open tickets |

### Health (System Info)
| Key | Description |
|-----|-------------|
| `db_version` | Current database schema version |
| `last_backup` | Last database backup timestamp |

## Usage Examples

### Example 1: Check if system is in maintenance mode
```python
import database.db as db

if db.get_system_config('maintenance_mode'):
    print("System is under maintenance")
    # Return maintenance message to users
else:
    # Normal operation
    pass
```

### Example 2: Enforce ticket limits
```python
import database.db as db

max_tickets = db.get_system_config('max_concurrent_tickets')
current_tickets = len(get_counsellor_tickets(counsellor_id))

if current_tickets >= max_tickets:
    print(f"Counsellor has reached maximum ticket limit ({max_tickets})")
    # Assign to different counsellor
```

### Example 3: Dashboard statistics
```python
import database.db as db

# Update stats first
db.update_system_stats()

# Get all stats
stats = db.get_all_system_configs(category='stats')

print(f"Total Users: {stats['stats']['total_users']['value']}")
print(f"Total Messages: {stats['stats']['total_messages']['value']}")
print(f"Active Tickets: {stats['stats']['active_tickets']['value']}")
```

### Example 4: Dynamic AI model selection
```python
import database.db as db

# Admin can change the model without code changes
current_model = db.get_system_config('ai_model_version')
print(f"Using AI model: {current_model}")

# Switch to different model
db.set_system_config('ai_model_version', 'llama-3.3-70b')
```

## Adding New Configuration Values

To add new configuration values, create a new migration:

```python
{
    'version': 7,
    'description': 'Add new config values',
    'sql': [
        """INSERT INTO system_metadata (category, key, value, data_type, description, is_editable) VALUES
            ('config', 'session_timeout', '3600', 'int', 'Session timeout in seconds', 1),
            ('config', 'enable_notifications', 'true', 'bool', 'Enable push notifications', 1)
        """
    ]
}
```

## Best Practices

1. **Use typed values**: The functions automatically convert values to correct types (int, bool, string)
2. **Update stats periodically**: Call `update_system_stats()` after bulk operations or on a schedule
3. **Don't hardcode configs**: Use `get_system_config()` instead of hardcoded values
4. **Mark properly**: Set `is_editable=1` only for values that should be changeable
5. **Document changes**: Add description for all new metadata entries

## Testing

Run the test script to verify functionality:
```bash
python test_system_metadata.py
```
