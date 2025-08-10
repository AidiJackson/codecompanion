"""
Integration utilities for the vector store with the existing system.
Provides helpers to integrate vector memory with the project memory and agents.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from memory.vector_store import VectorStore

logger = logging.getLogger(__name__)

class VectorMemoryIntegration:
    """
    Integration layer between vector store and the existing project memory system.
    """
    
    def __init__(self, vector_db_path: str = "memory/project_vectors.db"):
        """Initialize vector memory integration"""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.vector_store = VectorStore(
            db_path=vector_db_path,
            openai_api_key=self.openai_api_key
        )
        
    def store_agent_interaction(self, 
                               agent_name: str, 
                               interaction_content: str, 
                               interaction_type: str = "response",
                               metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store agent interaction in vector memory for semantic retrieval.
        
        Args:
            agent_name: Name of the agent
            interaction_content: The content to store
            interaction_type: Type of interaction (response, request, etc.)
            metadata: Additional metadata
            
        Returns:
            Context handle ID for referencing this interaction
        """
        enhanced_metadata = {
            "agent_name": agent_name,
            "interaction_type": interaction_type,
            "stored_at": "vector_memory",
            **(metadata or {})
        }
        
        document_id = f"{agent_name}_{interaction_type}_{hash(interaction_content) % 1000000}"
        
        handle = self.vector_store.add(
            document_id=document_id,
            text=interaction_content,
            metadata=enhanced_metadata
        )
        
        logger.info(f"Stored {agent_name} {interaction_type} in vector memory: {handle}")
        return handle
        
    def store_project_artifact(self, 
                              artifact_type: str, 
                              content: str,
                              title: str = "",
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store project artifact in vector memory for semantic search.
        
        Args:
            artifact_type: Type of artifact (code, documentation, etc.)
            content: The artifact content
            title: Title/name of the artifact
            metadata: Additional metadata
            
        Returns:
            Context handle ID
        """
        enhanced_metadata = {
            "artifact_type": artifact_type,
            "title": title,
            "stored_at": "vector_memory",
            **(metadata or {})
        }
        
        document_id = f"artifact_{artifact_type}_{hash(content) % 1000000}"
        
        handle = self.vector_store.add(
            document_id=document_id,
            text=content,
            metadata=enhanced_metadata
        )
        
        logger.info(f"Stored artifact {artifact_type} in vector memory: {handle}")
        return handle
        
    def find_similar_interactions(self, 
                                 query: str, 
                                 agent_name: Optional[str] = None,
                                 interaction_type: Optional[str] = None,
                                 top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar agent interactions using semantic search.
        
        Args:
            query: Search query
            agent_name: Filter by specific agent (optional)
            interaction_type: Filter by interaction type (optional)
            top_k: Number of results to return
            
        Returns:
            List of similar interactions with metadata
        """
        results = self.vector_store.query(query, top_k=top_k * 2)  # Get more to filter
        
        filtered_results = []
        for doc_id, score, metadata in results:
            # Apply filters
            if agent_name and metadata.get('agent_name') != agent_name:
                continue
            if interaction_type and metadata.get('interaction_type') != interaction_type:
                continue
                
            filtered_results.append({
                'document_id': doc_id,
                'similarity_score': score,
                'metadata': metadata
            })
            
            if len(filtered_results) >= top_k:
                break
                
        return filtered_results
        
    def find_similar_artifacts(self, 
                             query: str,
                             artifact_type: Optional[str] = None,
                             top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar project artifacts using semantic search.
        
        Args:
            query: Search query
            artifact_type: Filter by artifact type (optional)
            top_k: Number of results to return
            
        Returns:
            List of similar artifacts with metadata
        """
        results = self.vector_store.query(query, top_k=top_k * 2)
        
        filtered_results = []
        for doc_id, score, metadata in results:
            # Only include artifacts
            if not metadata.get('artifact_type'):
                continue
                
            # Apply artifact type filter
            if artifact_type and metadata.get('artifact_type') != artifact_type:
                continue
                
            filtered_results.append({
                'document_id': doc_id,
                'similarity_score': score,
                'metadata': metadata
            })
            
            if len(filtered_results) >= top_k:
                break
                
        return filtered_results
        
    def get_context_for_agent(self, 
                             agent_name: str, 
                             query: str,
                             max_contexts: int = 3) -> List[str]:
        """
        Get relevant context handles for an agent based on a query.
        This returns only handles, not full content, as requested.
        
        Args:
            agent_name: Name of the agent requesting context
            query: Context query
            max_contexts: Maximum number of context handles to return
            
        Returns:
            List of context handle IDs
        """
        # Find similar interactions and artifacts
        interactions = self.find_similar_interactions(query, top_k=max_contexts)
        artifacts = self.find_similar_artifacts(query, top_k=max_contexts)
        
        # Combine and sort by similarity
        all_results = interactions + artifacts
        all_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Get context handles for top results
        handles = []
        for result in all_results[:max_contexts]:
            # Find the context handle for this document
            handle_data = self.vector_store.get_context_handles()
            for handle in handle_data:
                if handle['document_id'] == result['document_id']:
                    handles.append(handle['handle_id'])
                    break
                    
        logger.info(f"Provided {len(handles)} context handles to {agent_name}")
        return handles
        
    def expand_context_handle(self, handle_id: str) -> Optional[Dict[str, Any]]:
        """
        Expand a context handle to get the full document content.
        Use this when an agent needs to access the actual content.
        
        Args:
            handle_id: Context handle ID
            
        Returns:
            Full document data or None if not found
        """
        return self.vector_store.get_document_by_handle(handle_id)
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get vector memory statistics"""
        return self.vector_store.stats()

# Global instance for easy access
_vector_integration = None

def get_vector_integration() -> VectorMemoryIntegration:
    """Get global vector memory integration instance"""
    global _vector_integration
    if _vector_integration is None:
        _vector_integration = VectorMemoryIntegration()
    return _vector_integration