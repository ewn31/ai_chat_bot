"""Module for managing counsellors and their assignments."""
from database import db
import argparse
import sys
import json


def get_counsellors():
    """Get a list of all counsellor IDs.

    Returns:
        list: A list of counsellor usernames.
    """
    return db.get_counsellors()

def assign_counsellor(ticket, counsellor):
    """Assign a counsellor to a user.

    Args:
        ticket (str): The ticket to assign the counsellor to.
        counsellor (str): The counsellor to assign.

    Returns:
        bool: True if the assignment was successful, False otherwise.
    """
    db.assign_ticket_handler(ticket, counsellor)
    return True

def get_assigned_counsellor(ticket):
    """Get the counsellor assigned to a ticket.

    Args:
        ticket (str): The ticket to get the assigned counsellor for.

    Returns:
        str: The ID of the assigned counsellor, or None if no counsellor is assigned.
    """
    ticket_data = db.get_ticket(ticket)
    if ticket_data:
        return ticket_data['handler'] if 'handler' in ticket_data.keys() else None
    return None

def add_counsellor(counsellor):
    """Add a new counsellor.

    Args:
        counsellor (dict): The counsellor to add.

    Returns:
        bool: True if the counsellor was added successfully, False otherwise.
    """
    if 'username' not in counsellor or 'email' not in counsellor:
        print("Provide a valid username and email")
        return False
    
    if db.save_counsellor(counsellor):
        return True
    return False

def list_counsellors():
    """List all counsellors.

    Returns:
        list: A list of all counsellors.
    """
    return db.get_counsellors()

def add_channel(counsellor, channel, channel_id, auth_key=None, order=None):
    """Adds a channel to a counsellor

    Args:
        counsellor (str): The username of the counsellor to add the channel to.
        channel (str): The name of the channel.
        channel_id (str): The id used to send messages.
        auth_key(str): The authorisation key for the channel
        order (int): The rank of the channel.
    
    Returns:
        bool: The status of the operation
    """

    return db.add_counsellor_channel(counsellor, channel, channel_id, auth_key, order)

def get_token(counsellor, channel):
    """Gets a counsellor auth token for a channel

    Args:
        counsellor (str): the username of the counsellor
        channel (str): channel name
        
    Returns:
        auth_token (str)
    """
    return db.get_counsellor_token(counsellor, channel)

def update_counsellor_channel(counsellor, channel, field, data):
    """Updates a counsellor channel information

    Args:
        counsellor (str): the username of the counsellor
        channel (str): channel name
        field (str): the field to update
        data (str): the new data
        
    Returns:
        bool: The status of the operation
    """
    return db.update_counsellor_channel(counsellor, channel, field, data)

def remove_counsellor_channel(counsellor, channel):
    """Removes a counsellor channel

    Args:
        counsellor (str): the username of the counsellor
        channel (str): channel name
        
    Returns:
        bool: The status of the operation
    """
    return db.delete_counsellor_channel(counsellor, channel)

def remove_all_counsellor_channels(counsellor):
    """Removes all counsellor channels

    Args:
        counsellor (str): the username of the counsellor
        
    Returns:
        bool: The status of the operation
    """
    return db.delete_all_counsellor_channels(counsellor)

def remove_counsellor(counsellor):
    """Remove a counsellor.

    Args:
        counsellor (str): The username of the counsellor to remove.

    Returns:
        bool: True if the counsellor was removed successfully, False otherwise.
    """
    status_deleted = db.delete_counsellor(counsellor)
    status_channels_deleted = db.delete_all_counsellor_channels(counsellor)
    status = status_deleted and status_channels_deleted
    if status:
        return True
    return False


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def cli_list_counsellors(args):
    """CLI handler for listing counsellors."""
    counsellors = list_counsellors()
    
    if not counsellors:
        print("No counsellors found.")
        return
    
    if args.json:
        # Get detailed info for JSON output
        details = db.get_counsellors_details()
        counsellors_list = []
        for c in details:
            counsellors_list.append({
                'id': c[0],
                'name': c[1],
                'username': c[2],
                'password': c[3],
                'email': c[4],
                'phone': c[5],
                'specialization': c[6],
                'current_ticket': c[7]
            })
        print(json.dumps(counsellors_list, indent=2))
    else:
        print(f"\nFound {len(counsellors)} counsellor(s):")
        print("-" * 50)
        details = db.get_counsellors_details()
        for c in details:
            print(f"Username: {c[2]}")
            print(f"  Name: {c[1] if c[1] else 'N/A'}")
            print(f"  Email: {c[4] if c[4] else 'N/A'}")
            print(f"  Phone: {c[5] if c[5] else 'N/A'}")
            print(f"  Current Ticket: {c[7] if c[7] else 'None'}")
            print()


