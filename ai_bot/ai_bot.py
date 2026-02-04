import os
import re
from typing import Tuple, Optional

from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
#from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_together import Together
#from .intent_inference import detect_intent
import gradio as gr

try:
    from .menstrual_health_prompt import (
        MENSTRUAL_HEALTH_SYSTEM_PROMPT,
        MENSTRUAL_MEDICAL_ALERTS,
        MEDICAL_ALERT_RESPONSES,
        detect_medical_alert
    )
except ImportError:
    from menstrual_health_prompt import (
        MENSTRUAL_HEALTH_SYSTEM_PROMPT,
        MENSTRUAL_MEDICAL_ALERTS,
        MEDICAL_ALERT_RESPONSES,
        detect_medical_alert
    )


#from summerizer import ConversationMemory


# Initialize conversation memory (global for session)
#memory = ConversationMemory()


# 1. Set your Together API key
os.environ["TOGETHER_API_KEY"] = "b65d99efc7e9fde5f5d8ff5e14171b2c736c26e8d45732093efde92c1d6c2f9e"

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "data")

# Load prompt configuration
# prompt_config_path = os.path.join(script_dir, "prompt_instructions.json")
# with open(prompt_config_path, 'r') as f:
#     prompt_config = json.load(f)

# 2. Load documents
loader = DirectoryLoader(data_dir, glob="**/*.txt")
docs = loader.load()

# 3. Split documents for embedding
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
split_docs = splitter.split_documents(docs)

# 4. Set up embeddings
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 5. Build a Chroma vector database
db = Chroma.from_documents(split_docs, embedding)

# 6. Set up Together LLM
# Model options (uncomment the one you want to use):

llm_model = os.getenv("LLM", "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo")

# RECOMMENDED: Best for empathetic healthcare conversations
llm = Together(
    model=llm_model,
    temperature=0.7,  # Higher temp for more natural, varied responses
    max_tokens=512,   # Limit response length
    top_p=0.9         # Nucleus sampling for better quality
)

# ALTERNATIVE 1: Excellent for medical contexts (slightly cheaper)
# llm = Together(
#     model="Qwen/Qwen2.5-72B-Instruct-Turbo",
#     temperature=0.7,
#     max_tokens=512,
#     top_p=0.9
# )

# ALTERNATIVE 2: Budget-friendly option (faster, cheaper)
# llm = Together(
#     model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
#     temperature=0.7,
#     max_tokens=512,
#     top_p=0.9
# )

# OLD MODEL (less suitable for empathetic conversations)
# llm = Together(
#     model="mistralai/Mixtral-8x7B-Instruct-v0.1",
#     temperature=0.0
# )

# 7. Strict retrieval and answer logic
out_of_scope_message = (
    "Sorry, I can only answer questions related to abortion."
)

retriever = db.as_retriever()

print("Welcome to your RAG chatbot! Type 'exit' or 'quit' to stop.")

# def build_structured_prompt(config, context, user_query, history=None):
#     """
#     Build a structured prompt based on the configuration format.
#     Supports XML, Markdown, and plain text formats.
    
#     Args:
#         config: Dictionary containing prompt configuration
#         context: Retrieved document context
#         user_query: User's question
#         history: Optional conversation history
        
#     Returns:
#         Formatted prompt string
#     """
#     prompt_format = config.get("prompt_format", "xml").lower()
    
#     if prompt_format == "xml":
#         # Build XML-structured prompt
#         prompt = f"""<instruction>
# You are a {config.get('role', 'helpful assistant')}. {config.get('task', 'Answer the user question.')}
# </instruction>

# <guidelines>
# """
#         # Add guidelines
#         for i, guideline in enumerate(config.get('guidelines', []), 1):
#             prompt += f"{i}. {guideline}\n"
        
#         prompt += "</guidelines>\n\n"
        
#         # Add constraints if any
#         constraints = config.get('constraints', {})
#         if constraints:
#             prompt += "<constraints>\n"
#             if constraints.get('context_only'):
#                 prompt += "- Use ONLY the provided context to answer\n"
#             if 'max_sentences' in constraints:
#                 prompt += f"- Maximum response length: {constraints['max_sentences']} sentences\n"
#             prompt += "</constraints>\n\n"
        
