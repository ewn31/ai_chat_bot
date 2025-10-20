
"""
summerizer.py - Conversation Summarization Module

A utility module for intelligent conversation history management in chatbots.
Provides extractive summarization to handle long conversations while preserving
context and managing token limits for LLM interactions.

Key Features:
- Extractive text summarization using NLTK
- Automatic conversation history management
- Token limit estimation and management
- Flexible input formats (strings or tuples)
- Integration-friendly for existing database systems

Main Functions:
- summarize_conversation(): Summarizes older messages while keeping recent ones
- prepare_context_for_llm(): Manages token limits automatically
- summarize_history(): Core extractive summarization function

Usage:
    from summerizer import summarize_conversation, prepare_context_for_llm
    
    # Get messages from your database
    messages = [("User", "Hello"), ("Bot", "Hi there!")]
    
    # Summarize for LLM context
    context = summarize_conversation(messages, max_recent=5)
    
    # Or with automatic token management
    context = prepare_context_for_llm(messages, max_tokens_estimate=2000)

Dependencies:
- nltk: For sentence tokenization and text processing

Author: Generated for local-llm-test-viac-bot project
"""

import nltk
from nltk.tokenize import sent_tokenize

# Ensure punkt tokenizer is available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def summarize_conversation(messages, max_recent=5, max_summary_sentences=5):
    """
    Summarize a list of conversation messages, keeping recent ones full and summarizing older ones.
    
    Args:
        messages (list): List of message strings or tuples (speaker, message)
        max_recent (int): Number of recent messages to keep in full
        max_summary_sentences (int): Maximum sentences in the summary
    
    Returns:
        str: Formatted context with summary + recent messages
    """
    if not messages:
        return ""
    
    # Handle different message formats
    if isinstance(messages[0], tuple):
        # Format: [(speaker, message), ...]
        formatted_messages = [f"{speaker}: {message}" for speaker, message in messages]
    else:
        # Format: [message1, message2, ...]
        formatted_messages = messages
    
    # If we have fewer messages than max_recent, return all
    if len(formatted_messages) <= max_recent:
        return "\n".join(formatted_messages)
    
    # Split into older (to summarize) and recent (keep full)
    older_messages = formatted_messages[:-max_recent]
    recent_messages = formatted_messages[-max_recent:]
    
    # Summarize older messages
    summary = summarize_history(older_messages, max_summary_sentences)
    
    # Combine summary with recent messages
    context_parts = []
    if summary:
        context_parts.append(f"Previous conversation summary: {summary}")
    context_parts.extend(recent_messages)
    
    return "\n".join(context_parts)

def prepare_history_for_llm(messages, max_tokens_estimate=2000, max_recent=5):
    """
    Prepare conversation context for LLM, estimating token usage.
    
    Args:
        messages (list): List of messages
        max_tokens_estimate (int): Rough estimate of max tokens to use
        max_recent (int): Number of recent messages to keep
    
    Returns:
        str: Context string ready for LLM
    """
    # Rough estimate: 1 token ≈ 4 characters
    max_chars = max_tokens_estimate * 4
    
    # Start with default summarization
    context = summarize_conversation(messages, max_recent)
    
    # If still too long, reduce recent messages
    while len(context) > max_chars and max_recent > 2:
        max_recent -= 1
        context = summarize_conversation(messages, max_recent)
    
    return context

def summarize_history(history, max_sentences=5):
    """
    Summarize a list of conversation turns (strings) by extracting the first N sentences.
    Args:
        history (list of str): List of conversation turns.
        max_sentences (int): Maximum number of sentences in the summary.
    Returns:
        str: Summary string.
    """
    if not history:
        return ""
    all_text = " ".join(history)
    sentences = sent_tokenize(all_text)
    summary = " ".join(sentences[:max_sentences])
    return summary
class ConversationMemory:
    def __init__(self, max_full=6, max_summary_sentences=5):
        self.full_history = []  # List of (speaker, message)
        self.summary = ""
        self.max_full = max_full
        self.max_summary_sentences = max_summary_sentences

    def add_turn(self, speaker, message):
        self.full_history.append((speaker, message))
        if len(self.full_history) > self.max_full:
            # Summarize older turns
            to_summarize = [f"{s}: {m}" for s, m in self.full_history[:-self.max_full]]
            self.summary = summarize_history(to_summarize, self.max_summary_sentences)
            self.full_history = self.full_history[-self.max_full:]

    def get_context(self):
        context = self.summary + "\n" if self.summary else ""
        for speaker, message in self.full_history:
            context += f"{speaker}: {message}\n"
        return context.strip()

# Example usage with your existing database:
#
# # Get messages from your database
# messages = get_conversation_from_db(user_id)  # Your DB function
#
# # Option 1: Simple summarization
# context = summarize_conversation(messages, max_recent=5)
#
# # Option 2: With token limit estimation
# context = prepare_context_for_llm(messages, max_tokens_estimate=1500)
#
# # Use context in your LLM prompt
# prompt = f"Context:\n{context}\n\nUser: {new_question}\nBot:"
