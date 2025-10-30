import os
import json
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
#from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_together import Together
from .intent_inference import detect_intent
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
with open(prompt_config_path, 'r') as f:
    prompt_config = json.load(f)

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

# RECOMMENDED: Best for empathetic healthcare conversations
llm = Together(
    model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
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

# while True:
#     query = input("\nAsk a question: ")
#     if query.lower() in ["exit", "quit"]:
#         print("Goodbye!")
#         break
#     # Step 0: Detect intent
#     intent, confidence = detect_intent(query)
#     if intent == "escalate" and confidence > 0.5:
#         print("Escalating to a human agent...")
#         break  # Exit the loop to simulate escalation
#     # Step 1: Retrieve relevant documents
#     retrieved_docs = retriever.get_relevant_documents(query)
#     if not retrieved_docs:  # No relevant info found
#         print("\nAnswer:", out_of_scope_message)
#         continue
#     # Step 2: Collate retrieved content for context
#     context = "\n".join(doc.page_content for doc in retrieved_docs)
#     # Step 3: Compose prompt for the LLM (you can also add an instruction here)
#     prompt = (
#         "Use ONLY the following context to answer the user's question.\n"
#         "If the answer isn't present, say: 'Sorry, I can only answer questions related to the documents you provided.'\n"
#         f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
#     )
#     # Step 4: Get answer from LLM
#     response = llm.invoke(prompt)
#     print("\nAnswer:", response)
# Step 5: Optional - Save conversation history or handle further logic
# This can be done by appending to a file or database as needed.
# import json
# conversation_history = {
#     "query": query,
#     "intent": intent,
#     "confidence": confidence,
#     "retrieved_docs": [doc.page_content for doc in retrieved_docs],
#     "response": response
# }
# with open("conversation_history.json", "a") as f:
#     json.dump(conversation_history, f)
#     f.write("\n")  # Newline for each conversation entry


def build_structured_prompt(config, context, user_query, history=None):
    """
    Build a structured prompt based on the configuration format.
    Supports XML, Markdown, and plain text formats.
    
    Args:
        config: Dictionary containing prompt configuration
        context: Retrieved document context
        user_query: User's question
        history: Optional conversation history
        
    Returns:
        Formatted prompt string
    """
    prompt_format = config.get("prompt_format", "xml").lower()
    
    if prompt_format == "xml":
        # Build XML-structured prompt
        prompt = f"""<instruction>
You are a {config.get('role', 'helpful assistant')}. {config.get('task', 'Answer the user question.')}
</instruction>

<guidelines>
"""
        # Add guidelines
        for i, guideline in enumerate(config.get('guidelines', []), 1):
            prompt += f"{i}. {guideline}\n"
        
        prompt += "</guidelines>\n\n"
        
        # Add constraints if any
        constraints = config.get('constraints', {})
        if constraints:
            prompt += "<constraints>\n"
            if constraints.get('context_only'):
                prompt += "- Use ONLY the provided context to answer\n"
            if 'max_sentences' in constraints:
                prompt += f"- Maximum response length: {constraints['max_sentences']} sentences\n"
            prompt += "</constraints>\n\n"
        
        # Add tone
        if 'tone' in config:
            prompt += f"<tone>\n{config['tone']}\n</tone>\n\n"
        
        # Add engagement requirement
        if config.get('engagement_required'):
            prompt += "<engagement>\nALWAYS end your response with one of:\n"
            prompt += "- A relevant follow-up question\n"
            prompt += "- An offer to explain related topics\n"
            prompt += "- An invitation to ask more questions\n"
            prompt += "</engagement>\n\n"
        
        # Add output instructions
        output_instructions = config.get('output_instructions', [])
        if output_instructions:
            prompt += "<output_format>\n"
            for instruction in output_instructions:
                prompt += f"- {instruction}\n"
            prompt += "</output_format>\n\n"
        
        # Add context
        prompt += f"<context>\n{context}\n</context>\n\n"
        
        # Add conversation history
        if history:
            prompt += f"<conversation_history>\n{history}\n</conversation_history>\n\n"
        else:
            prompt += "<conversation_history>\nThis is the start of the conversation.\n</conversation_history>\n\n"
        
        # Add user query
        prompt += f"<user_query>\n{user_query}\n</user_query>\n\n"
        
        # Add response section
        prompt += "<response>\n"
        
    elif prompt_format == "markdown":
        # Build Markdown-structured prompt
        prompt = f"""# Task
You are a {config.get('role', 'helpful assistant')}. {config.get('task', 'Answer the user question.')}

## Guidelines
"""
        for i, guideline in enumerate(config.get('guidelines', []), 1):
            prompt += f"{i}. {guideline}\n"
        
        prompt += "\n"
        
        # Add constraints
        constraints = config.get('constraints', {})
        if constraints:
            prompt += "## Constraints\n"
            if constraints.get('context_only'):
                prompt += "- Use ONLY the provided context\n"
            if 'max_sentences' in constraints:
                prompt += f"- Max length: {constraints['max_sentences']} sentences\n"
            prompt += "\n"
        
        # Add tone
        if 'tone' in config:
            prompt += f"## Tone\n{config['tone']}\n\n"
        
        # Add engagement
        if config.get('engagement_required'):
            prompt += "## Engagement\nALWAYS end with: follow-up question, offer related info, or invite more questions\n\n"
        
        # Add output instructions
        output_instructions = config.get('output_instructions', [])
        if output_instructions:
            prompt += "## Output Format\n"
            for instruction in output_instructions:
                prompt += f"- {instruction}\n"
            prompt += "\n"
        
        # Add context
        prompt += f"## Context\n{context}\n\n"
        
        # Add history
        prompt += f"## Conversation History\n{history if history else 'First interaction'}\n\n"
        
        # Add user query
        prompt += f"## User Question\n{user_query}\n\n"
        
        prompt += "## Your Response\n"
        
    else:  # plain text format
        # Build plain text prompt (fallback)
        prompt = f"You are a {config.get('role', 'helpful assistant')}. "
        prompt += f"{config.get('task', 'Answer the user question.')}\n\n"
        
        prompt += "GUIDELINES:\n"
        for i, guideline in enumerate(config.get('guidelines', []), 1):
            prompt += f"{i}. {guideline}\n"
        
        prompt += f"\nTone: {config.get('tone', 'professional')}\n\n"
        
        if config.get('engagement_required'):
            prompt += "Remember to end with an engaging follow-up question.\n\n"
        
        # Add output instructions
        output_instructions = config.get('output_instructions', [])
        if output_instructions:
            prompt += "OUTPUT FORMAT:\n"
            for instruction in output_instructions:
                prompt += f"- {instruction}\n"
            prompt += "\n"
        
        prompt += f"Context:\n{context}\n\n"
        prompt += f"Conversation History:\n{history if history else 'This is the start of the conversation.'}\n\n"
        prompt += f"Question: {user_query}\n\n"
        prompt += "Answer:"
    
    return prompt

    
def get_response(user_query, history=None):
    """
    Get a response from the chatbot based on the user query.
    """
    #if user_query.lower() in ["exit", "quit"]:
        #memory.add_turn("User", user_query)
        #memory.add_turn("Bot", "Goodbye!")
        #return "Goodbye!"

    # Step 0: Detect intent
    intent, confidence = detect_intent(user_query)
    #memory.add_turn("User", user_query)
    if intent == "escalate" and confidence > 0.7:
        #memory.add_turn("Bot", "Escalating to a human agent...")
        return "Escalating to a counsellor..."

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
    response = get_response(user_query)
    # Optionally, you can return the history as well for debugging or display
    # full_history = memory.get_history()
    return response
  
with gr.Blocks() as demo:
    gr.ChatInterface(
        fn=chat_interface,
        title="RAG Chatbot Demo",
        description="Ask questions about abortion.",
        theme="soft",
        examples=["What is abortion?", "What is safe abortion?", "What are the risks of abortion?"]
    )

if __name__ == "__main__":
    print("Starting the chatbot interface...")
    # Launch the Gradio interface
    demo.launch()
    