#         # Add tone
#         if 'tone' in config:
#             prompt += f"<tone>\n{config['tone']}\n</tone>\n\n"
        
#         # Add engagement requirement
#         if config.get('engagement_required'):
#             prompt += "<engagement>\nALWAYS end your response with one of:\n"
#             prompt += "- A relevant follow-up question\n"
#             prompt += "- An offer to explain related topics\n"
#             prompt += "- An invitation to ask more questions\n"
#             prompt += "</engagement>\n\n"
        
#         # Add output instructions
#         output_instructions = config.get('output_instructions', [])
#         if output_instructions:
#             prompt += "<output_format>\n"
#             for instruction in output_instructions:
#                 prompt += f"- {instruction}\n"
#             prompt += "</output_format>\n\n"
        
#         # Add context
#         prompt += f"<context>\n{context}\n</context>\n\n"
        
#         # Add conversation history
#         if history:
#             prompt += f"<conversation_history>\n{history}\n</conversation_history>\n\n"
#         else:
#             prompt += "<conversation_history>\nThis is the start of the conversation.\n</conversation_history>\n\n"
        
#         # Add user query
#         prompt += f"<user_query>\n{user_query}\n</user_query>\n\n"
        
#         # Add response section
#         prompt += "<response>\n"
        
#     elif prompt_format == "markdown":
#         # Build Markdown-structured prompt
#         prompt = f"""# Task
# You are a {config.get('role', 'helpful assistant')}. {config.get('task', 'Answer the user question.')}

# ## Guidelines
# """
#         for i, guideline in enumerate(config.get('guidelines', []), 1):
#             prompt += f"{i}. {guideline}\n"
        
#         prompt += "\n"
        
#         # Add constraints
#         constraints = config.get('constraints', {})
#         if constraints:
#             prompt += "## Constraints\n"
#             if constraints.get('context_only'):
#                 prompt += "- Use ONLY the provided context\n"
#             if 'max_sentences' in constraints:
#                 prompt += f"- Max length: {constraints['max_sentences']} sentences\n"
#             prompt += "\n"
        
#         # Add tone
#         if 'tone' in config:
#             prompt += f"## Tone\n{config['tone']}\n\n"
        
#         # Add engagement
#         if config.get('engagement_required'):
#             prompt += "## Engagement\nALWAYS end with: follow-up question, offer related info, or invite more questions\n\n"
        
#         # Add output instructions
#         output_instructions = config.get('output_instructions', [])
#         if output_instructions:
#             prompt += "## Output Format\n"
#             for instruction in output_instructions:
#                 prompt += f"- {instruction}\n"
#             prompt += "\n"
        
#         # Add context
#         prompt += f"## Context\n{context}\n\n"
        
#         # Add history
#         prompt += f"## Conversation History\n{history if history else 'First interaction'}\n\n"
        
#         # Add user query
#         prompt += f"## User Question\n{user_query}\n\n"
        
#         prompt += "## Your Response\n"
        
#     else:  # plain text format
#         # Build plain text prompt (fallback)
#         prompt = f"You are a {config.get('role', 'helpful assistant')}. "
#         prompt += f"{config.get('task', 'Answer the user question.')}\n\n"
        
#         prompt += "GUIDELINES:\n"
#         for i, guideline in enumerate(config.get('guidelines', []), 1):
#             prompt += f"{i}. {guideline}\n"
        
#         prompt += f"\nTone: {config.get('tone', 'professional')}\n\n"
        
#         if config.get('engagement_required'):
#             prompt += "Remember to end with an engaging follow-up question.\n\n"
        
#         # Add output instructions
#         output_instructions = config.get('output_instructions', [])
#         if output_instructions:
#             prompt += "OUTPUT FORMAT:\n"
#             for instruction in output_instructions:
#                 prompt += f"- {instruction}\n"
#             prompt += "\n"
        
#         prompt += f"Context:\n{context}\n\n"
#         prompt += f"Conversation History:\n{history if history else 'This is the start of the conversation.'}\n\n"
#         prompt += f"Question: {user_query}\n\n"
#         prompt += "Answer:"
    
