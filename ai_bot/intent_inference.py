
"""
intent_inference.py - Intent Classification Module

A machine learning-based intent detection system for chatbots that classifies
user messages into predefined intent categories using a pre-trained scikit-learn model.

This module provides real-time intent classification capabilities to help chatbots
understand user intentions and route conversations appropriately.

Key Features:
- Pre-trained intent classification model using scikit-learn
- TF-IDF vectorization for text feature extraction
- Confidence scoring for classification results
- Fast inference optimized for real-time chatbot interactions
- Automatic model loading on module import

Main Functions:
- detect_intent(): Classifies user message and returns intent with confidence

Model Components:
- intent_classifier.joblib: Pre-trained classification model
- intent_vectorizer.joblib: TF-IDF vectorizer for text preprocessing

Usage:
    from intent_inference import detect_intent
    
    # Classify a user message
    intent, confidence = detect_intent("I want to speak to a human")
    
    # Use results for routing
    if intent == "escalate" and confidence > 0.7:
        # Route to human agent
        pass

Dependencies:
- joblib: For loading pre-trained models
- scikit-learn: Required by the loaded models (implicit)

Author: Generated for local-llm-test-viac-bot project
"""

import joblib
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Load model and vectorizer only once on module import
clf = joblib.load(os.path.join(script_dir, "intent_classifier.joblib"))
vectorizer = joblib.load(os.path.join(script_dir, "intent_vectorizer.joblib"))

def detect_intent(user_message):
    """
    Predict intent label and confidence for a user message using the pre-trained model.
    
    This function takes a user's text input, vectorizes it using the loaded TF-IDF
    vectorizer, and classifies it using the pre-trained intent classification model.
    
    Args:
        user_message (str): The user's input message to classify
        
    Returns:
        tuple: A tuple containing:
            - predicted_intent (str): The predicted intent label
            - confidence (float): Confidence score (0.0 to 1.0) for the prediction
            
    Example:
        >>> intent, conf = detect_intent("I need help from a human")
        >>> print(f"Intent: {intent}, Confidence: {conf:.2f}")
        Intent: escalate, Confidence: 0.85
        
    Note:
        Higher confidence scores indicate more certain predictions. Consider using
        a confidence threshold (e.g., 0.7) for decision making in your chatbot logic.
    """
    x_new = vectorizer.transform([user_message])
    probs = clf.predict_proba(x_new)[0]
    best_idx = probs.argmax()
    predicted_intent = clf.classes_[best_idx]
    confidence = probs[best_idx]
    return predicted_intent, confidence
