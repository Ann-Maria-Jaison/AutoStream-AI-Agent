# AutoStream AI Agent Backend

A production-ready conversational AI agent for lead generation and customer support, built with LangGraph and FastAPI.

## Features

- **Intent Detection**: Classifies user messages into 5 intent categories (greeting, product inquiry, pricing, platform, high-intent lead)
- **RAG-Powered Knowledge Retrieval**: Answers questions using a local vector database of product knowledge
- **Stateful Conversation Management**: Maintains conversation history across 5+ turns using LangGraph
- **Lead Capture**: Collects and stores user details when high intent is detected
- **REST API**: FastAPI server with CORS support for frontend integration

## Quick Start

### 1. Setup Environment

```bash
cd backend
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Install Dependencies

```bash
uv add langchain langgraph langchain-openai langchain-community python-dotenv pydantic fastapi uvicorn psycopg2-binary aiohttp
```

Or use the pre-configured `pyproject.toml`:
```bash
uv sync
```

### 3. Run the Server

```bash
uv run main.py
```

The server will start at `http://localhost:8000`

## API Endpoints

### Chat Endpoint
```bash
POST /chat
Content-Type: application/json

{
  "message": "Tell me about your pricing",
  "session_id": "user123",
  "user_name": "John Doe",
  "user_email": "john@example.com",
  "user_platform": "YouTube"
}
```

Response:
```json
{
  "status": "success",
  "response": "AutoStream offers two plans...",
  "intent": "pricing_question",
  "lead_captured": false,
  "user_name": "John Doe",
  "user_email": "john@example.com",
  "user_platform": "YouTube"
}
```

### Lead Capture Endpoint
```bash
POST /lead-capture?name=John&email=john@example.com&platform=YouTube
```

### Statistics Endpoint
```bash
GET /stats
```

Returns total leads and last capture timestamp.

### Health Check
```bash
GET /health
```

## Architecture

### Technology Stack

- **Framework**: LangGraph (for agent orchestration and state management)
- **LLM**: OpenAI GPT-4o-mini (for reasoning, intent detection, and response generation)
- **Vector Store**: FAISS with OpenAI embeddings (for RAG)
- **Server**: FastAPI with Uvicorn
- **State Management**: In-memory with JSON persistence

### Why LangGraph?

LangGraph was chosen because it provides:

1. **Explicit State Management**: The `AgentState` model clearly defines conversation context, intent, and user details
2. **Workflow Orchestration**: The state graph allows conditional routing based on detected intent, ensuring proper conversation flow
3. **Memory Across Turns**: The `MemorySaver` checkpoint ensures conversation history persists across multiple turns without losing context
4. **Tool Calling Support**: Built-in support for function calling (used for lead capture)
5. **Production-Ready**: Designed for deployment with proper error handling and state serialization

### Agent Flow

```
User Message
    ↓
[Detect Intent] → Route based on intent
    ↓
    ├─→ High-Intent Lead → [Request Lead Details] → [Capture Lead] → [Respond]
    ├─→ Product Query → [Process Message + RAG] → [Respond]
    └─→ Greeting → [Respond]
    ↓
Response to User
```

### State Management

The agent maintains state across conversation turns:

```python
class AgentState:
    messages: List[BaseMessage]  # Full conversation history
    intent: str                   # Latest detected intent
    user_name: str               # Collected from user
    user_email: str              # Collected from user
    user_platform: str           # Collected from user
    lead_captured: bool          # Track capture status
    context: str                 # Retrieved knowledge
```

This enables the agent to:
- Remember previous messages (no repetition)
- Maintain context about which details have been collected
- Prevent duplicate lead captures
- Provide personalized responses

## Demo

Run the interactive demo:

```bash
uv run demo.py
```

This demonstrates:
1. Greeting and initial inquiry
2. Pricing question with RAG retrieval
3. High-intent detection
4. Lead detail collection
5. Lead capture confirmation

## Knowledge Base

The knowledge base (`knowledge_base.json`) contains:

- **Product Info**: Name, description, tagline
- **Pricing Plans**: Basic ($29/month) and Pro ($79/month) with features
- **Features**: AI captions, auto-cut, color grading, audio cleanup, batch export, story agent
- **Policies**: Refund policy, support availability, trial information