#     return prompt


def build_prompt(context: str, user_query: str, lang: str = "en", history: list = None) -> str:
    """Build complete prompt for menstrual health bot."""
    
    # Format conversation history
    if history:
        history_text = "\n".join([
            f"User: {turn['user']}\nBot: {turn['bot']}"
            for turn in history[-5:]  # Last 5 turns
        ])
    else:
        history_text = "This is the start of the conversation."
        
    if lang.lower()  in ["en", "english"]:
        language = "English"
    elif lang.lower() in ["fr", "french"]:
        language = "French"
    else:
        language = "English"
    

    # Build prompt
    prompt = f"""{MENSTRUAL_HEALTH_SYSTEM_PROMPT}

<relevant_information>
The following information from the knowledge base may be helpful:

{context}
</relevant_information>

<conversation_history>
{history_text}
</conversation_history>

<user_question>
{user_query}
</user_question>

<instructions>
Respond following all guidelines above.

If a question is out of scope, respond with:
I can only answer questions related to menstrual health, including periods, cramps, products, and menstrual dignity. What would you like to know?
REMEMBER:
1. Use inclusive language (not only women menstruate)
2. Normalize menstruation (counter stigma)
3. Provide accurate, evidence-based information
4. Be specific with medical info (dosages, warnings)
5. Recommend medical consultation when appropriate

Respond in plain text (no XML tags in output).
CRITICAL: You MUST respond ENTIRELY in {language}. Every single word of your response must be in {language}. Do not mix languages.
</instructions>
"""
    
    return prompt

    
# def get_response(user_query, history=None):
#     """
#     Get a response from the chatbot based on the user query.
#     """
#     #if user_query.lower() in ["exit", "quit"]:
#         #memory.add_turn("User", user_query)
#         #memory.add_turn("Bot", "Goodbye!")
#         #return "Goodbye!"

#     # Step 0: Detect intent
#     intent, confidence = detect_intent(user_query)
#     #memory.add_turn("User", user_query)
#     print(f"Detected intent: {intent} (confidence: {confidence})")

#     if intent == "escalate" and confidence > 0.6:
#         #memory.add_turn("Bot", "Escalating to a human agent...")
#         return "Escalating to a counsellor..."

#     # Step 1: Retrieve relevant documents
#     retrieved_docs = retriever.get_relevant_documents(user_query)
#     if not retrieved_docs:
#         #memory.add_turn("Bot", out_of_scope_message)
#         return out_of_scope_message

#     # Step 2: Collate retrieved content for context
#     context = "\n".join(doc.page_content for doc in retrieved_docs)

#     # Step 3: Build structured prompt using configuration
#     prompt = build_structured_prompt(
#         config=prompt_config,
#         context=context,
#         user_query=user_query,
#         history=history
#     )

#     # Step 4: Get answer from LLM
#     try:
#         response = llm.invoke(prompt)
#     except Exception as e:
#         print("Error occurred while invoking LLM:", e)
#         response = "Sorry, I couldn't process your request."
#     #memory.add_turn("Bot", response)
#     return response


