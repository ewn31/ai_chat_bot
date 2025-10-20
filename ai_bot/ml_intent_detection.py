
"""
Machine Learning Intent Detection Module

This module provides machine learning-based intent classification for the AI chat bot.
It uses scikit-learn to train a logistic regression classifier that can identify user
intents from chat messages, specifically for healthcare/reproductive health contexts.

The module handles several intent categories:
- escalate: Messages requiring human counselor intervention
- general_question: Standard information requests
- feedback: User appreciation or satisfaction comments
- greeting: Initial user greetings and hellos
- goodbye: Conversation ending messages

The classifier uses TF-IDF vectorization for feature extraction and is specifically
trained on healthcare-related conversations, particularly reproductive health scenarios.

Functions:
    load_intent_model(): Load saved model and vectorizer from disk
    detect_intent(user_message, clf, vectorizer, threshold): Predict intent with confidence

Training Data:
    Contains labeled examples for each intent category, with emphasis on sensitive
    healthcare scenarios that require immediate escalation to human counselors.

Model Files:
    - intent_classifier.joblib: Trained logistic regression model
    - intent_vectorizer.joblib: TF-IDF vectorizer for text preprocessing

Dependencies:
    pandas: Data manipulation and analysis
    sklearn: Machine learning algorithms and utilities
    joblib: Model serialization and loading

Usage:
    # Load trained model
    clf, vectorizer = load_intent_model()
    
    # Detect intent for user message
    intent, confidence = detect_intent("I need help", clf, vectorizer)
    print(f"Intent: {intent}, Confidence: {confidence:.2f}")
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import joblib

# --- 1. Prepare your labeled data ---
# Example data: replace or expand with your real chat logs!
data = [
    # escalate
    ("I want to talk to a real person.", "escalate"),
    ("Can I speak to a human agent?", "escalate"),
    ("Not helping, I need someone!", "escalate"),
    ("This is frustrating.", "escalate"),
    ("This is urgent, escalate!", "escalate"),
    ("I want a manager.", "escalate"),
    ("Put me through to customer service.", "escalate"),
    ("Let me talk to support.", "escalate"),
    ("I need to file a complaint.", "escalate"),
    ("Can you connect me with an agent?", "escalate"),
    ("I am not satisfied with these answers.", "escalate"),
    ("Escalate this issue!", "escalate"),
    ("Your bot is not helpful.", "escalate"),
    ("It’s not working, get me a person.", "escalate"),
    ("Is there a real person I can talk to?", "escalate"),
    ("Can you escalate this ticket?", "escalate"),
    ("I am angry. Get me help.", "escalate"),
    ("I need urgent human assistance.", "escalate"),
    ("I’m getting nowhere, please escalate.", "escalate"),
    ("I want to speak to your supervisor.", "escalate"),
    ("Pls am sorry for entering you dm without you concern but pls I need your help pls I need abortion pills", "escalate"),
    ("Pls i need abortion pills", "escalate"),
    ("I am bleeding", "escalate"),
    ("Please I am still bleeding. please is that normal. Like now it was heavy and dark with some clots", "escalate"),
    ("Hi pls I need abortion pills for pregnancy about 2 to 3 weeks and how much", "escalate"),
    ("I feel pains", "escalate"),
    ("Please I need abortion pills right now, where can I get them?", "escalate"),
    ("Can someone send me meds for abortion? I can’t go to a clinic.", "escalate"),
    ("I’m 6 weeks pregnant — how do I get pills?", "escalate"),
    ("I need to terminate my pregnancy, please help me find someone.", "escalate"),
    ("Hoping you can help me access an abortion — I don’t know what to do.", "escalate"),
    ("Is there anyone who can help me get a safe abortion?", "escalate"),
    ("I don’t want to be pregnant anymore, can you refer me to someone? logistics", "escalate"),
    ("I am bleeding a lot after taking something, please help.", "escalate"),
    ("I’m passing big clots and my stomach hurts — is this normal?", "escalate"),
    ("Please, I’m still bleeding two days later and it’s heavy.", "escalate"),
    ("I fainted after bleeding, what should I do?", "escalate"),
    ("My bleeding smells bad and I have a fever.", "escalate"),
    ("I took pills and now my bleeding is very heavy with dizziness.", "escalate"),
    ("Severe abdominal pain and vomiting after trying to end my pregnancy. Please help.", "escalate"),
    ("I can’t stand up, pain is unbearable after the procedure.", "escalate"),
    ("My temperature is 39°C and I have bad pain. What do I do?", "escalate"),
    ("I’m passing tissue and feel faint — is this emergency?", "escalate"),
    ("How do I use abortion pills? Step by step please.", "escalate"),
    ("What dose should I take and when? I’m scared to do it alone.", "escalate"),
    ("If I take pills at home, when should I go to hospital?", "escalate"),
    ("I don’t know if I should take the pills now or wait.", "escalate"),
    ("I don’t have anywhere to go; I’m terrified and don’t know who to tell.", "escalate"),
    ("I feel suicidal because of this pregnancy — I need someone to talk to.", "escalate"),
    ("I’m a minor and my parents will kick me out if they find out. Please help.", "escalate"),
    ("I’m shaking and crying and don’t know what to do next.", "escalate"),
    ("I was forced into this and I need support and help getting care.", "escalate"),
    ("I took the pills but I’m still pregnant — what went wrong?", "escalate"),
    ("I still have pregnancy symptoms after medication, please advise.", "escalate"),
    ("I think something is left inside me; my pain isn’t going away.", "escalate"),
    ("Can you refer me to a nearby clinic that does abortions? logistics", "escalate"),
    ("I have no money — is there a free service or counselor who can help? logistics", "escalate"),
    ("Are there safe providers in my city? I need contact details. logistics", "escalate"),
    ("I need a female counselor who speaks my language — can you connect me? logistics", "escalate"),
    ("I’m not sure how many weeks I am, can someone check and advise?", "escalate"),
    ("I just found out I’m pregnant — is it too late for pills?", "escalate"),
    ("I messaged earlier and nothing’s changed — the bleeding has increased.", "escalate"),
    ("The pain has worsened since yesterday. I need a human to talk to.", "escalate"),
    ("Please help me, I’m bleeding and scared I’ll die.", "escalate"),
    ("I’m begging you — send help or tell me where to go.", "escalate"),
    ("I can’t reach anyone else, please connect me to a counsellor now.", "escalate"),
    ("Sorry to bother — I may need an abortion and would like to speak to someone.", "escalate"),
    ("Hi, can a real person advise me on options? Chatbot answers aren’t enough.", "escalate"),
    ("My partner forces me to keep it; I need help in secret.", "escalate"),
    ("I was assaulted and need emergency help and counseling.", "escalate"),
    ("I took meds but I don’t remember the name — I’m worried.", "escalate"),
    ("I’m dizzy, confused, and can’t walk steady. Please someone help.", "escalate"),
    ("Pls i need pills.. DM me.", "escalate"),
    ("I’ve got heavy bleed n cramps, not normal right?", "escalate"),
    ("Need help asap. 2wks preg. scared.", "escalate"),
    ("Help me please, I think the pills didn’t work and I’m still pregnant.", "escalate"),

    # general_question
    ("How do I reset my password?", "general_question"),
    ("Can you tell me my account balance?", "general_question"),
    ("How does your service work?", "general_question"),
    ("What are your working hours?", "general_question"),
    ("Can you help me update my email address?", "general_question"),
    ("Where can I find my transaction history?", "general_question"),
    ("What is the return policy?", "general_question"),
    ("How do I change my subscription?", "general_question"),
    ("Can I download my invoice?", "general_question"),
    ("How to contact technical support?", "general_question"),
    ("Do you offer discounts?", "general_question"),
    ("What are your payment options?", "general_question"),
    ("How do I close my account?", "general_question"),
    ("Is my data secure with you?", "general_question"),
    ("What is your privacy policy?", "general_question"),
    ("How can I update my profile picture?", "general_question"),
    ("Can you help me with setting up 2FA?", "general_question"),
    ("How do I change my phone number?", "general_question"),
    ("Where do I upload documents?", "general_question"),
    ("How do I delete a saved address?", "general_question"),

    # feedback
    ("Thank you, that's helpful.", "feedback"),
    ("Great service!", "feedback"),
    ("I appreciate your assistance.", "feedback"),
    ("You’ve been very helpful.", "feedback"),
    ("Thanks for the quick response.", "feedback"),
    ("Nice bot!", "feedback"),
    ("This was exactly what I needed.", "feedback"),
    ("Kudos to your support team!", "feedback"),
    ("Everything works perfectly.", "feedback"),
    ("Your service is fantastic.", "feedback"),
    ("I’m happy with this solution.", "feedback"),
    ("That solved my issue, thanks!", "feedback"),
    ("Much appreciated.", "feedback"),
    ("I’m satisfied with the support.", "feedback"),
    ("Awesome!", "feedback"),
    ("Perfect, thank you!", "feedback"),
    ("You made my day.", "feedback"),
    ("I’ll recommend this to others.", "feedback"),
    ("The instructions were clear.", "feedback"),
    ("That was easy.", "feedback"),

    # greeting
    ("Hello!", "greeting"),
    ("Hi, can you help me?", "greeting"),
    ("Good morning.", "greeting"),
    ("Hey there!", "greeting"),
    ("Hi!", "greeting"),
    ("Good afternoon!", "greeting"),
    ("Hello there.", "greeting"),
    ("Hey!", "greeting"),
    ("Good evening.", "greeting"),
    ("Greetings!", "greeting"),
    ("Hi, I need assistance.", "greeting"),
    ("Hello, support.", "greeting"),
    ("Hey, bot!", "greeting"),
    ("Hi, what's up?", "greeting"),
    ("Morning!", "greeting"),
    ("Yo!", "greeting"),
    ("Hey, I have a question.", "greeting"),
    ("Hi, anyone there?", "greeting"),
    ("Hi, can I ask something?", "greeting"),
    ("Hello, I’m here.", "greeting"),

    # goodbye
    ("Goodbye.", "goodbye"),
    ("Bye!", "goodbye"),
    ("See you later.", "goodbye"),
    ("Thanks, bye.", "goodbye"),
    ("Talk to you soon.", "goodbye"),
    ("Have a nice day.", "goodbye"),
    ("I’m done, thanks.", "goodbye"),
    ("See you.", "goodbye"),
    ("Take care.", "goodbye"),
    ("Bye bye.", "goodbye"),
    ("Thanks and goodbye.", "goodbye"),
    ("I’ll be back.", "goodbye"),
    ("Later!", "goodbye"),
    ("Farewell.", "goodbye"),
    ("Catch you later.", "goodbye"),
    ("Have a good one.", "goodbye"),
    ("I’m signing off.", "goodbye"),
    ("That’s all I need, bye.", "goodbye"),
    ("I have to go now.", "goodbye"),
    ("Peace out.", "goodbye"),
]

df = pd.DataFrame(data, columns=["message", "intent"])

# --- 2. Split into train and test sets ---
X_train, X_test, y_train, y_test = train_test_split(
    df['message'], df['intent'], test_size=0.2, random_state=42, stratify=df['intent']
)

# --- 3. Feature extraction ---
vectorizer = TfidfVectorizer()
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# --- 4. Train classifier ---
clf = LogisticRegression(max_iter=1000)
clf.fit(X_train_vec, y_train)

# --- 5. Evaluate (optional) ---
y_pred = clf.predict(X_test_vec)
print("Classification Report:\n", classification_report(y_test, y_pred))

# --- 6. Save model and vectorizer for chatbot use ---
joblib.dump(clf, "intent_classifier.joblib")
joblib.dump(vectorizer, "intent_vectorizer.joblib")

print("Model and vectorizer saved!\n")

# --- 7. Inference Function ---

def load_intent_model():
    """
    Load the trained intent classification model and vectorizer from disk.
    
    This function loads the previously saved logistic regression classifier
    and TF-IDF vectorizer that were trained on intent classification data.
    
    Returns:
        tuple: A tuple containing (classifier, vectorizer)
            - classifier (LogisticRegression): Trained intent classification model
            - vectorizer (TfidfVectorizer): Fitted TF-IDF vectorizer for text preprocessing
            
    Raises:
        FileNotFoundError: If model files are not found in the current directory
        
    Example:
        >>> clf, vectorizer = load_intent_model()
        >>> print(type(clf))
        <class 'sklearn.linear_model._logistic.LogisticRegression'>
    """
    clf = joblib.load("intent_classifier.joblib")
    vectorizer = joblib.load("intent_vectorizer.joblib")
    return clf, vectorizer

def detect_intent(user_message, clf, vectorizer, threshold=0.5):
    """
    Predict the intent of a user message using the trained classification model.
    
    This function takes a user's text message and predicts the most likely intent
    category along with a confidence score. The function uses TF-IDF vectorization
    to convert the text into features that the classifier can process.
    
    Args:
        user_message (str): The user's input message to classify
        clf (LogisticRegression): Trained intent classification model
        vectorizer (TfidfVectorizer): Fitted TF-IDF vectorizer for text preprocessing
        threshold (float, optional): Minimum confidence threshold (default: 0.5)
                                   Currently not used in implementation but available
                                   for future confidence-based filtering
    
    Returns:
        tuple: A tuple containing (predicted_intent, confidence)
            - predicted_intent (str): The predicted intent category 
              ('escalate', 'general_question', 'feedback', 'greeting', 'goodbye')
            - confidence (float): Confidence score between 0 and 1, where 1 is
              maximum confidence
    
    Example:
        >>> clf, vectorizer = load_intent_model()
        >>> intent, conf = detect_intent("I need to speak with a human", clf, vectorizer)
        >>> print(f"Intent: {intent}, Confidence: {conf:.2f}")
        Intent: escalate, Confidence: 0.85
        
    Note:
        The function currently returns the highest probability intent regardless
        of the threshold parameter. Future versions may implement threshold-based
        filtering for low-confidence predictions.
    """
    x_new = vectorizer.transform([user_message])
    probs = clf.predict_proba(x_new)[0]
    best_idx = probs.argmax()
    predicted_intent = clf.classes_[best_idx]
    confidence = probs[best_idx]
    return predicted_intent, confidence

# --- 8. Example Usage in Chatbot ---

if __name__ == "__main__":
    # Load model & vectorizer
    clf, vectorizer = load_intent_model()

    # Test messages
    test_messages = [
        "Can I get a human agent?",
        "Thank you so much!",
        "Bye for now.",
        "Why doesn't this work?",
        "This is urgent!",
        "How do I change my password?",
        "Please I need abortion pills",
        "I am bleeding heavily",
        "Hello, is anyone there?",
        "I want to speak to your supervisor.",
        "What are your working hours?",
        "Thanks, that was helpful.",
        "what is abortion?",
        "I want to abort my pregnacy",
        "I need help, I'm scared",
        "Is it safe to take abortion pills?",
        "How long does an abortion take?",
        "What are the side effects of abortion?",
    ]

    for msg in test_messages:
        intent, conf = detect_intent(msg, clf, vectorizer)
        print(f"User: {msg}\nPredicted intent: {intent} (confidence: {conf:.2f})\n")
