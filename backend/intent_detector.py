"""
Intent detection module for classifying user messages.
"""

from enum import Enum
from typing import Optional
import os
from pydantic import BaseModel
from hybrid_llm import get_hybrid_llm


class Intent(str, Enum):
    """User intent classifications."""
    CASUAL_GREETING = "casual_greeting"
    PRODUCT_INQUIRY = "product_inquiry"
    HIGH_INTENT_LEAD = "high_intent_lead"
    PLATFORM_QUESTION = "platform_question"
    PRICING_QUESTION = "pricing_question"


class IntentResult(BaseModel):
    """Result of intent detection."""
    intent: Intent
    confidence: float
    reasoning: str


class IntentDetector:
    """Detects user intent from messages using hybrid LLM system."""
    
    def __init__(self):
        self.hybrid_llm = get_hybrid_llm()
        
        self.intent_prompt = """
You are an expert at detecting user intent in conversations about AutoStream, an AI-powered video editing platform.

Classify the user's message into ONE of these categories:
1. CASUAL_GREETING - Simple greeting, small talk, pleasantries
2. PRODUCT_INQUIRY - General questions about AutoStream, features, or how it works
3. PRICING_QUESTION - Questions about pricing, plans, costs, or trial
4. PLATFORM_QUESTION - Questions about which platforms (YouTube, Instagram, TikTok) are supported
5. HIGH_INTENT_LEAD - The user explicitly shows readiness to sign up, try the product, or commit (e.g., "I want to sign up", "let's try it", "how do I get started with the pro plan")

User message: "{message}"

Respond ONLY with a JSON object in this exact format:
{{
  "intent": "INTENT_NAME",
  "confidence": 0.95,
  "reasoning": "Brief explanation of why this intent was chosen"
}}

Do NOT include any other text, just the JSON object.
"""
    
    def detect(self, message: str) -> IntentResult:
        """
        Detect the intent of a user message using hybrid LLM system.
        
        Args:
            message: The user's message
            
        Returns:
            IntentResult with detected intent and confidence
        """
        try:
            # Use hybrid LLM for intent classification
            result = self.hybrid_llm.classify_intent(message)
            
            # Map hybrid intents to our enum
            intent_mapping = {
                "greeting": Intent.CASUAL_GREETING,
                "product_inquiry": Intent.PRODUCT_INQUIRY,
                "pricing_inquiry": Intent.PRICING_QUESTION,
                "platform_inquiry": Intent.PLATFORM_QUESTION,
                "high_intent_lead": Intent.HIGH_INTENT_LEAD,
                "inquiry": Intent.PRODUCT_INQUIRY,  # New fallback intent
                "general": Intent.CASUAL_GREETING  # Default fallback
            }
            
            detected_intent = intent_mapping.get(result["intent"], Intent.CASUAL_GREETING)
            
            return IntentResult(
                intent=detected_intent,
                confidence=result["confidence"],
                reasoning=f"Detected using {result['provider']} LLM. Fallback used: {result['fallback_used']}"
            )
        
        except Exception as e:
            print(f"Error detecting intent with hybrid LLM: {e}")
            # Fallback to keyword-based detection
            return self._fallback_detection(message)
    
    def _fallback_detection(self, message: str) -> IntentResult:
        """Fallback keyword-based intent detection."""
        message_lower = message.lower()
        
        # High-intent keywords
        high_intent_keywords = [
            "sign up", "signup", "get started", "start", "try",
            "want to", "ready to", "let's go", "how do i",
            "i'd like", "i want", "can i", "subscribe", "purchase",
            "buy", "upgrade", "pro plan", "basic plan"
        ]
        
        # Check for high-intent
        if any(keyword in message_lower for keyword in high_intent_keywords):
            return IntentResult(
                intent=Intent.HIGH_INTENT_LEAD,
                confidence=0.85,
                reasoning="Message contains sign-up or commitment language"
            )
        
        # Pricing questions
        if any(word in message_lower for word in ["price", "cost", "plan", "free", "$", "how much"]):
            return IntentResult(
                intent=Intent.PRICING_QUESTION,
                confidence=0.9,
                reasoning="Message contains pricing-related keywords"
            )
        
        # Platform questions
        if any(word in message_lower for word in ["youtube", "instagram", "tiktok", "platform", "where", "which"]):
            return IntentResult(
                intent=Intent.PLATFORM_QUESTION,
                confidence=0.85,
                reasoning="Message asks about platform support"
            )
        
        # Product inquiry
        if any(word in message_lower for word in ["how", "what", "feature", "does", "work", "can it"]):
            return IntentResult(
                intent=Intent.PRODUCT_INQUIRY,
                confidence=0.8,
                reasoning="Message asks about product features or functionality"
            )
        
        # Default to casual greeting
        return IntentResult(
            intent=Intent.CASUAL_GREETING,
            confidence=0.7,
            reasoning="No specific intent detected, treating as greeting"
        )


def get_intent_detector() -> IntentDetector:
    """Get or create the global intent detector instance."""
    return IntentDetector()