def get_response(user_query: str, lang: str = "en", history: list = None) -> str:
    """
    Get response from menstrual health chatbot.
    Includes medical alert detection.
    """
    
    # STEP 1: Check for medical alerts
    alert_type, requires_attention = detect_medical_alert(user_query)
    
    if requires_attention:
        print(f"⚠️ MEDICAL ALERT: {alert_type}")
        # Prepend medical alert to response
        alert_message = MEDICAL_ALERT_RESPONSES.get(
            alert_type,
            MEDICAL_ALERT_RESPONSES["severe_symptoms"]
        )
        
        # Still retrieve context for additional info
        retrieved_docs = retriever.get_relevant_documents(user_query)
        context = "\n\n".join([doc.page_content for doc in retrieved_docs])
        
        prompt = build_prompt(context, user_query, lang, history)
        
        try:
            response = llm.invoke(prompt)
            # Add medical alert before the response
            return f"{alert_message}\n\n{response}"
        except Exception as e:
            print(f"Error: {e}")
            return alert_message
    
    # STEP 2: Normal flow - retrieve context and respond
    retrieved_docs = retriever.get_relevant_documents(user_query)

    if not retrieved_docs:
        # Return localized message based on language
        if lang.lower() in ["fr", "french"]:
            return "Je peux vous aider avec des questions sur la santé menstruelle, y compris les règles, les crampes, les produits et la dignité menstruelle. Que souhaitez-vous savoir?"
        else:
            return "I can help with questions about menstrual health, including periods, cramps, products, and menstrual dignity. What would you like to know?"

    context = "\n\n".join([doc.page_content for doc in retrieved_docs])
    
    if lang.lower() in ["fr", "french"]:
        print("Responding in French")
        lang = "french"

    prompt = build_prompt(context, user_query, lang, history)
    
    try:
        response = llm.invoke(prompt)
        return response
    except Exception as e:
        print(f"Error: {e}")
        # Return localized error message
        if lang.lower() in ["fr", "french"]:
            return "Je rencontre des difficultés techniques. Veuillez réessayer ou consulter un professionnel de santé pour les questions médicales."
        else:
            return "I'm having technical difficulties. Please try again or consult a healthcare provider for medical questions."



# def chat_interface(user_query, history):
#     """
#     Interface function for Gradio to handle user queries.
#     """
#     response = get_response(user_query)
#     # Optionally, you can return the history as well for debugging or display
#     # full_history = memory.get_history()
#     return response
  
# with gr.Blocks() as demo:
#     gr.ChatInterface(
#         fn=chat_interface,
#         title="RAG Chatbot Demo",
#         description="Ask questions about abortion.",
#         theme="soft",
#         examples=["What is abortion?", "What is safe abortion?", "What are the risks of abortion?"]
#     )

# if __name__ == "__main__":
#     print("Starting the chatbot interface...")
#     # Launch the Gradio interface
#     demo.launch()


def chat_interface(user_query: str, history) -> str:
    """Gradio interface function."""
    
    # Convert Gradio history format
    chat_history = []
    if history:
        for item in history:
            # Gradio ChatInterface passes tuples with (user_msg, bot_msg) or more elements
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                user_msg, bot_msg = item[0], item[1]
                if user_msg and bot_msg:
                    chat_history.append({"user": user_msg, "bot": bot_msg})
    
    response = get_response(user_query, chat_history)
    return response


# Create Gradio interface
WELCOME_MESSAGE = """🌸 **Welcome to Menstrual Dignity & Health Support**

I provide inclusive, stigma-free information about menstruation for everyone who menstruates - including women, girls, trans men, non-binary people, and all menstruators.

**I can help with:**
- Understanding your menstrual cycle
- Managing cramps and pain
- Choosing menstrual products
- Busting myths and challenging stigma
- Sexual health during periods
- Gender-affirming menstrual strategies
- When to seek medical help

**Remember:** 
- Menstruation is natural, healthy, and nothing to be ashamed of
- Not only women menstruate
- You deserve to manage your period with dignity

What would you like to know?
"""
with gr.Blocks() as demo:
    gr.ChatInterface(
        fn=chat_interface,
        title="Menstrual Dignity & Health Bot",
        description=WELCOME_MESSAGE,
        #theme="soft",
        examples=[
            "What is menstrual dignity?",
            "How do I use ibuprofen for cramps?",
            "Can I swim during my period?",
            "Is menstrual blood dirty?",
            "I'm a trans guy and periods make me dysphoric. What can I do?",
            "Can you get pregnant during your period?",
            "What menstrual products are available?",
            "When should I see a doctor about my period?",
                ],
    #chatbot=gr.Chatbot(height=500),
    #textbox=gr.Textbox(placeholder="Ask about menstrual health...", container=False, scale=7),
    #retry_btn="🔄 Retry",
    #undo_btn="↩️ Undo",
    #clear_btn="🗑️ Clear"
)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("MENSTRUAL DIGNITY & HEALTH CHATBOT")
    print("="*60)
    
    #if not TOGETHER_API_KEY:
        #print("\n⚠️ ERROR: Set TOGETHER_API_KEY environment variable")
        #exit(1)
    
    print("\nLaunching Gradio interface...")
    demo.launch(share=True)    