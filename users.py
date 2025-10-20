
"""
User Management Module

This module provides high-level user management functionality for the AI chat bot.
It acts as a wrapper around the database operations, adding validation and 
business logic for user-related operations.

Functions:
    get_user_profile(user): Retrieve user profile information
    create_user(user): Create a new user
    update_user_handler(user, handler): Update user's handler assignment
    delete_user_profile(user): Delete a user's profile
    get_all_users(): Retrieve all users
    get_user_count(): Get total number of users
    update_user(user, field, data): Update specific user field
    update_handler(user, handler): Update user's handler (alias function)
    
Dependencies:
    db: Database module for data persistence
"""

from database import db

def get_user_profile(user):
    """Get the user's profile information.

    Args:
        user (str): The user's unique identifier.

    Returns:
        dict: The user's profile information or None if not found.
    """
    if db.user_exist(user):
        return db.get_user_profile(user)
    return None

def create_user(user):
    """Create a new user.

    Args:
        user (str): The user's unique identifier.

    Returns:
        bool: True if the user was created successfully, False otherwise.
    """
    if not db.user_exist(user):
        db.save_user(user)
        return True
    return False

def update_user_handler(user, handler):
    """Update the user's handler information.

    Args:
        user (str): The user's unique identifier.
        handler (str): The new handler information.

    Returns:
        bool: True if the handler was updated successfully, False otherwise.
    """
    if db.user_exist(user):
        db.update_user_handler(user, handler)
        return True
    return False

def delete_user_profile(user):
    """Delete the user's profile information.

    Args:
        user (str): The user's unique identifier.

    Returns:
        bool: True if the profile was deleted successfully, False otherwise.
    """
    if db.user_exist(user):
        db.delete_user_profile(user)
        return True
    return False

def get_all_users():
    """Get a list of all users.

    Returns:
        list: A list of all users or an empty list if none found.
    """
    return db.get_all_users()

def get_user_count():
    """Get the total number of users.

    Returns:
        int: The total number of users or 0 if none found.
    """
    return db.get_user_count()

def update_user(user, field, data):
    """Update the user's information.

    Args:
        user (str): The user's unique identifier.
        field (str): The specific field to update.
        data (any): The new data to set for the field.

    Returns:
        bool: True if the user was updated successfully, False otherwise.
    """

    if db.user_exist(user):
        db.update_user(user, field, data)
        return True
    return False

def update_handler(user, handler):
    """Update the user's handler information.

    Args:
        user (str): The user's unique identifier.
        handler (str): The new handler information.

    Returns:
        bool: True if the handler was updated successfully, False otherwise.
    """
    if db.user_exist(user):
        db.update_user_handler(user, handler)
        return True
    return False
