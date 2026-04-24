"""
RAG (Retrieval-Augmented Generation) module for AutoStream knowledge base.
"""

import json
import os
from typing import Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from hybrid_llm import get_hybrid_llm


class KnowledgeBase:
    """Manages the AutoStream knowledge base with hybrid LLM integration."""
    
    def __init__(self, knowledge_file: str = "knowledge_base.json"):
        self.knowledge_file = knowledge_file
        self.documents = []
        self.vectorstore = None
        self.hybrid_llm = get_hybrid_llm()
        self.load_knowledge()
    
    def load_knowledge(self):
        """Load knowledge base from JSON file."""
        # Handle path relative to this file if not absolute
        file_path = self.knowledge_file
        if not os.path.isabs(file_path):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(base_dir, file_path)
            
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert knowledge to documents
        self.documents = self._convert_to_documents(data)
        
        # Initialize FAISS vectorstore
        try:
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=os.getenv("OPENAI_API_KEY")
            )
            self.vectorstore = FAISS.from_documents(
                self.documents,
                embeddings
            )
        except Exception as e:
            print(f"Warning: Could not initialize FAISS vectorstore: {e}")
            print("Falling back to simple keyword search")
    
    def _convert_to_documents(self, data: dict) -> list[Document]:
        """Convert knowledge base JSON to Document objects."""
        documents = []
        
        # Product info
        product_text = f"""
Product Name: {data['product']['name']}
Description: {data['product']['description']}
Tagline: {data['product']['tagline']}
"""
        documents.append(Document(
            page_content=product_text,
            metadata={"type": "product"}
        ))
        
        # Pricing info
        pricing_text = "AutoStream Pricing:\n\n"
        for plan in data['pricing']['plans']:
            pricing_text += f"""
Plan: {plan['name']}
Price: ${plan['price']}/{plan['frequency']}
Features: {', '.join(plan['features'])}
"""
        documents.append(Document(
            page_content=pricing_text,
            metadata={"type": "pricing"}
        ))
        
        # Features info
        features_text = "AutoStream Features:\n\n"
        for feature in data['features']:
            features_text += f"- {feature['name']}: {feature['description']}\n"
        documents.append(Document(
            page_content=features_text,
            metadata={"type": "features"}
        ))
        
        # Policies info
        policies = data.get('policies', {})
        policies_text = "Company Policies:\n"
        if 'refunds' in policies:
            policies_text += f"- Refunds: {policies['refunds']}\n"
        if 'support' in policies:
            policies_text += f"- Support: {policies['support']}\n"
        if 'trial' in policies:
            policies_text += f"- Trial: {policies['trial']}\n"

        documents.append(Document(
            page_content=policies_text,
            metadata={"type": "policies"}
        ))
        
        return documents
    
    def retrieve(self, query: str, k: int = 3) -> list[str]:
        """
        Retrieve relevant documents from the knowledge base.
        
        Args:
            query: The search query
            k: Number of documents to retrieve
            
        Returns:
            List of relevant document contents
        """
        if self.vectorstore:
            try:
                results = self.vectorstore.similarity_search(query, k=k)
                return [doc.page_content for doc in results]
            except Exception as e:
                print(f"Error during retrieval: {e}")
                return self._fallback_search(query)
        else:
            return self._fallback_search(query)
    
    def _fallback_search(self, query: str) -> list[str]:
        """Simple keyword-based search fallback."""
        query_lower = query.lower()
        results = []
        
        for doc in self.documents:
            if any(word in doc.page_content.lower() for word in query_lower.split()):
                results.append(doc.page_content)
        
        return results[:3] if results else [self._get_default_response()]
    
    def _get_default_response(self) -> str:
        """Get default response when no matches found."""
        return """
AutoStream is an AI-powered video editing platform.
We offer:
- Basic Plan: $29/month with 10 videos/month in 720p
- Pro Plan: $79/month with unlimited videos in 4K and 24/7 support

Our features include:
- Smart Auto-Cut: AI-powered silence and filler detection
- AI Captions: 98% accurate in 30+ languages
- One-Click Colour Grade: Cinematic LUT presets
- Audio Cleanup: Noise removal and level normalization
- Batch Export: Optimized for YouTube, Reels, TikTok
- AI Story Agent: Text-to-video assembly

Would you like to try AutoStream? I can help you get started!
"""
    
    def generate_response(self, query: str, context: str = "") -> dict:
        """
        Generate a response using the hybrid LLM system with retrieved context.
        
        Args:
            query: User query
            context: Additional context (optional)
            
        Returns:
            Dict with response and metadata
        """
        # Retrieve relevant documents
        relevant_docs = self.retrieve(query, k=3)
        retrieved_context = "\n\n".join(relevant_docs)
        
        # Create prompt with context
        prompt = f"""
        You are a strictly accurate AI assistant for AutoStream. Your goal is to provide 100% accurate information based ONLY on the provided Knowledge Base.
        
        CRITICAL RULES:
        1. If the answer is in the Knowledge Base, provide it clearly and concisely.
        2. If the answer is NOT in the Knowledge Base, you MUST say: "I'm sorry, but I don't have information about that specific question. I can only provide details about AutoStream's features, pricing (Basic/Pro plans), and policies."
        3. DO NOT hallucinate or use outside knowledge.
        4. If the user expresses interest in a plan (e.g., "I'll go with Pro"), acknowledge it and mention you can help them get started.
        
        Knowledge Base:
        {retrieved_context}
        
        Additional Context:
        {context}
        
        User Question: {query}
        
        Response:
        """
        
        # Use hybrid LLM to generate response
        result = self.hybrid_llm.generate_response(prompt, temperature=0.0, max_tokens=500)
        
        return {
            "response": result["response"],
            "provider": result["provider"],
            "fallback_used": result["fallback_used"],
            "retrieved_docs": len(relevant_docs),
            "context_used": bool(retrieved_context.strip())
        }
    
    def get_all_knowledge(self) -> str:
        """Get all knowledge as a single string for context."""
        return "\n\n".join([doc.page_content for doc in self.documents])


# Global knowledge base instance
_knowledge_base: Optional[KnowledgeBase] = None


def get_knowledge_base() -> KnowledgeBase:
    """Get or create the global knowledge base instance."""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base
