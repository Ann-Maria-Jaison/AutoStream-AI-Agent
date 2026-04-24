"""
Conversation Manager - Simple session-based state tracking
Fixes the conversation flow issue by maintaining proper state.
"""

import random
from typing import Dict, Any
from hybrid_llm import get_hybrid_llm
from rag import get_knowledge_base
from lead_capture import get_lead_manager

# Global session storage
sessions: Dict[str, Dict[str, Any]] = {}

class ConversationManager:
    """Manages conversation state and flow logic."""
    
    def __init__(self):
        self.hybrid_llm = get_hybrid_llm()
        self.knowledge_base = get_knowledge_base()
        self.lead_manager = get_lead_manager()
    
    def process_message(self, message: str, session_id: str) -> Dict[str, Any]:
        """
        Process message with proper conversation state tracking.
        
        Args:
            message: User message
            session_id: Unique session identifier
            
        Returns:
            Dict with response and metadata
        """
        # Initialize session if needed
        if session_id not in sessions:
            sessions[session_id] = {
                "step": "start",
                "data": {},
                "conversation_count": 0
            }
        
        state = sessions[session_id]
        step = state["step"]
        state["conversation_count"] += 1
        
        # Step-based conversation flow
        if step == "start":
            return self._handle_start(state, message)
        
        elif step == "ask_name":
            return self._handle_ask_name(state, message)
        
        elif step == "ask_email":
            return self._handle_ask_email(state, message)
        
        elif step == "ask_platform":
            return self._handle_ask_platform(state, message, session_id)
        
        else:  # normal conversation
            return self._handle_normal_conversation(state, message)
    
    def _handle_start(self, state: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Handle the start of conversation."""
        # Detect intent
        intent_result = self.hybrid_llm.classify_intent(message)
        intent = intent_result["intent"]
        
        if intent == "greeting":
            state["step"] = "normal"
            return {
                "response": self._get_greeting_response(),
                "intent": intent,
                "step": state["step"],
                "lead_captured": False
            }
        
        elif intent == "high_intent_lead":
            state["step"] = "ask_name"
            # Personalize based on plan selection
            plan_name = "Basic Plan"
            if "pro" in message.lower():
                plan_name = "Pro Plan"
            
            state["data"]["plan"] = plan_name
            plan_mention = f" the {plan_name}" if plan_name else ""
                
            return {
                "response": f"Okay, fine, let's go with{plan_mention}! What's your name?",
                "intent": intent,
                "step": state["step"],
                "lead_captured": False
            }
        
        else:  # pricing, platform, product, inquiry, or general
            state["step"] = "normal"
            return self._handle_normal_conversation(state, message)
    
    def _handle_ask_name(self, state: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Handle name collection step."""
        state["data"]["name"] = message.strip()
        state["step"] = "ask_email"
        
        return {
            "response": "Your email?",
            "intent": "high_intent_lead",
            "step": state["step"],
            "lead_captured": False
        }
    
    def _handle_ask_email(self, state: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Handle email collection step."""
        email = message.strip()
        
        # Basic email validation
        if "@" not in email or "." not in email:
            return {
                "response": "That doesn't look like a valid email. Could you provide your email address?",
                "intent": "high_intent_lead",
                "step": state["step"],
                "lead_captured": False
            }
        
        state["data"]["email"] = email
        state["step"] = "ask_platform"
        
        return {
            "response": "Which platform?",
            "intent": "high_intent_lead",
            "step": state["step"],
            "lead_captured": False
        }
    
    def _handle_ask_platform(self, state: Dict[str, Any], message: str, session_id: str) -> Dict[str, Any]:
        """Handle platform collection and lead capture."""
        state["data"]["platform"] = message.strip()
        
        # Capture the lead
        try:
            result = self.lead_manager.capture_lead(
                state["data"]["name"],
                state["data"]["email"], 
                state["data"]["platform"],
                state["data"].get("plan", "Basic Plan")
            )
            
            if result.get("status") == "success":
                # Clear session state (conversation complete)
                sessions.pop(session_id, None)
                
                return {
                    "response": result.get("message", "You're all set! We'll contact you soon."),
                    "intent": "high_intent_lead",
                    "step": "complete",
                    "lead_captured": True,
                    "lead_data": state["data"]
                }
            else:
                return {
                    "response": f"I had trouble saving your information: {result.get('message')}. Could you try again?",
                    "intent": "high_intent_lead",
                    "step": state["step"],
                    "lead_captured": False
                }
            
        except Exception as e:
            return {
                "response": "I had trouble saving your information. Could you try again or contact support?",
                "intent": "high_intent_lead",
                "step": state["step"],
                "lead_captured": False,
                "error": str(e)
            }
    
    def _handle_normal_conversation(self, state: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Handle normal conversation with RAG and intent detection."""
        # Detect intent
        intent_result = self.hybrid_llm.classify_intent(message)
        intent = intent_result["intent"]
        
        # Check if this is a high-intent message during normal conversation
        if intent == "high_intent_lead":
            state["step"] = "ask_name"
            # Personalize based on plan selection
            plan_name = "Basic Plan"
            if "pro" in message.lower():
                plan_name = "Pro Plan"
            
            state["data"]["plan"] = plan_name
            plan_mention = f" the {plan_name}" if plan_name else ""

            return {
                "response": f"Okay, fine, let's go with{plan_mention}! What's your name?",
                "intent": intent,
                "step": state["step"],
                "lead_captured": False
            }
        
        # Use RAG for knowledge-based responses
        rag_result = self.knowledge_base.generate_response(message)
        
        return {
            "response": rag_result["response"],
            "intent": intent,
            "step": state["step"],
            "lead_captured": False,
            "rag_used": rag_result["context_used"]
        }
    
    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get current session state for debugging."""
        return sessions.get(session_id, {"step": "none", "data": {}})
    
    def _get_greeting_response(self) -> str:
        """Get a human-like greeting response with variation."""
        responses = [
            "Hey! I can help you with AutoStream. What would you like to know?",
            "Hi! Looking for pricing or features?",
            "Hello! I'm here to help you with AutoStream."
        ]
        return random.choice(responses)
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a session."""
        return sessions.pop(session_id, None) is not None

# Global instance
conversation_manager = ConversationManager()

def get_conversation_manager() -> ConversationManager:
    """Get the global conversation manager instance."""
    return conversation_manager
