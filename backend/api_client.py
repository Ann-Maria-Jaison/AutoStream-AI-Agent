"""
Client helper for frontend integration with the AutoStream AI Agent backend.
This can be used as a reference or imported for backend-to-backend communication.
"""

import aiohttp
import asyncio
from typing import Optional, Dict, Any
import json


class AutoStreamAgentClient:
    """
    HTTP client for communicating with the AutoStream AI Agent backend.
    Useful for testing and frontend integration.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def chat(
        self,
        message: str,
        session_id: str = "default",
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        user_platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to the agent.
        
        Args:
            message: User message
            session_id: Session ID for conversation history
            user_name: Optional user name
            user_email: Optional user email
            user_platform: Optional creator platform
            
        Returns:
            Response dictionary
        """
        payload = {
            "message": message,
            "session_id": session_id,
            "user_name": user_name,
            "user_email": user_email,
            "user_platform": user_platform
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                return await response.json()
    
    async def capture_lead(
        self,
        name: str,
        email: str,
        platform: str
    ) -> Dict[str, Any]:
        """
        Manually capture a lead.
        
        Args:
            name: User name
            email: User email
            platform: Creator platform
            
        Returns:
            Capture result
        """
        params = {
            "name": name,
            "email": email,
            "platform": platform
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/lead-capture",
                params=params
            ) as response:
                return await response.json()
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get agent statistics.
        
        Returns:
            Statistics dictionary
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/stats") as response:
                return await response.json()
    
    async def get_knowledge(self) -> Dict[str, Any]:
        """
        Get the knowledge base.
        
        Returns:
            Knowledge base content
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/knowledge-base") as response:
                return await response.json()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check server health.
        
        Returns:
            Health status
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/health") as response:
                return await response.json()


# Frontend Integration Example (React/NextJS)
FRONTEND_INTEGRATION_EXAMPLE = """
// frontend/hooks/useAutoStreamAgent.ts
import { useState, useCallback } from 'react';

interface ChatMessage {
  role: 'user' | 'agent';
  content: string;
  intent?: string;
  leadCaptured?: boolean;
}

export function useAutoStreamAgent() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(`session_${Date.now()}`);
  
  const sendMessage = useCallback(async (message: string) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          session_id: sessionId
        })
      });
      
      const data = await response.json();
      
      setMessages(prev => [
        ...prev,
        { role: 'user', content: message },
        {
          role: 'agent',
          content: data.response,
          intent: data.intent,
          leadCaptured: data.lead_captured
        }
      ]);
      
      return data;
    } finally {
      setLoading(false);
    }
  }, [sessionId]);
  
  return { messages, loading, sendMessage };
}

// Usage in component
export function ChatInterface() {
  const { messages, loading, sendMessage } = useAutoStreamAgent();
  const [input, setInput] = useState('');
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    await sendMessage(input);
    setInput('');
  };
  
  return (
    <div>
      {messages.map((msg, i) => (
        <div key={i} className={msg.role}>
          {msg.content}
          {msg.leadCaptured && <p>✓ Lead captured!</p>}
        </div>
      ))}
      
      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          placeholder="Type your message..."
        />
        <button type="submit" disabled={loading}>Send</button>
      </form>
    </div>
  );
}
"""


# Async example usage
async def example_conversation():
    """Example of a complete conversation flow."""
    client = AutoStreamAgentClient()
    
    # Check server health
    health = await client.health_check()
    print(f"Server Health: {health}")
    
    # Start conversation
    messages = [
        "Hi, tell me about AutoStream",
        "What's the pricing for YouTube creators?",
        "That sounds great, I want to try the Pro plan"
    ]
    
    for msg in messages:
        print(f"\nUser: {msg}")
        response = await client.chat(msg, session_id="example")
        print(f"Agent: {response['response']}")
        
        if response.get('lead_captured'):
            print("✓ Lead captured!")


if __name__ == "__main__":
    # Run example conversation
    asyncio.run(example_conversation())
