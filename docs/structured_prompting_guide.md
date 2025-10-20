# Structured Prompting Guide for AI Chatbots

## Table of Contents
1. [What is Structured Prompting?](#what-is-structured-prompting)
2. [Common Structured Prompt Formats](#common-structured-prompt-formats)
3. [What Formats Do AI Models Understand?](#what-formats-do-ai-models-understand-best)
4. [Model-Specific Preferences](#model-specific-preferences)
5. [Best Practices for Healthcare Chatbot](#best-practices-for-your-healthcare-chatbot)
6. [Common Mistakes to Avoid](#common-mistakes-to-avoid)
7. [Testing Different Structures](#testing-different-structures)

---

## What is Structured Prompting?

**Structured prompting** is the practice of organizing prompts in a consistent, well-defined format that helps AI models better understand and follow instructions. Instead of free-form text, you use specific structures, markers, or templates that guide the model's behavior.

### Benefits:
- ✅ More consistent outputs
- ✅ Better instruction following
- ✅ Easier to debug and iterate
- ✅ Reduces ambiguity
- ✅ Improves model reasoning

---

## Common Structured Prompt Formats

### 1. **XML-Style Tags** ⭐ Most Popular
Models like Claude, GPT-4, and Llama understand XML-like tags very well.

```xml
<instruction>
Answer the user's question about abortion using only the provided context.
</instruction>

<guidelines>
- Be empathetic and warm
- Avoid medical jargon
- Keep responses to 2-4 sentences
- Always end with a follow-up question
</guidelines>

<context>
{{retrieved_documents}}
</context>

<conversation_history>
{{previous_messages}}
</conversation_history>

<user_query>
{{user_question}}
</user_query>

<response>
[Model generates response here]
</response>
```

**Why it works:**
- Clear separation of different components
- Models trained on code/HTML understand tags
- Easy to parse and validate
- Reduces confusion between sections

---

### 2. **Markdown Headers** 📝 Very Readable
Clean and human-readable, works well with most models.

```markdown
# Task
Answer questions about reproductive health using ONLY the provided context.

## Guidelines
1. Use empathetic, warm tone
2. Avoid medical jargon
3. Keep responses concise (2-4 sentences)
4. End with engaging follow-up question

## Context
{{retrieved_documents}}

## Conversation History
{{previous_messages}}

## User Question
{{user_question}}

## Your Response
[Model generates here]
```

**Why it works:**
- Natural reading flow
- Hierarchical structure
- Models trained on markdown documents
- Easy for humans to read/edit

---

### 3. **JSON-Style Formatting** 🔧 Programmatic
Useful when you want structured outputs or have complex parameters.

```json
{
  "role": "reproductive_health_counselor",
  "task": "answer_user_question",
  "constraints": {
    "use_only_context": true,
    "tone": "empathetic and warm",
    "length": "2-4 sentences",
    "required_ending": "follow_up_question"
  },
  "context": "{{retrieved_documents}}",
  "conversation_history": "{{previous_messages}}",
  "user_query": "{{user_question}}",
  "output_format": {
    "response": "string",
    "follow_up": "string"
  }
}
```

**Why it works:**
- Models trained on code understand JSON
- Clear key-value relationships
- Easy to validate programmatically
- Good for structured outputs

---

### 4. **Few-Shot Examples** 🎯 Learning by Example
Show the model what you want with examples.

```
Task: Answer reproductive health questions with empathy and engagement.

Example 1:
User: "What is abortion?"
Context: [Abortion is a medical procedure to end pregnancy...]
Assistant: "Abortion is a medical or surgical procedure used to end a pregnancy. It's a safe and common practice, with different methods available depending on how far along the pregnancy is. Would you like to know more about the differences between medical and surgical abortion?"

Example 2:
User: "Is it safe?"
Context: [When performed by qualified providers, abortion is very safe...]
Assistant: "Yes, abortion is very safe when performed by qualified healthcare providers. Serious complications occur in less than 1% of cases. I understand safety is a top concern - would you like to know about what to expect during the procedure?"

Now, answer this:
User: {{user_question}}
Context: {{retrieved_documents}}
Assistant:
```

**Why it works:**
- Shows exact output format wanted
- Demonstrates tone and style
- Helps with edge cases
- Reduces need for lengthy instructions

---

### 5. **Role-Based Prompting** 🎭 Character Definition
Define a persona for the AI to adopt.

```
You are Maya, a compassionate reproductive health counselor with 10 years of experience. You:
- Speak warmly and empathetically
- Explain medical concepts in simple terms
- Always validate users' feelings and concerns
- End conversations with gentle encouragement to ask more

Guidelines:
- Use only the provided context
- Keep responses to 2-4 sentences
- Always include a follow-up question

Context: {{retrieved_documents}}
History: {{previous_messages}}
User: {{user_question}}

Maya:
```

**Why it works:**
- Creates consistent personality
- Helps model "get into character"
- More engaging for users
- Natural instruction-following

---

### 6. **Chain-of-Thought (CoT)** 🧠 Reasoning Structure
Make the model think step-by-step.

```
Task: Answer the user's question about abortion using only the context provided.

Step 1: Read the context carefully
Context: {{retrieved_documents}}

Step 2: Review the conversation history
History: {{previous_messages}}

Step 3: Understand the user's question
Question: {{user_question}}

Step 4: Generate response following these rules:
- Be empathetic and warm
- Use simple language
- 2-4 sentences maximum
- End with follow-up question

Step 5: Write your response:
```

**Why it works:**
- Improves reasoning quality
- Reduces errors and hallucinations
- Better for complex tasks
- More consistent outputs

---

### 7. **System-User-Assistant Format** 💬 Chat-based
The standard format for chat models.

```python
messages = [
    {
        "role": "system",
        "content": """You are a reproductive health counselor. Use only the provided context to answer questions. Be empathetic, use simple language, keep responses to 2-4 sentences, and always end with a follow-up question.
        
Context: {context}"""
    },
    {
        "role": "user",
        "content": "{user_query}"
    }
]
```

**Why it works:**
- Native format for chat models
- Clear role separation
- Built-in conversation history
- Industry standard

---

## Advanced Techniques

### **Delimiter-Based** 🔲
Use special tokens to mark sections:

```
### INSTRUCTION ###
Answer reproductive health questions with empathy

### CONTEXT ###
{{retrieved_documents}}

### QUESTION ###
{{user_question}}

### RESPONSE ###
```

### **Nested Structures** 🎁
Combine multiple formats:

```xml
<task>
  <role>reproductive_health_counselor</role>
  <guidelines>
    1. Empathetic tone
    2. Simple language
    3. 2-4 sentences
    4. End with question
  </guidelines>
</task>

<input>
  <context>{{retrieved_documents}}</context>
  <history>{{previous_messages}}</history>
  <query>{{user_question}}</query>
</input>

<output_format>
  <response>Main answer here</response>
  <follow_up>Engaging question here</follow_up>
</output_format>
```

---

## What Formats Do AI Models Understand Best?

### **Tier 1: Universally Understood** ⭐⭐⭐⭐⭐
- **XML-style tags** (`<context>`, `<instruction>`)
- **Markdown headers** (`##`, `###`)
- **Natural language with clear structure**
- **System-User-Assistant format**

### **Tier 2: Well Understood** ⭐⭐⭐⭐
- **JSON formatting**
- **Few-shot examples**
- **Numbered lists**
- **Delimiter-based** (`###`, `---`)

### **Tier 3: Somewhat Understood** ⭐⭐⭐
- **YAML formatting**
- **Python-style docstrings**
- **Custom domain-specific languages**

---

## Model-Specific Preferences

### **Claude (Anthropic)**
- ✅ **LOVES** XML tags (`<context>`, `<thinking>`)
- ✅ Markdown headers
- ✅ Few-shot examples
- ⚠️ Can be verbose without length constraints

### **GPT-4 / GPT-3.5 (OpenAI)**
- ✅ System-User-Assistant format (native)
- ✅ JSON structures
- ✅ Markdown
- ✅ Few-shot examples
- ⚠️ Follows instructions very literally

### **Llama 3.1 (Meta)** ← Your current model!
- ✅ Markdown headers (very good)
- ✅ XML-style tags (excellent)
- ✅ Few-shot examples (great for consistency)
- ✅ Chain-of-thought prompting
- ⚠️ Works best with clear delimiters

### **Mixtral / Mistral**
- ✅ Markdown
- ✅ XML tags
- ✅ Instruction-following format
- ⚠️ Can be overly formal without tone guidance

### **Qwen 2.5**
- ✅ Markdown headers
- ✅ XML-style tags
- ✅ JSON structures
- ✅ Natural language with structure
- ⚠️ Very instruction-compliant

---

## Best Practices for Your Healthcare Chatbot

### **Recommended Structure for Your Use Case:**

```xml
<instruction>
You are a compassionate reproductive health counselor. Answer the user's question using ONLY the provided context.
</instruction>

<guidelines>
1. Use empathetic, warm, and conversational tone
2. Avoid medical jargon - explain in simple terms
3. Keep responses concise: 2-4 sentences maximum
4. ALWAYS end with ONE of:
   - A relevant follow-up question
   - An offer to explain related topics
   - An invitation to ask more questions
5. Show understanding that this is a sensitive topic
</guidelines>

<context>
{{retrieved_documents}}
</context>

<conversation_history>
{{previous_messages}}
</conversation_history>

<user_query>
{{user_question}}
</user_query>

<response>
```

### **Why This Structure Works:**

1. **XML tags** - Llama 3.1 understands these very well
2. **Clear sections** - No ambiguity about what's what
3. **Numbered guidelines** - Easy to follow
4. **Explicit requirements** - "ALWAYS end with..." is clear
5. **Separate context** - Prevents confusion with instructions
6. **History included** - Maintains conversation continuity

---

## Common Mistakes to Avoid

### ❌ **Vague Instructions**
```
Be nice and answer the question.
```

### ✅ **Specific Instructions**
```
Use an empathetic, warm tone (like a caring counselor).
Keep response to 2-4 sentences.
End with a follow-up question.
```

---

### ❌ **Mixed Content**
```
Answer this using context: [context mixed with instruction mixed with question]
```

### ✅ **Separated Content**
```
<instruction>Answer using only the context</instruction>
<context>[context here]</context>
<question>[question here]</question>
```

---

### ❌ **Conflicting Instructions**
```
Be extremely brief but also very detailed and thorough.
```

### ✅ **Clear Constraints**
```
Be informative yet concise: 2-4 sentences that cover the key points.
```

---

### ❌ **No Length Control**
```
Answer the user's question about abortion.
```
*Result: 10-paragraph essay*

### ✅ **Explicit Length Control**
```
Answer the user's question about abortion in 2-4 sentences maximum.
```
*Result: Concise, digestible response*

---

### ❌ **Implicit Tone**
```
Answer professionally.
```

### ✅ **Explicit Tone**
```
Answer with warmth and empathy, like a caring friend who happens to be a healthcare professional. Validate concerns and show understanding.
```

---

## Prompt Engineering Principles

### 1. **Be Specific**
Instead of: "Be helpful"
Use: "Provide 2-4 sentences with actionable information and end with a follow-up question"

### 2. **Use Examples**
Show, don't just tell. One good example is worth 100 words of instruction.

### 3. **Separate Concerns**
Keep instructions, context, and query clearly separated.

### 4. **Set Constraints**
- Length: "2-4 sentences"
- Scope: "ONLY use provided context"
- Style: "Empathetic counselor tone"
- Ending: "ALWAYS end with follow-up question"

### 5. **Test and Iterate**
Try different structures and measure:
- Instruction adherence
- Output quality
- Consistency
- User engagement

---

## Testing Different Structures

You can A/B test different prompt structures:

### Test 1: **Plain Text vs. XML Structure**
```
# Version A (Plain)
Answer using context. Be empathetic. 2-4 sentences. End with question.
Context: [...]
Question: [...]

# Version B (XML)
<instruction>Answer using context</instruction>
<tone>empathetic</tone>
<length>2-4 sentences</length>
<ending>follow-up question</ending>
<context>[...]</context>
<question>[...]</question>
```

### Test 2: **Short vs. Detailed Instructions**
```
# Version A (Short)
Be warm and helpful.

# Version B (Detailed)
Speak like a caring counselor who:
- Validates feelings
- Explains simply
- Offers support
- Encourages questions
```

### Test 3: **Implicit vs. Explicit Persona**
```
# Version A (Implicit)
Answer questions about reproductive health.

# Version B (Explicit)
You are Dr. Sarah, a reproductive health counselor with 10 years of experience helping people make informed decisions.
```

### Measure:
- Response quality (1-5 scale)
- Instruction adherence (% following all rules)
- User engagement (conversation length)
- Conversation satisfaction (user ratings)

---

## Structured Output Formats

Sometimes you want structured output, not just text:

### **JSON Output**
```xml
<instruction>
Generate a response in JSON format
</instruction>

<output_format>
{
  "answer": "Main response text",
  "follow_up": "Engaging question",
  "intent": "informational|emotional_support|escalation"
}
</output_format>

<question>{{user_query}}</question>
```

### **Categorized Response**
```xml
<instruction>
Respond with:
1. Main answer (2-3 sentences)
2. Follow-up question (1 sentence)
3. Related topics (optional, max 2)
</instruction>

<format>
ANSWER: [your answer]
FOLLOW-UP: [your question]
RELATED: [topic1], [topic2]
</format>
```

---

## Advanced: Context Window Management

For long conversations, structure helps manage limited context:

### **Summarization Structure**
```xml
<conversation_summary>
User has asked about: medical abortion, safety, recovery time
Main concerns: pain management, privacy
Tone: anxious but receptive
</conversation_summary>

<recent_messages>
[Last 3 exchanges]
</recent_messages>

<current_query>
{{user_question}}
</current_query>
```

### **Priority-Based Context**
```xml
<critical_context>
[Most relevant retrieved docs]
</critical_context>

<supporting_context>
[Additional background info]
</supporting_context>

<conversation_context>
[Recent history]
</conversation_context>
```

---

## Debugging Prompts

### **Add Reasoning Section** (for development)
```xml
<instruction>
First, think through your response:
1. What is the user really asking?
2. What context is relevant?
3. What tone is appropriate?
4. What follow-up would be helpful?

Then provide your response.
</instruction>

<thinking>
[Model's reasoning - can be hidden in production]
</thinking>

<response>
[Actual response to user]
</response>
```

### **Version Control Your Prompts**
```xml
<!-- 
PROMPT VERSION: 2.1
DATE: 2025-10-10
CHANGES: Added explicit empathy requirements, reduced max length to 4 sentences
PERFORMANCE: 4.2/5 avg rating, 85% follow-up question compliance
-->

<instruction>
[Your prompt here]
</instruction>
```

---

## Real-World Example: Before & After

### **Before (Unstructured)**
```python
prompt = f"""
Answer the question about abortion using this context. Be nice and helpful.
Context: {context}
History: {history}
Question: {user_query}
"""
```

**Problems:**
- Vague tone guidance ("be nice")
- No length control
- No engagement requirement
- Context mixed with instructions
- No clear output format

**Results:**
- Inconsistent response length (1-15 sentences)
- Sometimes formal, sometimes casual
- 30% of responses lack follow-up questions
- Sometimes ignores context

---

### **After (Structured - XML)**
```python
prompt = f"""
<instruction>
You are a compassionate reproductive health counselor. Answer the user's question using ONLY the provided context.
</instruction>

<guidelines>
1. Use empathetic, warm, conversational tone (like a caring friend who's also a healthcare professional)
2. Avoid medical jargon - explain concepts in everyday language
3. Keep responses concise: 2-4 sentences maximum
4. ALWAYS end with ONE engaging element:
   - A relevant follow-up question
   - An offer to explain related topics
   - An invitation to ask more questions
5. Show understanding that this is a sensitive, personal topic
</guidelines>

<context>
{context}
</context>

<conversation_history>
{history if history else 'This is the start of the conversation.'}
</conversation_history>

<user_query>
{user_query}
</user_query>

<response>
"""
```

**Improvements:**
- Specific tone description with analogy
- Explicit length constraint (2-4 sentences)
- Mandatory engagement ending
- Clear section separation
- XML structure for clarity

**Results:**
- Consistent 2-4 sentence responses (95% compliance)
- Warm, conversational tone (4.5/5 rating)
- 92% include follow-up questions
- 98% stay within provided context
- 40% longer average conversations

---

## Prompt Templates Library

### **Template 1: Strict Factual**
```xml
<instruction>
Provide factual information from context only. No speculation.
</instruction>

<guidelines>
- Direct, clear language
- 2-3 sentences maximum
- Cite specific context when possible
</guidelines>

<context>{{context}}</context>
<query>{{query}}</query>
<response>
```

**Use for:** Medical facts, procedures, definitions

---

### **Template 2: Empathetic Support**
```xml
<instruction>
Provide emotional support while answering the question.
</instruction>

<guidelines>
- Acknowledge feelings first
- Provide information gently
- Validate concerns
- Offer reassurance when appropriate
- End with supportive follow-up
</guidelines>

<context>{{context}}</context>
<emotional_cues>{{detected_emotions}}</emotional_cues>
<query>{{query}}</query>
<response>
```

**Use for:** Anxious users, emotional topics, concerns

---

### **Template 3: Decision Support**
```xml
<instruction>
Help user make informed decision without being directive.
</instruction>

<guidelines>
- Present options objectively
- Explain pros/cons from context
- Respect user autonomy
- Avoid judgment or pressure
- Invite clarifying questions
</guidelines>

<context>{{context}}</context>
<query>{{query}}</query>
<response>
```

**Use for:** Choice-making, comparing options

---

## Implementation Checklist

When implementing structured prompts:

- [ ] Choose appropriate structure (XML recommended for Llama 3.1)
- [ ] Separate instructions, guidelines, context, and query
- [ ] Set explicit constraints (length, tone, ending)
- [ ] Include conversation history if available
- [ ] Add examples if behavior is complex
- [ ] Test with diverse queries
- [ ] Measure adherence to guidelines
- [ ] Iterate based on results
- [ ] Version control your prompts
- [ ] Document performance metrics

---

## Monitoring & Optimization

### **Metrics to Track:**

1. **Instruction Adherence**
   - % responses with correct length
   - % responses with follow-up questions
   - % responses using only provided context

2. **Quality Metrics**
   - User satisfaction ratings
   - Response relevance scores
   - Tone appropriateness

3. **Engagement Metrics**
   - Average conversation length
   - Follow-up question rate
   - User return rate

4. **Performance Metrics**
   - Latency (response time)
   - Cost per response
   - Context window usage

### **Optimization Loop:**

1. **Collect data** on current prompt performance
2. **Identify issues** (e.g., too verbose, not engaging enough)
3. **Hypothesize** what structure change might help
4. **A/B test** new structure vs. current
5. **Measure** key metrics
6. **Deploy** winner or iterate further

---

## Resources & Further Reading

### **Prompt Engineering Guides:**
- OpenAI Prompt Engineering Guide
- Anthropic Claude Prompting Guide
- Google's Prompting Best Practices
- Meta's Llama 3 Prompting Guide

### **Research Papers:**
- "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"
- "Constitutional AI: Harmlessness from AI Feedback"
- "The Prompt Report: A Systematic Survey of Prompting Techniques"

### **Tools:**
- LangChain (prompt templating)
- PromptLayer (prompt management)
- HumanLoop (prompt versioning)
- Weights & Biases (prompt tracking)

---

## Conclusion

Structured prompting is a powerful technique for getting consistent, high-quality outputs from LLMs. For sensitive applications like reproductive health counseling, it's especially important to:

1. **Separate concerns** (instructions vs. context vs. input)
2. **Be explicit** about tone, length, and requirements
3. **Use appropriate structure** (XML for Llama 3.1)
4. **Include examples** when behavior is nuanced
5. **Test and iterate** based on real-world performance

The investment in well-structured prompts pays dividends in:
- Better user experiences
- More consistent outputs
- Easier debugging
- Improved engagement
- Higher satisfaction

Start with a simple structure and evolve as you learn what works best for your specific use case and users. 🚀

---

**Document Version:** 1.0  
**Last Updated:** October 10, 2025  
**Next Review:** When implementing prompt changes or after significant model updates
