import os
import json
import re
from typing import Tuple, Optional
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
#from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_together import Together

try:
    from .intent_inference import detect_intent
except ImportError:
    from intent_inference import detect_intent

# Import the comprehensive prompt
try:
    from .abortion_counselling_prompt import (
        SYSTEM_PROMPT,
        CRISIS_PATTERNS,
        ESCALATION_MESSAGES
    )
except ImportError:
    from abortion_counselling_prompt import (
        SYSTEM_PROMPT,
        CRISIS_PATTERNS,
        ESCALATION_MESSAGES
    )

import gradio as gr


#from summerizer import ConversationMemory


# Initialize conversation memory (global for session)
#memory = ConversationMemory()


# 1. Set your Together API key
os.environ["TOGETHER_API_KEY"] = "b65d99efc7e9fde5f5d8ff5e14171b2c736c26e8d45732093efde92c1d6c2f9e"

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(script_dir, "data")

# Load prompt configuration
prompt_config_path = os.path.join(script_dir, "prompt_instructions.json")
with open(prompt_config_path, 'r', encoding='utf-8') as f:
    prompt_config = json.load(f)

# 2. Load documents
loader = DirectoryLoader(data_dir, glob="**/*.txt")
docs = loader.load()
print(f"Loaded {len(docs)} documents.")

# 3. Split documents for embedding
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
split_docs = splitter.split_documents(docs)
print(f"Split into {len(split_docs)} document chunks.")

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

#detect crisis fuction from claude

def detect_crisis(text: str) -> Tuple[Optional[str], bool]:
    """
    Detect crisis indicators in user message.
    Returns: (crisis_type, is_crisis)
    """
    text_lower = text.lower()
    
    for crisis_type, patterns in CRISIS_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return crisis_type, True
    
    return None, False

#def build_structured_prompt(config, context, user_query, history=None):
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
#     #prompt_format = config.get("prompt_format", "xml").lower()
    
#     #if prompt_format == "xml":
#         # Build XML-structured prompt
#     old_prompt = f"""<instruction>
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

def build_structured_prompt(config, context, user_query, lang='EN', history=None):
    """
    Build prompt using comprehensive system prompt instead of simple JSON config.
    Now ignores most of the JSON config and uses SYSTEM_PROMPT instead.
    """

    # Format conversation history
    if history:
        # History is already a formatted string from prepare_history_for_llm
        if isinstance(history, str):
            history_text = history
        # Legacy format: list of dicts with 'user' and 'bot' keys
        elif isinstance(history, list):
            history_text = "\n".join([
                f"User: {turn['user']}\nBot: {turn['bot']}"
                for turn in history[-5:]  # Last 5 turns only
            ])
        else:
            history_text = str(history)
    else:
        history_text = "This is the start of the conversation."
    # Set language
    language = 'English'
    if (lang == 'fr') or (lang == 'FR') or (lang == 'Fr'):
        language = 'French'
    
    # Build comprehensive prompt
    prompt = f"""{SYSTEM_PROMPT}

<relevant_information>
The following information from our knowledge base may be helpful:

{context}
</relevant_information>

<conversation_history>
{history_text}
</conversation_history>

<user_message>
{user_query}
</user_message>

<instructions>
Respond appropriately following ALL guidelines above.

REMEMBER:
1. Be non-directive (don't tell them what to do)
2. Be non-judgmental (validate all feelings)
3. Provide accurate information
4. Protect privacy

Respond in plain text (no XML tags in output).
Respond in {language}
</instructions>
"""
    
    return prompt

    
def get_response(user_query, lang, history=None):
    """
    Get a response from the chatbot based on the user query.
    Now with crisis detection and escalation.
    
    """
    #if user_query.lower() in ["exit", "quit"]:
        #memory.add_turn("User", user_query)
        #memory.add_turn("Bot", "Goodbye!")
        #return "Goodbye!"

    # Step 0: Detect intent
    intent, confidence = detect_intent(user_query)
    #memory.add_turn("User", user_query)
    print(f"Detected intent: {intent} (confidence: {confidence})")

    if intent == "escalate" and confidence > 0.43:
        #memory.add_turn("Bot", "Escalating to a human agent...")
        return "Escalating to a counsellor..."
    
    #Crisis detection
    crisis_type, is_crisis = detect_crisis(user_query)
    
    if is_crisis:
        print(f"⚠️ CRISIS DETECTED: {crisis_type}")
        escalation_msg = ESCALATION_MESSAGES.get(
            crisis_type, 
            ESCALATION_MESSAGES["coercion"]  # Default
        )
        return escalation_msg

    # Step 1: Retrieve relevant documents
    retrieved_docs = retriever.get_relevant_documents(user_query)
    if not retrieved_docs:
        #memory.add_turn("Bot", out_of_scope_message)
        return out_of_scope_message

    # Step 2: Collate retrieved content for context
    context = "\n".join(doc.page_content for doc in retrieved_docs)

    # Step 3: Build structured prompt using configuration
    prompt = build_structured_prompt(
        config=prompt_config,
        context=context,
        user_query=user_query,
        lang=lang,
        history=history
    )

    # Step 4: Get answer from LLM
    try:
        response = llm.invoke(prompt)
    except Exception as e:
        print("Error occurred while invoking LLM:", e)
        response = "Sorry, I couldn't process your request."
    #memory.add_turn("Bot", response)
    return response

def chat_interface(user_query, history):
    """
    Interface function for Gradio to handle user queries.
    """
    chat_history = []
    if history:
        for user_msg, bot_msg in history:
            if user_msg and bot_msg:
                chat_history.append({"user": user_msg, "bot": bot_msg})

    response = get_response(user_query, 'EN', history=chat_history)
    # Optionally, you can return the history as well for debugging or display
    # full_history = memory.get_history()
    return response

PRIVACY_NOTICE = """🔒 **PRIVACY & CONFIDENTIALITY**

**Your privacy is protected:**
- This conversation is confidential
- Your information is secure
- We never share with anyone

**For crisis support:**
- Counselor: +237-XXX-XXX-XXX
- Crisis Line: XXX-XXX-XXXX (24/7)

How can I help you today?
"""

with gr.Blocks() as demo:
    gr.ChatInterface(
        fn=chat_interface,
        title="Abortion Information & Support Bot",
        description=PRIVACY_NOTICE,
        theme="soft",
        examples=["What is abortion?",
                  "What is safe abortion?",
                  "What are the risks of abortion?"
                  "What are the different methods",
                  "I'm not sure what to do"
                  ]
    )

if __name__ == "__main__":
    print("Starting the chatbot interface...")
    # Launch the Gradio interface
    demo.launch(share=True)
    