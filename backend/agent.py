"""
AutoStream AI Agent - LangGraph Implementation
Implementing a proper state-based agentic workflow as per assignment requirements.
"""

import operator
from typing import Annotated, Dict, List, TypedDict, Union, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from intent_detector import get_intent_detector, Intent
from rag import get_knowledge_base
from lead_capture import get_lead_manager, mock_lead_capture

# Define the state for our agent
class AgentState(TypedDict):
    messages: Annotated[List[Dict[str, str]], operator.add]
    intent: Optional[str]
    user_data: Dict[str, str]
    current_step: str
    response: Optional[str]
    lead_captured: bool

class LangGraphAgent:
    """
    AutoStream AI Agent using LangGraph for state management and workflow.
    """
    
    def __init__(self):
        self.intent_detector = get_intent_detector()
        self.knowledge_base = get_knowledge_base()
        self.lead_manager = get_lead_manager()
        
        # Build the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("process_input", self.process_input)
        workflow.add_node("retrieve_knowledge", self.retrieve_knowledge)
        workflow.add_node("lead_workflow", self.lead_workflow)
        
        # Set entry point
        workflow.set_entry_point("process_input")
        
        # Add edges
        workflow.add_conditional_edges(
            "process_input",
            self.route_after_input,
            {
                "knowledge": "retrieve_knowledge",
                "lead": "lead_workflow",
                "end": END
            }
        )
        
        workflow.add_edge("retrieve_knowledge", END)
        workflow.add_edge("lead_workflow", END)
        
        # Compile with memory persistence
        self.memory = MemorySaver()
        self.app = workflow.compile(checkpointer=self.memory)
    
    def process_input(self, state: AgentState):
        """Node to process input and detect intent."""
        last_message = state["messages"][-1]["content"]
        
        # Detect intent
        intent_result = self.intent_detector.detect(last_message)
        intent = intent_result.intent
        
        # If we are in the middle of lead collection, force high_intent_lead logic
        if state["current_step"] in ["ask_name", "ask_email", "ask_platform"]:
            intent = Intent.HIGH_INTENT_LEAD
            
        return {
            "intent": intent,
            "current_step": "processed"
        }
    
    def route_after_input(self, state: AgentState):
        """Route based on detected intent."""
        intent = state["intent"]
        
        if intent == Intent.HIGH_INTENT_LEAD or state["current_step"] in ["ask_name", "ask_email", "ask_platform"]:
            return "lead"
        elif intent in [Intent.PRICING_QUESTION, Intent.PRODUCT_INQUIRY, Intent.PLATFORM_QUESTION]:
            return "knowledge"
        else:
            return "knowledge" # Default to knowledge/greeting
            
    def retrieve_knowledge(self, state: AgentState):
        """Node to retrieve information from RAG."""
        last_message = state["messages"][-1]["content"]
        rag_result = self.knowledge_base.generate_response(last_message)
        
        return {
            "response": rag_result["response"],
            "current_step": "answered"
        }
    
    def lead_workflow(self, state: AgentState):
        """Node to handle lead collection logic."""
        last_message = state["messages"][-1]["content"]
        user_data = state["user_data"].copy()
        current_step = state["current_step"]
        
        # Logic to progress through lead capture steps
        if "name" not in user_data:
            # Check if we just asked for name or if this is the start
            if any(msg["content"].endswith("name?") for msg in state["messages"][-5:] if msg["role"] == "assistant"):
                user_data["name"] = last_message.strip()
                response = "Great! And what is your email address?"
                new_step = "ask_email"
            else:
                response = "I'd love to help you get started with AutoStream! First, what is your name?"
                new_step = "ask_name"
        
        elif "email" not in user_data:
            # Validate email simply
            if "@" not in last_message or "." not in last_message:
                response = "That doesn't look like a valid email. Please provide your email address."
                new_step = "ask_email"
            else:
                user_data["email"] = last_message.strip()
                response = "Got it. And which platform do you primarily create for (e.g., YouTube, Instagram)?"
                new_step = "ask_platform"
                
        elif "platform" not in user_data:
            user_data["platform"] = last_message.strip()
            # WE HAVE ALL THREE! Trigger the tool.
            mock_lead_capture(user_data["name"], user_data["email"], user_data["platform"])
            # Also call the manager for storage
            self.lead_manager.capture_lead(user_data["name"], user_data["email"], user_data["platform"])
            
            response = f"Thank you, {user_data['name']}! I've successfully captured your details for {user_data['platform']}. We'll be in touch at {user_data['email']} very soon!"
            new_step = "complete"
            return {
                "response": response,
                "user_data": user_data,
                "current_step": new_step,
                "lead_captured": True
            }
        else:
            response = "You're already all set up! Is there anything else I can help with?"
            new_step = "complete"

        return {
            "response": response,
            "user_data": user_data,
            "current_step": new_step,
            "lead_captured": False
        }

class AutoStreamAgent:
    """Wrapper class to maintain existing API but use LangGraph backend."""
    
    def __init__(self):
        self.agent = LangGraphAgent()
        
    def chat(self, user_message: str, session_id: str = "default") -> dict:
        # Prepare input state
        config = {"configurable": {"thread_id": session_id}}
        
        # Get existing state or initialize
        state = self.agent.app.get_state(config).values
        if not state:
            state = {
                "messages": [],
                "intent": None,
                "user_data": {},
                "current_step": "start",
                "response": None,
                "lead_captured": False
            }
            
        # Add user message
        state["messages"].append({"role": "user", "content": user_message})
        
        # Run the graph
        final_state = self.agent.app.invoke(state, config)
        
        # Add assistant message to history
        self.agent.app.update_state(config, {"messages": [{"role": "assistant", "content": final_state["response"]}]})
        
        return {
            "status": "success",
            "response": final_state["response"],
            "intent": final_state["intent"],
            "lead_captured": final_state["lead_captured"],
            "step": final_state["current_step"]
        }

# Global agent instance
_agent = None

def get_agent() -> AutoStreamAgent:
    global _agent
    if _agent is None:
        _agent = AutoStreamAgent()
    return _agent
