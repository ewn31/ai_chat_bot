"""
Message Management Module

This module provides functionality for managing chat messages in the AI chat bot.
It handles saving messages to the database and retrieving message history for users.

Functions:
    save_message(message): Save a message to the database
    get_messages(user_id, limit): Retrieve messages for a specific user
    
Dependencies:
    db: Database module for data persistence
"""

from database import db

def save_message(message, user_id):
    """Save a message to the database.

    Args:
        message (dict): A dictionary containing message details.

    Returns:
        bool: True if the message was saved successfully, False otherwise.
    """
    return db.save_memory(message, user_id)

def get_messages(user_id, limit=100):
    """Get messages for a specific user.

    Args:
        user_id (str): The user's unique identifier.
        limit (int): The maximum number of messages to retrieve.

    Returns:
        list: A list of messages for the user.
    """
    messages = db.get_memory(user_id)
    return messages[-limit:] if messages else []

def delete_user_memory(user_id):
    """Delete all messages associated with a specific user.

    Args:
        user_id (str): The user's unique identifier.

    Returns:
        bool: True if the messages were deleted successfully, False otherwise.
    """
    return db.delete_memory(user_id)

def delete_message_by_id(message_id):
    """Delete a specific message by its ID.

    Args:
        message_id (int): The unique identifier of the message to delete.

    Returns:
        bool: True if the message was deleted successfully, False otherwise.
    """
    return db.delete_message(message_id)