To update the knowledge base, edit `knowledge_base.json` and the RAG module will automatically reindex.

## Lead Storage

Captured leads are stored in `leads.json` with the following structure:

```json
[
  {
    "name": "John Doe",
    "email": "john@example.com",
    "platform": "YouTube",
    "timestamp": "2024-04-24T10:30:45.123456"
  }
]
```

## WhatsApp Integration Guide

To integrate this agent with WhatsApp using webhooks:

### 1. Setup Webhook Endpoint

Create an endpoint that receives WhatsApp webhook events:

```python
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: dict):
    # Extract message from WhatsApp webhook
    message = request["messages"][0]["text"]["body"]
    phone_number = request["messages"][0]["from"]
    
    # Process with agent
    result = agent.chat(message, session_id=phone_number)
    
    # Send response back via WhatsApp API
    send_whatsapp_message(phone_number, result["response"])
    
    return {"status": "success"}
```

### 2. Use Phone Number as Session ID

Each WhatsApp user has a unique phone number that serves as the session ID, maintaining conversation history per user.

### 3. Handle Media Messages

Extend the agent to handle images/videos by:
- Processing media URLs from WhatsApp webhook
- Adding vision capabilities to analyze images
- Storing media attachments with lead data

### 4. Deploy to Production

- Use ngrok for local testing: `ngrok http 8000`
- Deploy FastAPI server to production (Vercel, AWS Lambda, etc.)
- Register webhook URL with WhatsApp Business API
- Set webhook token for security

### 5. Response Formatting

Format responses for WhatsApp:
- Keep messages under 1000 characters
- Use line breaks for readability
- Include buttons/quick replies for common actions
- Queue messages to respect rate limits

## Database Integration (Future)

To add PostgreSQL persistence:

1. Create tables from SQL schema
2. Update `lead_capture.py` to use async SQLAlchemy
3. Implement user session storage in PostgreSQL
4. Enable persistent conversation history

```sql
CREATE TABLE leads (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  email VARCHAR(255),
  platform VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE conversations (
  id SERIAL PRIMARY KEY,
  session_id VARCHAR(255),
  messages JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Environment Variables

Required:
- `OPENAI_API_KEY`: Your OpenAI API key

Optional:
- `PORT`: Server port (default: 8000)
- `DATABASE_URL`: PostgreSQL connection string
- `ENVIRONMENT`: "development" or "production"

## Testing

To test the agent locally:

```bash
# Start the server
uv run main.py

# In another terminal, test the API
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about AutoStream"}'
```

## Deployment

### To Vercel

```bash
# Ensure you have a vercel.json config
vercel deploy
```

### To AWS Lambda

```bash
# Create serverless handler wrapper
pip install mangum
# Deploy with serverless framework or AWS SAM
```

### To Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Code Structure

```
backend/
├── main.py                 # FastAPI server and routes
├── agent.py               # LangGraph agent implementation
├── intent_detector.py     # Intent classification
├── rag.py                 # Vector store and retrieval
├── lead_capture.py        # Lead storage and management
├── knowledge_base.json    # Product knowledge
├── demo.py                # Interactive demo
├── README.md              # This file
└── .env.example           # Environment variables template
```

## Error Handling

The agent includes comprehensive error handling:

- **Invalid emails**: Pydantic validation prevents bad email addresses
- **API failures**: Fallback detection uses keyword-based intent classification
- **RAG retrieval errors**: Falls back to keyword search or default response
- **Missing API keys**: Clear error messages with setup instructions

## Performance Considerations

- **Conversation History**: Stored in memory per session (scales to ~100 concurrent users per instance)
- **Vector Embeddings**: Cached after initial load, ~50ms retrieval time
- **LLM Calls**: ~1-2 seconds per message (rate limited by OpenAI)
- **Concurrent Requests**: Use Uvicorn workers for parallel processing

## Support

For issues or questions:
1. Check the demo script for usage examples
2. Review the API endpoint documentation
3. Check OpenAI API status and rate limits
4. Ensure OPENAI_API_KEY is correctly set

## License

This project is part of the ServiceHive ML internship assignment.
