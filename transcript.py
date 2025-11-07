import messages


def generate_transcript(user_id):
    """Generate a transcript of the conversation history for a specific user.

    Args:
        user_id (str): The user's unique identifier.
    """
    conversation_history = messages.get_messages(user_id, limit=100)
    transcript = "<br>".join([f"<em>{msg['_from']}</em>: {msg['content']}" for msg in conversation_history])
    return transcript
