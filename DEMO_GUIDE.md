# 🎬 Demo Recording Guide

Follow this script to record your 2-3 minute demo video for the ServiceHive assignment. This ensures you hit all the evaluation criteria.

## 📍 Preparation
1. Start the backend: `cd backend && uv run main.py`
2. Start the frontend: `npm run dev`
3. Open `http://localhost:3000` in your browser.

---

## 🎭 The Script

### 1. Introduction (15s)
- Briefly show the UI.
- "Hi, this is [Your Name]. Today I'm demoing the AutoStream AI Agent built for the ServiceHive assignment using LangGraph and RAG."

### 2. Greeting & RAG Knowledge (45s)
- **Type**: `Hi! Tell me about your pricing plans.`
- **Action**: Show the agent retrieving info from the knowledge base.
- **Explain**: "The agent detected a pricing inquiry and used RAG to pull accurate data from our local knowledge base. It shows the Basic Plan at $29 and the Pro Plan at $79."
- **Follow-up**: `Does the Pro plan include 4K?`
- **Explain**: "The agent maintains context across turns to confirm feature details."

### 3. Intent Shift (30s)
- **Type**: `That sounds perfect. I want to sign up for the Pro plan for my YouTube channel.`
- **Action**: Agent should respond by asking for your name.
- **Explain**: "I've now shown high intent. The agent correctly identified the 'High Intent Lead' category and started the lead capture workflow using LangGraph nodes."

### 4. Lead Collection (45s)
- **Type**: `[Your Name]`
- **Action**: Agent asks for email.
- **Type**: `[Your Email]`
- **Action**: Agent asks for platform.
- **Type**: `YouTube`
- **Explain**: "The agent is collecting the three mandatory fields: Name, Email, and Platform. It will NOT trigger the tool until all three are provided."

### 5. Tool Execution (30s)
- **Action**: After you provide the platform, the agent should confirm capture.
- **Explain**: "Now that all details are collected, the `mock_lead_capture` function was triggered. If you check the terminal, you'll see the success message printed as required by the assignment."
- **Action**: (Optional) Quickly switch to the terminal to show `Lead captured successfully: ...`.

### 6. Conclusion (15s)
- "The agent successfully managed state across 6+ turns, utilized a RAG pipeline, and executed tool logic only when qualified. Thank you!"

---

## 💡 Technical Highlights to Mention
- "Built using **LangGraph** for robust state management."
- "Implements a **Hybrid LLM** strategy for 100% reliability."
- "Uses **FAISS** for semantic knowledge retrieval."
