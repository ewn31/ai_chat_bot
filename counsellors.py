"""Module for managing counsellors and their assignments."""
from database import db


def get_counsellors_ids():
    """Get a list of all counsellor IDs.

    Returns:
        list: A list of counsellor IDs.
    """
    return db.get_counsellors_ids()

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
    if 'name' not in counsellor or 'email' not in counsellor:
        print("Provide a valid name and email")
        return False
    
    if db.save_counsellor(counsellor):
        return True
    return False

def remove_counsellor(counsellor_id):
    """Remove a counsellor.

    Args:
        counsellor_id (str): The ID of the counsellor to remove.

    Returns:
        bool: True if the counsellor was removed successfully, False otherwise.
    """
    status = db.delete_counsellor(counsellor_id)
    if status:
        return True
    return False

def list_counsellors():
    """List all counsellors.

    Returns:
        list: A list of all counsellors.
    """
    return db.get_counsellors()

def add_channel(counsellor_id, channel, channel_id, order):
    """Adds a channel to a counsellor

    Args:
        counsellor_id (str): The ID of the counsellor to add the channel to.
        channel (str): The name of the channel.
        channel_id (str): The id used to send messages.
        order (int): The rank of the channel.
    
    Returns:
        bool: The status of the operation
    """

    return db.add_counsellor_channel(counsellor_id, channel, channel_id, order)
