"""
Hybrid LLM System - Smart Fallback Architecture

Primary: Gemini API (faster, cheaper)
Fallback 1: OpenAI API (reliable)
Fallback 2: Local rule-based logic (always works)

This creates a fault-tolerant system that's impressive in interviews.

For demo reliability: Set USE_API = False to use local mode only.
"""

import os
import logging
from typing import Optional, Dict, Any
from enum import Enum

import google.generativeai as genai
from openai import OpenAI

# 🎯 DEMO MODE: Set to False for reliable local-only demo
USE_API = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    LOCAL = "local"

class HybridLLM:
    """
    Hybrid LLM system with smart fallback logic.
    
    Architecture:
    1. Try Gemini API first (fast, cost-effective)
    2. Fallback to OpenAI if Gemini fails
    3. Final fallback to local rule-based logic
    """
    
    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize Gemini if key is available
        self.gemini_client = None
        if self.gemini_api_key and self.gemini_api_key != "your_gemini_api_key_here":
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_client = genai.GenerativeModel('gemini-pro')
                logger.info("✅ Gemini client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Gemini initialization failed: {e}")
        
        # Initialize OpenAI if key is available
        self.openai_client = None
        if self.openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                logger.info("✅ OpenAI client initialized")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI initialization failed: {e}")
    
    def _try_gemini(self, prompt: str, **kwargs) -> Optional[str]:
        """Try to get response from Gemini API."""
        if not self.gemini_client:
            return None
            
        try:
            logger.info("🚀 Trying Gemini API...")
            response = self.gemini_client.generate_content(prompt)
            
            if response.text:
                logger.info("✅ Gemini API successful")
                return response.text.strip()
            else:
                logger.warning("⚠️ Gemini returned empty response")
                return None
                
        except Exception as e:
            logger.warning(f"❌ Gemini API failed: {e}")
            return None
    
    def _try_openai(self, prompt: str, **kwargs) -> Optional[str]:
        """Try to get response from OpenAI API."""
        if not self.openai_client:
            return None
            
        try:
            logger.info("🔄 Falling back to OpenAI API...")
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get('max_tokens', 1000),
                temperature=kwargs.get('temperature', 0.7)
            )
            
            if response.choices and response.choices[0].message.content:
                logger.info("✅ OpenAI API successful")
                return response.choices[0].message.content.strip()
            else:
                logger.warning("⚠️ OpenAI returned empty response")
                return None
                
        except Exception as e:
            logger.warning(f"❌ OpenAI API failed: {e}")
            return None
    
    def _try_local_fallback(self, prompt: str, **kwargs) -> str:
        """Accuracy-focused local fallback for demo reliability."""
        prompt_lower = prompt.lower()
        
        # Extract user question from RAG prompt if present
        import re
        user_question_match = re.search(r"User Question: (.*)", prompt, re.IGNORECASE)
        if user_question_match:
            question = user_question_match.group(1).lower().strip()
        else:
            question = prompt_lower
            
        # 1. Precise keyword matching on the extracted question
        
        # Refund Policy (Focused)
        if any(w in question for w in ["refund", "return"]):
            return "No refund after 7 days"
        # General "policy" inquiry (only if short or specific)
        if any(w == question or w in question for w in ["policy", "policies", "plicies"]):
            # Avoid matching "hiring policy", "privacy policy" (not in KB), etc.
            if not any(unrelated in question for unrelated in ["hiring", "privacy", "security", "data"]):
                return "No refund after 7 days"
            
        # Pricing
        if any(w in question for w in ["price", "cost", "how much", "monthly", "plan"]):
            if "pro" in question:
                return "Pro Plan: $79/month (Unlimited videos, 4K, 24/7 Priority support, Batch export)"
            return """AutoStream Pricing:
- Basic Plan: $29/month (10 videos, 720p, Email support)
- Pro Plan: $79/month (Unlimited videos, 4K, 24/7 Priority support, Batch export)"""
        
        # Features
        if any(w in question for w in ["feature", "capability", "what do", "how it works", "silence", "auto-cut", "caption"]):
            return """AutoStream Features:
- Smart Auto-Cut: AI removes silences and dead air automatically.
- AI Captions: 98% accurate auto-transcription in 30+ languages.
- One-Click Colour Grade: Cinematic LUT presets.
- AI Story Agent: Describe your vision, and we assemble the rough cut."""

        # Support
        if any(w in question for w in ["support", "help", "contact"]):
            return "Support: 24/7 support is available on the Pro plan. Basic plan users get email support."
            
        # Neutral acknowledgments
        if any(w == question for w in ["okay", "ok", "thanks", "thank you", "cool", "got it"]):
            return "You're very welcome! Let me know if you have any other questions about AutoStream."

        # 2. RAG specific handling for the "I don't know" fallback
        if "knowledge base:" in prompt_lower:
            return "I don't have that information about that specific question. I can only provide details about AutoStream's features, pricing (Basic/Pro plans), and policies."

        # 3. Conversational fallbacks
        if any(word in prompt_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return "Hello! I'm your AutoStream AI assistant. How can I help you today?"
            
        return "I can help with pricing, plans, or features of AutoStream. What would you like to know?"
    
    def generate_response(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate response using hybrid LLM system.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters (max_tokens, temperature, etc.)
            
        Returns:
            Dict with response and metadata about which provider was used
        """
        result = {
            "response": "",
            "provider": "",
            "success": False,
            "fallback_used": False
        }
        
        # 🎯 DEMO MODE: Use local logic for reliable demo
        if not USE_API:
            logger.info("🎯 Demo Mode: Using local logic for reliability")
            local_response = self._try_local_fallback(prompt, **kwargs)
            result.update({
                "response": local_response,
                "provider": LLMProvider.LOCAL.value,
                "success": True,
                "fallback_used": False
            })
            return result
        
        # API Mode: Try Gemini first
        gemini_response = self._try_gemini(prompt, **kwargs)
        if gemini_response:
            result.update({
                "response": gemini_response,
                "provider": LLMProvider.GEMINI.value,
                "success": True
            })
            return result
        
        # Fallback to OpenAI
        openai_response = self._try_openai(prompt, **kwargs)
        if openai_response:
            result.update({
                "response": openai_response,
                "provider": LLMProvider.OPENAI.value,
                "success": True,
                "fallback_used": True
            })
            return result
        
        # Final fallback to local logic
        local_response = self._try_local_fallback(prompt, **kwargs)
        result.update({
            "response": local_response,
            "provider": LLMProvider.LOCAL.value,
            "success": True,
            "fallback_used": True
        })
        
        return result
    
    def classify_intent(self, message: str) -> Dict[str, Any]:
        """
        Classify user intent using hybrid system with enhanced local detection.
        
        Returns intent classification with provider info.
        """
        # 🎯 Enhanced local intent detection for demo
        if not USE_API:
            return self._classify_intent_local(message)
        
        # API mode: Use LLM for classification
        prompt = f"""
        Classify the following user message into one of these intents:
        - greeting: Hello, hi, hey, etc.
        - product_inquiry: Questions about features, capabilities, what we do
        - pricing_inquiry: Questions about cost, pricing, plans
        - platform_inquiry: Questions about integrations, platforms, how to connect
        - high_intent_lead: Shows strong purchase intent, ready to buy
        - general: General questions or unclear intent
        
        Message: "{message}"
        
        Respond with just the intent name (one word).
        """
        
        result = self.generate_response(prompt, temperature=0.1, max_tokens=50)
        
        # Extract intent from response
        intent = result["response"].lower().strip()
        valid_intents = ["greeting", "product_inquiry", "pricing_inquiry", "platform_inquiry", "high_intent_lead", "general"]
        
        if intent not in valid_intents:
            intent = "general"  # Default fallback
        
        return {
            "intent": intent,
            "provider": result["provider"],
            "fallback_used": result["fallback_used"],
            "confidence": 0.8 if result["provider"] != "local" else 0.6
        }
    
    def _classify_intent_local(self, message: str) -> Dict[str, Any]:
        """Smart intent detection with natural language understanding."""
        t = message.lower().strip()
        
        # 1. High intent detection (highest priority)
        buy_words = ["buy", "signup", "sign up", "try", "subscribe", "start", "get started", "want", "ready", "interested", "go with", "choose", "select", "pro plan", "basic plan"]
        if any(w in t for w in buy_words):
            return {
                "intent": "high_intent_lead",
                "provider": "local",
                "fallback_used": False,
                "confidence": 0.95
            }
            
        # 2. Other intents
        greeting_words = ["hi", "hello", "hey", "good morning", "good evening", "greetings"]
        pricing_words = ["price", "cost", "how much", "plan", "pricing", "subscription", "monthly", "fee"]
        
        if any(w in t for w in greeting_words):
            return {
                "intent": "greeting",
                "provider": "local",
                "fallback_used": False,
                "confidence": 0.9
            }
        
        elif any(w in t for w in pricing_words):
            return {
                "intent": "pricing_inquiry",
                "provider": "local",
                "fallback_used": False,
                "confidence": 0.9
            }
        
        # Platform detection
        elif any(w in t for w in ["youtube", "instagram", "tiktok", "platform", "integration", "works with"]):
            return {
                "intent": "platform_inquiry",
                "provider": "local",
                "fallback_used": False,
                "confidence": 0.85
            }
        
        # Product/feature inquiry
        elif any(w in t for w in ["feature", "features", "tell me about", "what", "how", "explain", "does", "can"]):
            return {
                "intent": "product_inquiry",
                "provider": "local",
                "fallback_used": False,
                "confidence": 0.8
            }
        
        # Default to general
        return {
            "intent": "general",
            "provider": "local",
            "fallback_used": False,
            "confidence": 0.6
        }
    
    def generate_conversational_response(self, message: str, context: str = "") -> Dict[str, Any]:
        """
        Generate conversational response with context.
        """
        prompt = f"""
        You are a helpful AI assistant for AutoStream. Be conversational and friendly.
        
        Context: {context}
        
        User message: {message}
        
        Provide a helpful, conversational response.
        """
        
        return self.generate_response(prompt, temperature=0.7, max_tokens=500)

# Global instance
hybrid_llm = HybridLLM()

def get_hybrid_llm():
    """Get the global hybrid LLM instance."""
    return hybrid_llm

if __name__ == "__main__":
    # Test the hybrid system
    llm = get_hybrid_llm()
    
    test_messages = [
        "Hello there!",
        "How much does this cost?",
        "What features do you offer?",
        "Tell me about your platform integrations"
    ]
    
    print("🧪 Testing Hybrid LLM System")
    print("=" * 50)
    
    for msg in test_messages:
        print(f"\n📝 Input: {msg}")
        result = llm.generate_response(msg)
        print(f"🤖 Provider: {result['provider']}")
        print(f"🔄 Fallback Used: {result['fallback_used']}")
        print(f"💬 Response: {result['response']}")
        print("-" * 30)
