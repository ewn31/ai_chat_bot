"""
Improved Intent Detection Training Data for Abortion Counseling Bot

This dataset addresses the following issues from the original:
1. Severe class imbalance (was 80:20:20:20:20)
2. Missing French language examples (21% of users speak French)
3. Insufficient general_question examples about abortion information
4. Missing location/cost/provider requests that should escalate
5. Inability to distinguish "I need pills" vs "What are pills?"

New distribution (more balanced):
- escalate: ~120 examples
- general_question: ~90 examples (MAJOR INCREASE)
- feedback: ~25 examples
- greeting: ~25 examples
- goodbye: ~25 examples

Total: ~285 examples (vs original 160)
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.utils.class_weight import compute_class_weight
import joblib
import numpy as np

# Comprehensive training data
data = [
    # ========================================================================
    # ESCALATE - Medical Emergencies (~40 examples)
    # ========================================================================
    ("I am bleeding", "escalate"),
    ("I'm bleeding heavily", "escalate"),
    ("Please I am still bleeding. please is that normal. Like now it was heavy and dark with some clots", "escalate"),
    ("I am bleeding a lot after taking something, please help.", "escalate"),
    ("I'm passing big clots and my stomach hurts — is this normal?", "escalate"),
    ("Please, I'm still bleeding two days later and it's heavy.", "escalate"),
    ("I fainted after bleeding, what should I do?", "escalate"),
    ("My bleeding smells bad and I have a fever.", "escalate"),
    ("I took pills and now my bleeding is very heavy with dizziness.", "escalate"),
    ("Severe abdominal pain and vomiting after trying to end my pregnancy. Please help.", "escalate"),
    ("I can't stand up, pain is unbearable after the procedure.", "escalate"),
    ("My temperature is 39°C and I have bad pain. What do I do?", "escalate"),
    ("I'm passing tissue and feel faint — is this emergency?", "escalate"),
    ("I feel pains", "escalate"),
    ("I've got heavy bleed n cramps, not normal right?", "escalate"),
    ("I'm dizzy, confused, and can't walk steady. Please someone help.", "escalate"),
    ("Please help me, I'm bleeding and scared I'll die.", "escalate"),
    ("I'm begging you — send help or tell me where to go.", "escalate"),
    ("I took meds but I don't remember the name — I'm worried.", "escalate"),
    ("I think something is left inside me; my pain isn't going away.", "escalate"),
    ("I'm shaking and have chills after the procedure", "escalate"),
    ("The bleeding won't stop and I'm getting weak", "escalate"),
    ("I can't stop vomiting and I'm in pain", "escalate"),
    ("My fever is getting worse", "escalate"),
    ("I feel like I'm going to pass out", "escalate"),
    
    # French - Medical Emergencies
    ("Je saigne beaucoup", "escalate"),
    ("J'ai très mal au ventre", "escalate"),
    ("Je me sens très faible", "escalate"),
    ("J'ai de la fièvre et des douleurs", "escalate"),
    ("Je saigne depuis deux jours", "escalate"),
    ("J'ai des caillots de sang", "escalate"),
    ("Je ne peux pas me lever", "escalate"),
    ("Aidez-moi s'il vous plaît, je saigne", "escalate"),
    ("J'ai pris des médicaments et maintenant je saigne beaucoup", "escalate"),
    ("Est-ce normal de saigner autant?", "escalate"),
    
    # ========================================================================
    # ESCALATE - Direct Requests for Pills/Medication (~30 examples)
    # ========================================================================
    ("Pls am sorry for entering you dm without you concern but pls I need your help pls I need abortion pills", "escalate"),
    ("Pls i need abortion pills", "escalate"),
    ("Hi pls I need abortion pills for pregnancy about 2 to 3 weeks and how much", "escalate"),
    ("Please I need abortion pills right now, where can I get them?", "escalate"),
    ("Can someone send me meds for abortion? I can't go to a clinic.", "escalate"),
    ("I'm 6 weeks pregnant — how do I get pills?", "escalate"),
    ("Where can I get the pills please", "escalate"),
    ("I need pills urgently", "escalate"),
    ("Can you give me abortion pills?", "escalate"),
    ("Where do I buy abortion pills?", "escalate"),
    ("How can I get misoprostol?", "escalate"),
    ("I need mifepristone, where can I find it?", "escalate"),
    ("Can you send me the medication?", "escalate"),
    ("I want to order abortion pills", "escalate"),
    ("Do you have pills I can buy?", "escalate"),
    ("Where can I purchase abortion medication?", "escalate"),
    ("I need to get pills today", "escalate"),
    ("Can you help me get the pills?", "escalate"),
    ("Pls i need pills.. DM me.", "escalate"),
    ("Need pills asap", "escalate"),
    
    # French - Pill Requests
    ("J'ai besoin de pilules d'avortement", "escalate"),
    ("Où puis-je acheter des pilules?", "escalate"),
    ("Je veux des pilules abortives", "escalate"),
    ("Pouvez-vous m'envoyer des médicaments?", "escalate"),
    ("J'ai besoin de misoprostol", "escalate"),
    ("Où trouver des pilules d'avortement?", "escalate"),
    ("Je veux commander des pilules", "escalate"),
    ("Avez-vous des pilules à vendre?", "escalate"),
    ("J'ai besoin de médicaments maintenant", "escalate"),
    
    # ========================================================================
    # ESCALATE - Provider/Clinic/Cost Requests (~25 examples)
    # ========================================================================
    ("Looking for a provider", "escalate"),
    ("Can you refer me to a nearby clinic that does abortions?", "escalate"),
    ("I have no money — is there a free service or counselor who can help?", "escalate"),
    ("Are there safe providers in my city? I need contact details.", "escalate"),
    ("I need a female counselor who speaks my language — can you connect me?", "escalate"),
    ("Where can I get abortion services in Buea?", "escalate"),
    ("I need a clinic in Douala", "escalate"),
    ("Can you give me a doctor's contact?", "escalate"),
    ("How much does abortion cost?", "escalate"),
    ("What's the price for abortion in Cameroon?", "escalate"),
    ("I need an affordable clinic", "escalate"),
    ("Can you recommend a safe provider?", "escalate"),
    ("I need to find a doctor who does abortions", "escalate"),
    ("Where is the nearest abortion clinic?", "escalate"),
    ("How much will it cost me?", "escalate"),
    ("Do you know any providers in Yaoundé?", "escalate"),
    ("I need contact information for a clinic", "escalate"),
    ("Can you connect me with a provider?", "escalate"),
    ("I'm looking for affordable abortion services", "escalate"),
    ("Where can I go for help in my city?", "escalate"),
    
    # French - Provider/Cost Requests
    ("Où puis-je obtenir un avortement?", "escalate"),
    ("Combien coûte un avortement?", "escalate"),
    ("Pouvez-vous me donner le contact d'un médecin?", "escalate"),
    ("Je cherche une clinique à Douala", "escalate"),
    ("Y a-t-il des services gratuits?", "escalate"),
    ("J'ai besoin d'un médecin qui parle français", "escalate"),
    ("Ces médicaments coûtent environ combien ici au cameroun", "escalate"),
    ("Je veux que vous puissiez me trouver le contact d'un professionnel de santé", "escalate"),
    
    # ========================================================================
    # ESCALATE - Emotional Distress & Crisis (~15 examples)
    # ========================================================================
    ("I don't have anywhere to go; I'm terrified and don't know who to tell.", "escalate"),
    ("I feel suicidal because of this pregnancy — I need someone to talk to.", "escalate"),
    ("I'm a minor and my parents will kick me out if they find out. Please help.", "escalate"),
    ("I'm shaking and crying and don't know what to do next.", "escalate"),
    ("I was forced into this and I need support and help getting care.", "escalate"),
    ("I need help, I'm scared", "escalate"),
    ("I don't know what to do, I'm panicking", "escalate"),
    ("I'm so scared and alone", "escalate"),
    ("I can't tell anyone about this", "escalate"),
    ("I'm afraid of what will happen", "escalate"),
    ("My partner forces me to keep it; I need help in secret.", "escalate"),
    ("I was assaulted and need emergency help and counseling.", "escalate"),
    ("I'm desperate and don't know where to turn", "escalate"),
    ("Need help asap. 2wks preg. scared.", "escalate"),
    ("I'm having a mental breakdown", "escalate"),
    
    # ========================================================================
    # ESCALATE - General Human Agent Requests (~10 examples)
    # ========================================================================
    ("I want to talk to a real person.", "escalate"),
    ("Can I speak to a human agent?", "escalate"),
    ("Not helping, I need someone!", "escalate"),
    ("Let me talk to support.", "escalate"),
    ("Can you connect me with an agent?", "escalate"),
    ("Is there a real person I can talk to?", "escalate"),
    ("I need to speak with a counsellor", "escalate"),
    ("Can I talk to someone?", "escalate"),
    ("Connect me to a human", "escalate"),
    ("I want to speak to your supervisor.", "escalate"),
    
    # ========================================================================
    # GENERAL_QUESTION - Abortion Information (~45 examples)
    # ========================================================================
    ("What is abortion?", "general_question"),
    ("What is safe abortion?", "general_question"),
    ("How does abortion work?", "general_question"),
    ("What should I expect during an abortion?", "general_question"),
    ("Is abortion safe?", "general_question"),
    ("What are the side effects of abortion?", "general_question"),
    ("What are the risks of abortion?", "general_question"),
    ("How long does abortion take?", "general_question"),
    ("What are the different methods of abortion?", "general_question"),
    ("What's the difference between surgical and medical abortion?", "general_question"),
    ("Can I get pregnant again after abortion?", "general_question"),
    ("How will I know if the abortion was successful?", "general_question"),
    ("When can I take a pregnancy test after abortion?", "general_question"),
    ("What is medical abortion?", "general_question"),
    ("What is surgical abortion?", "general_question"),
    ("How effective is abortion?", "general_question"),
    ("What happens during a medication abortion?", "general_question"),
    ("What should I expect after an abortion?", "general_question"),
    ("How do I know which abortion method is right for me?", "general_question"),
    ("Is abortion painful?", "general_question"),
    ("How long does recovery take after abortion?", "general_question"),
    ("Can abortion affect my future fertility?", "general_question"),
    ("What are the emotional effects of abortion?", "general_question"),
    ("Is it normal to feel sad after an abortion?", "general_question"),
    ("What support is available after abortion?", "general_question"),
    ("How do I take care of myself after an abortion?", "general_question"),
    ("What should I avoid after an abortion?", "general_question"),
    ("When can I have sex after an abortion?", "general_question"),
    ("What are the warning signs after abortion?", "general_question"),
    ("How much bleeding is normal after abortion?", "general_question"),
    ("When should my period return after abortion?", "general_question"),
    ("Can I exercise after an abortion?", "general_question"),
    ("What foods should I eat after abortion?", "general_question"),
    
    # French - General Questions
    ("Qu'est-ce que l'avortement?", "general_question"),
    ("Comment fonctionne l'avortement médical?", "general_question"),
    ("L'avortement est-il sûr?", "general_question"),
    ("Quels sont les effets secondaires?", "general_question"),
    ("Combien de temps dure un avortement?", "general_question"),
    ("Quelles sont les méthodes d'avortement?", "general_question"),
    ("Est-ce que l'avortement fait mal?", "general_question"),
    ("Puis-je tomber enceinte après un avortement?", "general_question"),
    ("Qu'est-ce qu'un avortement médicamenteux?", "general_question"),
    ("Quels sont les risques de l'avortement?", "general_question"),
    ("Comment savoir si l'avortement a réussi?", "general_question"),
    
    # ========================================================================
    # GENERAL_QUESTION - Pills Information (NOT requests) (~20 examples)
    # ========================================================================
    ("What are abortion pills?", "general_question"),
    ("How do abortion pills work?", "general_question"),
    ("What are abortion pills made of?", "general_question"),
    ("Tell me about medication abortion", "general_question"),
    ("How effective are abortion pills?", "general_question"),
    ("What's the difference between mifepristone and misoprostol?", "general_question"),
    ("How long do abortion pills take to work?", "general_question"),
    ("What are the side effects of abortion pills?", "general_question"),
    ("Are abortion pills safe?", "general_question"),
    ("Can I use abortion pills at home?", "general_question"),
    ("How do I know if abortion pills worked?", "general_question"),
    ("What happens after taking abortion pills?", "general_question"),
    ("How many pills do I need to take?", "general_question"),
    ("What is the success rate of abortion pills?", "general_question"),
    ("Can abortion pills fail?", "general_question"),
    ("What if abortion pills don't work?", "general_question"),
    ("Are there different types of abortion pills?", "general_question"),
    ("How far along can I be to use pills?", "general_question"),
    ("What's the time frame for using abortion pills?", "general_question"),
    ("Tell me about the abortion pill process", "general_question"),
    
    # French - Pills Information
    ("Qu'est-ce que les pilules d'avortement?", "general_question"),
    ("Comment fonctionnent les pilules?", "general_question"),
    ("Les pilules sont-elles sûres?", "general_question"),
    ("Quels sont les effets des pilules?", "general_question"),
    ("Comment prendre les pilules d'avortement?", "general_question"),
    
    # ========================================================================
    # GENERAL_QUESTION - Legal & Other Topics (~15 examples)
    # ========================================================================
    ("Is abortion legal?", "general_question"),
    ("What are the laws about abortion?", "general_question"),
    ("What is the legal age for abortion?", "general_question"),
    ("Do I need parental consent?", "general_question"),
    ("What are my rights regarding abortion?", "general_question"),
    ("Is abortion confidential?", "general_question"),
    ("Will my information be kept private?", "general_question"),
    ("Who will know about my abortion?", "general_question"),
    ("Can someone find out I had an abortion?", "general_question"),
    ("What is informed consent for abortion?", "general_question"),
    ("Do I need my partner's permission?", "general_question"),
    ("What if I'm under 18?", "general_question"),
    ("À 19ans suis-je encore mineur?", "general_question"),
    ("Can I change my mind about abortion?", "general_question"),
    ("What are the alternatives to abortion?", "general_question"),
    
    # French - Legal Questions
    ("L'avortement est-il légal au Cameroun?", "general_question"),
    ("Ai-je besoin du consentement parental?", "general_question"),
    ("Quels sont mes droits?", "general_question"),
    ("Est-ce confidentiel?", "general_question"),
    
    # ========================================================================
    # GENERAL_QUESTION - Other Service Questions (~10 examples)
    # ========================================================================
    ("How does your service work?", "general_question"),
    ("What can you help me with?", "general_question"),
    ("What information do you provide?", "general_question"),
    ("Can you answer questions about abortion?", "general_question"),
    ("What topics can you discuss?", "general_question"),
    ("Are you a real person or a bot?", "general_question"),
    ("How do I use this service?", "general_question"),
    ("What are your working hours?", "general_question"),
    ("Is this service free?", "general_question"),
    ("Who runs this service?", "general_question"),
    
    # ========================================================================
    # FEEDBACK (~25 examples)
    # ========================================================================
    ("Thank you, that's helpful.", "feedback"),
    ("Great service!", "feedback"),
    ("I appreciate your assistance.", "feedback"),
    ("You've been very helpful.", "feedback"),
    ("Thanks for the quick response.", "feedback"),
    ("Nice bot!", "feedback"),
    ("This was exactly what I needed.", "feedback"),
    ("Kudos to your support team!", "feedback"),
    ("Everything works perfectly.", "feedback"),
    ("Your service is fantastic.", "feedback"),
    ("I'm happy with this solution.", "feedback"),
    ("That solved my issue, thanks!", "feedback"),
    ("Much appreciated.", "feedback"),
    ("I'm satisfied with the support.", "feedback"),
    ("Awesome!", "feedback"),
    ("Perfect, thank you!", "feedback"),
    ("You made my day.", "feedback"),
    ("I'll recommend this to others.", "feedback"),
    ("The instructions were clear.", "feedback"),
    ("That was easy.", "feedback"),
    ("Very informative, thank you", "feedback"),
    ("This helped me a lot", "feedback"),
    ("Good information", "feedback"),
    ("Merci beaucoup", "feedback"),
    ("Très utile, merci", "feedback"),
    
    # ========================================================================
    # GREETING (~25 examples)
    # ========================================================================
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
    ("Hello, I'm here.", "greeting"),
    ("Greetings Ma'am", "greeting"),
    ("Bonjour", "greeting"),
    ("Salut", "greeting"),
    ("Bonsoir", "greeting"),
    ("Bonjour, je peux vous poser une question?", "greeting"),
    
    # ========================================================================
    # GOODBYE (~25 examples)
    # ========================================================================
    ("Goodbye.", "goodbye"),
    ("Bye!", "goodbye"),
    ("See you later.", "goodbye"),
    ("Thanks, bye.", "goodbye"),
    ("Talk to you soon.", "goodbye"),
    ("Have a nice day.", "goodbye"),
    ("I'm done, thanks.", "goodbye"),
    ("See you.", "goodbye"),
    ("Take care.", "goodbye"),
    ("Bye bye.", "goodbye"),
    ("Thanks and goodbye.", "goodbye"),
    ("I'll be back.", "goodbye"),
    ("Later!", "goodbye"),
    ("Farewell.", "goodbye"),
    ("Catch you later.", "goodbye"),
    ("Have a good one.", "goodbye"),
    ("I'm signing off.", "goodbye"),
    ("That's all I need, bye.", "goodbye"),
    ("I have to go now.", "goodbye"),
    ("Peace out.", "goodbye"),
    ("Au revoir", "goodbye"),
    ("À bientôt", "goodbye"),
    ("Merci, au revoir", "goodbye"),
    ("Bonne journée", "goodbye"),
    ("Salut, à plus tard", "goodbye"),
]

# Create DataFrame
df = pd.DataFrame(data, columns=["message", "intent"])

# Print class distribution
print("=" * 60)
print("CLASS DISTRIBUTION")
print("=" * 60)
print(df['intent'].value_counts())
print(f"\nTotal examples: {len(df)}")
print("=" * 60)

# Split into train and test sets with stratification
X_train, X_test, y_train, y_test = train_test_split(
    df['message'], 
    df['intent'], 
    test_size=0.2, 
    random_state=42, 
    stratify=df['intent']
)

# Feature extraction with TF-IDF
vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),  # Use both unigrams and bigrams
    max_features=1000,   # Limit vocabulary size
    min_df=1,            # Minimum document frequency
    lowercase=True
)
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Compute class weights to handle any remaining imbalance
class_weights = compute_class_weight(
    'balanced',
    classes=np.unique(y_train),
    y=y_train
)
class_weight_dict = dict(zip(np.unique(y_train), class_weights))

print("\nCLASS WEIGHTS:")
for intent, weight in class_weight_dict.items():
    print(f"  {intent}: {weight:.2f}")
print()

# Train classifier with class weights
clf = LogisticRegression(
    max_iter=1000,
    class_weight=class_weight_dict,  # Handle remaining imbalance
    random_state=42,
    C=1.0  # Regularization strength
)
clf.fit(X_train_vec, y_train)

# Evaluate
y_pred = clf.predict(X_test_vec)
print("=" * 60)
print("CLASSIFICATION REPORT")
print("=" * 60)
print(classification_report(y_test, y_pred))

# Save model and vectorizer
joblib.dump(clf, "intent_classifier.joblib")
joblib.dump(vectorizer, "intent_vectorizer.joblib")

print("=" * 60)
print("✅ Model and vectorizer saved!")
print("=" * 60)

# ============================================================================
# INFERENCE FUNCTIONS
# ============================================================================

def load_intent_model():
    """Load the trained intent classification model and vectorizer from disk."""
    clf = joblib.load("intent_classifier.joblib")
    vectorizer = joblib.load("intent_vectorizer.joblib")
    return clf, vectorizer

def detect_intent(user_message, clf, vectorizer, threshold=0.6):
    """
    Predict the intent of a user message.
    
    Args:
        user_message: The user's input message
        clf: Trained classifier
        vectorizer: Fitted TF-IDF vectorizer
        threshold: Minimum confidence (default 0.6, lowered from 0.7)
    
    Returns:
        (predicted_intent, confidence)
    """
    x_new = vectorizer.transform([user_message])
    probs = clf.predict_proba(x_new)[0]
    best_idx = probs.argmax()
    predicted_intent = clf.classes_[best_idx]
    confidence = probs[best_idx]
    
    # If confidence is low, default to escalate for safety in healthcare context
    if confidence < threshold and predicted_intent != "escalate":
        # Check if any escalation probability is significant
        escalate_idx = list(clf.classes_).index("escalate") if "escalate" in clf.classes_ else -1
        if escalate_idx >= 0 and probs[escalate_idx] > 0.3:
            return "escalate", probs[escalate_idx]
    
    return predicted_intent, confidence

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Load model & vectorizer
    clf, vectorizer = load_intent_model()

    print("\n" + "=" * 60)
    print("TESTING WITH SAMPLE MESSAGES")
    print("=" * 60)
    
    # Test messages covering different scenarios
    test_messages = [
        # Should escalate - pill requests
        ("I need abortion pills", "escalate"),
        ("Where can I get pills?", "escalate"),
        ("Pls i need pills", "escalate"),
        ("J'ai besoin de pilules", "escalate"),
        
        # Should escalate - medical emergencies
        ("I am bleeding heavily", "escalate"),
        ("I'm in severe pain", "escalate"),
        ("Je saigne beaucoup", "escalate"),
        
        # Should escalate - provider/cost requests
        ("How much does abortion cost?", "escalate"),
        ("I need a clinic in Douala", "escalate"),
        ("Where can I find a provider?", "escalate"),
        ("Combien coûte un avortement?", "escalate"),
        
        # Should be general_question - information
        ("What is abortion?", "general_question"),
        ("How do abortion pills work?", "general_question"),
        ("Is abortion safe?", "general_question"),
        ("What are the side effects?", "general_question"),
        ("Qu'est-ce que l'avortement?", "general_question"),
        ("Les pilules sont-elles sûres?", "general_question"),
        
        # Other intents
        ("Hello", "greeting"),
        ("Thank you", "feedback"),
        ("Goodbye", "goodbye"),
        ("Bonjour", "greeting"),
        ("Merci", "feedback"),
    ]

    correct = 0
    total = len(test_messages)
    
    for msg, expected in test_messages:
        intent, conf = detect_intent(msg, clf, vectorizer)
        status = "✅" if intent == expected else "❌"
        print(f"{status} '{msg}'")
        print(f"   Expected: {expected} | Got: {intent} (conf: {conf:.2f})\n")
        if intent == expected:
            correct += 1
    
    print("=" * 60)
    print(f"ACCURACY: {correct}/{total} ({100*correct/total:.1f}%)")
    print("=" * 60)
