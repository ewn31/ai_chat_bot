"""
Manage the dashboard API key.

Usage:
    python manage_api_key.py set              # Generate a random key and save it
    python manage_api_key.py set <your-key>   # Set a specific key
    python manage_api_key.py show             # Show the current key
    python manage_api_key.py delete           # Remove the key (disables API access)
"""

import sys
import secrets
import database.db as db


CONFIG_KEY = 'dashboard_api_key'


def show_key():
    key = db.get_system_config(CONFIG_KEY)
    if key:
        print(f"Current API key: {key}")
    else:
        print("No API key is set. Dashboard API access is disabled.")


def set_key(value=None):
    if value is None:
        value = secrets.token_urlsafe(32)
        print(f"Generated API key: {value}")
    else:
        print(f"Setting API key to: {value}")

    if db.set_system_config(CONFIG_KEY, value):
        print("API key saved successfully.")
    else:
        print("ERROR: Failed to save API key. Make sure migration 12 has been applied.")
        sys.exit(1)


def delete_key():
    if db.set_system_config(CONFIG_KEY, ''):
        print("API key deleted. Dashboard API access is now disabled.")
    else:
        print("ERROR: Failed to delete API key.")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == 'show':
        show_key()
    elif command == 'set':
        value = sys.argv[2] if len(sys.argv) > 2 else None
        set_key(value)
    elif command == 'delete':
        delete_key()
    else:
        print(f"Unknown command: {command}")
        print(__doc__.strip())
        sys.exit(1)


if __name__ == '__main__':
    main()
