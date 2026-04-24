# 🤖 AutoStream AI Agent

Intelligent conversational AI agent for the AutoStream video editing platform. This project implements a "Social-to-Lead" agentic workflow using a RAG-based knowledge retrieval system and automated lead capture.

---

## 🎥 Demo Video

**Watch the project demonstration here:** [Google Drive Video Link](INSERT_YOUR_DRIVE_LINK_HERE)

---

## 🚀 How to Run Locally

### Prerequisites
- **Python 3.9+**
- **Node.js 18+**
- [uv](https://github.com/astral-sh/uv) (Recommended) or `pip`

### 1. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and configure your environment variables:
   ```bash
   cp .env.example .env
   # Add your OPENAI_API_KEY or GEMINI_API_KEY
   ```
3. Install dependencies and run:
   ```bash
   uv sync
   uv run main.py
   ```
   *The API will be available at `http://localhost:8000`*

### 2. Frontend Setup
1. From the root directory, install dependencies:
   ```bash
   npm install
   ```
2. Run the development server:
   ```bash
   npm run dev
   ```
   *The interface will be available at `http://localhost:3000`*

---

## 🏗️ Architecture Explanation

We chose **LangGraph** for this project because it provides a granular, state-driven approach to building agentic workflows, which is superior to standard linear chains. Unlike basic LLM wrappers, LangGraph allows us to define a directed acyclic graph (DAG) where nodes represent distinct processing steps like intent detection, RAG retrieval, and tool execution. This architecture is particularly effective for "Social-to-Lead" workflows where the agent must evaluate user input at each step before deciding whether to retrieve information or trigger a lead capture tool.

State management is handled using LangGraph’s built-in `StateGraph` and `MemorySaver` checkpointer. We defined a custom `AgentState` typed dictionary that tracks the complete conversation history, currently detected intent, and extracted lead information (name, email, platform). By utilizing an in-memory SQLite checkpointer, the agent successfully retains memory across **5-6+ conversation turns**. This allows the agent to maintain context—for example, remembering a user's specific editing needs mentioned in the first message while answering a detailed pricing question five turns later. This stateful persistence ensures a seamless and professional user experience, as the agent can handle multi-turn dialogues without losing context or requiring redundant inputs, fulfilling the mandatory requirement for robust, multi-turn session memory management.

---

## 📱 WhatsApp Deployment (Webhooks)

To integrate this agent with WhatsApp using Webhooks, the following architecture would be implemented:

1.  **Webhook Endpoint**: Deploy the FastAPI backend to a publicly accessible server and create a dedicated endpoint (e.g., `/webhook/whatsapp`) to receive incoming HTTP POST requests from the WhatsApp Business API.
2.  **Payload Extraction**: When a message is received, the backend parses the JSON payload to extract the `from` (sender's phone number) and the `body` (message text).
3.  **State Linking**: The sender's phone number is used as the `thread_id` or `session_id` within our LangGraph persistence layer. This ensures that when the agent processes the message, it automatically retrieves the specific conversation history for that user.
4.  **Automated Response**: Once the agent generates a response, the backend calls the WhatsApp Cloud API's `messages` endpoint to send the text back to the user's phone number.
5.  **Media Handling**: For a production environment, the webhook would also handle media IDs, allowing the agent to process images or videos sent via WhatsApp.

---

## 🛠️ Technical Stack

- **Language**: Python 3.9+
- **Framework**: LangGraph (LangChain)
- **LLM**: Gemini 1.5 Flash / GPT-4o-mini
- **Vector Store**: FAISS (for RAG pipeline)
- **API**: FastAPI
- **Frontend**: Next.js 15 + TailwindCSS
