
"""
Support Ticket Management Module

This module provides functionality for managing support tickets in the AI chat bot system.
It handles the creation, retrieval, and management of support tickets that are used to
escalate user issues to human counsellors when the AI bot cannot provide adequate assistance.

The module integrates with the transcript system to include conversation history in tickets
and uses the database module for persistent storage of ticket information.

Functions:
    create_ticket(user): Create a new support ticket for a user
    get_ticket(ticket_id): Retrieve ticket details by ID
    close_ticket(ticket_id): Close an existing ticket
    list_open_tickets(): Get all open tickets
    list_all_tickets(): Get all tickets (all statuses)

Ticket ID Format:
    Tickets are assigned IDs in the format "00T{user_id}" for easy identification.

Dependencies:
    transcript: For generating conversation transcripts
    db: Database module for ticket persistence
"""

from database import db
import transcript

def create_ticket(user):
    """Create a support ticket for escalating user issues to a counsellor.

    Args:
        user (str): The user ID for whom to create the ticket.

    Returns:
        str or None: The created ticket ID in format "00T{user_id}", 
                    or None if creation failed.
    """
    ts = transcript.generate_transcript(user)
    ticket_id = f"00T{user}"
    try:
        db.create_ticket(user, ticket_id, transcript=ts)
        return ticket_id
    except Exception as e:
        print(f"Error creating ticket: {e}")
        return None

def get_ticket(ticket_id):
    """Retrieve a support ticket by its ID.

    Args:
        ticket_id (str): The unique ticket identifier.

    Returns:
        tuple or None: The ticket details as a database row tuple,
                      or None if ticket not found.
    """
    return db.get_ticket(ticket_id)

def close_ticket(ticket_id):
    """Close a support ticket by updating its status to 'closed'.

    Args:
        ticket_id (str): The unique ticket identifier.

    Returns:
        bool: True if the ticket was closed successfully, False otherwise.
    """
    return db.update_ticket_status(ticket_id, "closed")

def list_open_tickets():
    """List all support tickets with 'open' status.

    Returns:
        list: A list of tuples containing open ticket data,
             empty list if no open tickets found.
    """
    return db.get_open_tickets()

def list_all_tickets():
    """List all support tickets regardless of status.
    
    Note: This function calls db.get_tickets() which may not exist.
    Consider implementing this in the db module if needed.

    Returns:
        list: A list of tuples containing all ticket data,
             empty list if no tickets found.
    """
    return db.get_tickets()

def assign_handler(ticket_id, handler):
    """Assign a counsellor handler to a support ticket.

    Args:
        ticket_id (str): The unique ticket identifier.
        handler (str): The counsellor's identifier to assign.

    Returns:
        bool: True if the handler was assigned successfully, False otherwise.
    """
    return db.assign_ticket_handler(ticket_id, handler)