def cli_add_counsellor(args):
    """CLI handler for adding a counsellor."""
    counsellor = {
        'username': args.username,
        'email': args.email,
        'name': args.name if args.name else args.username,
        'password': args.password if args.password else 'changeme123'
    }
    
    if args.phone:
        counsellor['phone'] = args.phone
    
    if add_counsellor(counsellor):
        print(f"✅ Counsellor '{args.username}' added successfully!")
        if not args.password:
            print("⚠️  Default password 'changeme123' was set. Please change it.")
    else:
        print(f"❌ Failed to add counsellor '{args.username}'")
        sys.exit(1)


def cli_remove_counsellor(args):
    """CLI handler for removing a counsellor."""
    if not args.force:
        response = input(f"Are you sure you want to remove counsellor '{args.username}'? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Operation cancelled.")
            return
    
    if remove_counsellor(args.username):
        print(f"✅ Counsellor '{args.username}' removed successfully!")
    else:
        print(f"❌ Failed to remove counsellor '{args.username}'")
        sys.exit(1)


def cli_add_channel(args):
    """CLI handler for adding a channel to a counsellor."""
    if add_channel(args.username, args.channel, args.channel_id, args.auth_key, args.order):
        print(f"✅ Channel '{args.channel}' added to counsellor '{args.username}'!")
    else:
        print(f"❌ Failed to add channel '{args.channel}' to counsellor '{args.username}'")
        sys.exit(1)


def cli_remove_channel(args):
    """CLI handler for removing a channel from a counsellor."""
    if remove_counsellor_channel(args.username, args.channel):
        print(f"✅ Channel '{args.channel}' removed from counsellor '{args.username}'!")
    else:
        print(f"❌ Failed to remove channel '{args.channel}' from counsellor '{args.username}'")
        sys.exit(1)


def cli_get_token(args):
    """CLI handler for getting a counsellor's channel token."""
    token = get_token(args.username, args.channel)
    
    if token:
        if args.json:
            print(json.dumps({'username': args.username, 'channel': args.channel, 'token': token}))
        else:
            print(f"Token for {args.username} on {args.channel}: {token}")
    else:
        print(f"❌ No token found for {args.username} on {args.channel}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Counsellor Management CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all counsellors
  python counsellors.py list
  
  # Add a new counsellor
  python counsellors.py add --username alice --email alice@example.com --name "Alice Smith"
  
  # Remove a counsellor
  python counsellors.py remove --username alice
  
  # Add a channel to a counsellor
  python counsellors.py add-channel --username alice --channel whatsapp --channel-id 237612345678
  
  # Get channel token
  python counsellors.py get-token --username alice --channel whatsapp
        """
    )
    
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all counsellors')
    list_parser.set_defaults(func=cli_list_counsellors)
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new counsellor')
    add_parser.add_argument('--username', required=True, help='Counsellor username')
    add_parser.add_argument('--email', required=True, help='Counsellor email')
    add_parser.add_argument('--name', help='Counsellor full name (defaults to username)')
    add_parser.add_argument('--password', help='Counsellor password (defaults to "changeme123")')
    add_parser.add_argument('--phone', help='Counsellor phone number')
    add_parser.set_defaults(func=cli_add_counsellor)
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a counsellor')
    remove_parser.add_argument('--username', required=True, help='Counsellor username')
    remove_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    remove_parser.set_defaults(func=cli_remove_counsellor)
    
    # Add channel command
    add_channel_parser = subparsers.add_parser('add-channel', help='Add a channel to a counsellor')
    add_channel_parser.add_argument('--username', required=True, help='Counsellor username')
    add_channel_parser.add_argument('--channel', required=True, help='Channel name (e.g., whatsapp, email)')
    add_channel_parser.add_argument('--channel-id', required=True, help='Channel ID for sending messages')
    add_channel_parser.add_argument('--auth-key', help='Authorization key for the channel')
    add_channel_parser.add_argument('--order', type=int, help='Channel priority order')
    add_channel_parser.set_defaults(func=cli_add_channel)
    
    # Remove channel command
    remove_channel_parser = subparsers.add_parser('remove-channel', help='Remove a channel from a counsellor')
    remove_channel_parser.add_argument('--username', required=True, help='Counsellor username')
    remove_channel_parser.add_argument('--channel', required=True, help='Channel name')
    remove_channel_parser.set_defaults(func=cli_remove_channel)
    
    # Get token command
    get_token_parser = subparsers.add_parser('get-token', help='Get channel authentication token')
    get_token_parser.add_argument('--username', required=True, help='Counsellor username')
    get_token_parser.add_argument('--channel', required=True, help='Channel name')
    get_token_parser.set_defaults(func=cli_get_token)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute the command
    args.func(args)


if __name__ == "__main__":
    main()
