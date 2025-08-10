"""
Tiny Local Vector Memory using SQLite-VSS or lightweight fallbacks.

This module provides a lightweight vector storage solution that:
1. Uses SQLite for persistence with vector similarity search
2. Falls back to TF-IDF similarity when OpenAI embeddings are unavailable  
3. Stores only handles in artifacts, never raw long text
4. Supports add/query operations with metadata
"""

import sqlite3
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    TfidfVectorizer = None
    cosine_similarity = None
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Lightweight vector storage with SQLite persistence.
    
    Features:
    - OpenAI embeddings for high-quality semantic search (when available)
    - TF-IDF fallback for basic similarity matching
    - Context handles instead of raw text storage
    - Metadata support for filtering and enrichment
    """
    
    def __init__(self, db_path: str = "memory/vector_memory.db", openai_api_key: Optional[str] = None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenAI client if available
        self.openai_client = None
        self.use_openai = False
        
        if OPENAI_AVAILABLE and openai_api_key and OpenAI is not None:
            try:
                self.openai_client = OpenAI(api_key=openai_api_key)
                self.use_openai = True
                logger.info("✅ Vector store initialized with OpenAI embeddings")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize OpenAI client: {e}")
        
        # Initialize TF-IDF fallback
        self.tfidf_vectorizer = None
        self.tfidf_enabled = SKLEARN_AVAILABLE
        if not self.use_openai and self.tfidf_enabled and TfidfVectorizer is not None:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                lowercase=True,
                ngram_range=(1, 2)
            )
            logger.info("📊 Vector store initialized with TF-IDF fallback")
        elif not self.use_openai:
            logger.warning("⚠️  No vector similarity available - install scikit-learn for TF-IDF fallback")
        
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize SQLite database with vector storage tables"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Main documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vector_documents (
                    document_id TEXT PRIMARY KEY,
                    text_content TEXT NOT NULL,
                    text_hash TEXT NOT NULL,
                    metadata TEXT,
                    embedding_type TEXT,
                    embedding_data BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Context handles table - stores only references, not full text
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS context_handles (
                    handle_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    context_type TEXT NOT NULL,
                    summary TEXT,
                    key_phrases TEXT,
                    importance_score REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES vector_documents (document_id)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_hash ON vector_documents(text_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_handle_type ON context_handles(context_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_handle_score ON context_handles(importance_score)")
            
            conn.commit()
            
        logger.info(f"✅ Vector database initialized at {self.db_path}")
    
    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding for text using OpenAI or return None"""
        if not self.use_openai or not self.openai_client:
            return None
            
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text.strip()
            )
            return np.array(response.data[0].embedding, dtype=np.float32)
        except Exception as e:
            logger.error(f"Failed to get OpenAI embedding: {e}")
            return None
    
    def _calculate_text_hash(self, text: str) -> str:
        """Calculate hash for text deduplication"""
        import hashlib
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _extract_key_phrases(self, text: str, max_phrases: int = 5) -> List[str]:
        """Extract key phrases from text for context handles"""
        words = text.lower().split()
        # Simple extraction - get longer words and potential compound terms
        phrases = []
        
        # Single important words (longer than 4 chars)
        important_words = [w for w in words if len(w) > 4 and w.isalpha()]
        phrases.extend(important_words[:max_phrases//2])
        
        # Two-word combinations
        if len(words) > 1:
            bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1) 
                      if len(words[i]) > 3 and len(words[i+1]) > 3]
            phrases.extend(bigrams[:max_phrases//2])
        
        return phrases[:max_phrases]
    
    def add(self, document_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add document to vector store and return context handle.
        
        Args:
            document_id: Unique identifier for the document
            text: Text content to store and index
            metadata: Optional metadata dictionary
            
        Returns:
            handle_id: Context handle ID for referencing this document
        """
        if not text.strip():
            raise ValueError("Text content cannot be empty")
        
        text_hash = self._calculate_text_hash(text)
        metadata_json = json.dumps(metadata or {})
        
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Check if document already exists
            existing = cursor.execute(
                "SELECT document_id FROM vector_documents WHERE document_id = ? OR text_hash = ?",
                (document_id, text_hash)
            ).fetchone()
            
            if existing:
                logger.info(f"Document {document_id} already exists, skipping")
                # Return existing handle if available
                handle = cursor.execute(
                    "SELECT handle_id FROM context_handles WHERE document_id = ? LIMIT 1",
                    (document_id,)
                ).fetchone()
                return handle[0] if handle else document_id
            
            # Get embedding
            embedding = self._get_embedding(text)
            embedding_type = "openai" if embedding is not None else "none"
            embedding_data = embedding.tobytes() if embedding is not None else None
            
            # Insert document
            cursor.execute("""
                INSERT INTO vector_documents 
                (document_id, text_content, text_hash, metadata, embedding_type, embedding_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (document_id, text, text_hash, metadata_json, embedding_type, embedding_data))
            
            # Create context handle
            handle_id = f"ctx_{uuid.uuid4().hex[:12]}"
            key_phrases = self._extract_key_phrases(text)
            summary = text[:200] + "..." if len(text) > 200 else text
            
            cursor.execute("""
                INSERT INTO context_handles
                (handle_id, document_id, context_type, summary, key_phrases, importance_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                handle_id, 
                document_id, 
                "document", 
                summary, 
                json.dumps(key_phrases),
                min(1.0, len(text) / 1000.0)  # Simple importance based on length
            ))
            
            conn.commit()
            
        logger.info(f"✅ Added document {document_id} with handle {handle_id}")
        return handle_id
    
    def query(self, text: str, top_k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """
        Query for similar documents.
        
        Args:
            text: Query text
            top_k: Number of results to return
            
        Returns:
            List of (document_id, similarity_score, metadata) tuples
        """
        if not text.strip():
            return []
        
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all documents
            documents = cursor.execute("""
                SELECT document_id, text_content, metadata, embedding_type, embedding_data
                FROM vector_documents
                ORDER BY created_at DESC
            """).fetchall()
            
            if not documents:
                return []
            
            results = []
            query_embedding = self._get_embedding(text)
            
            if query_embedding is not None:
                # Use OpenAI embeddings for similarity
                for doc in documents:
                    if doc['embedding_type'] == 'openai' and doc['embedding_data']:
                        doc_embedding = np.frombuffer(doc['embedding_data'], dtype=np.float32)
                        similarity = np.dot(query_embedding, doc_embedding) / (
                            np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                        )
                        metadata = json.loads(doc['metadata'] or '{}')
                        results.append((doc['document_id'], float(similarity), metadata))
                        
            elif self.tfidf_enabled and self.tfidf_vectorizer is not None and cosine_similarity is not None:
                # Use TF-IDF fallback
                texts = [text] + [doc['text_content'] for doc in documents]
                try:
                    tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
                    query_vector = tfidf_matrix[0]
                    doc_vectors = tfidf_matrix[1:]
                    
                    similarities = cosine_similarity(query_vector, doc_vectors)[0]
                    
                    for i, doc in enumerate(documents):
                        metadata = json.loads(doc['metadata'] or '{}')
                        results.append((doc['document_id'], float(similarities[i]), metadata))
                        
                except Exception as e:
                    logger.error(f"TF-IDF similarity failed: {e}")
                    
            else:
                # Simple keyword matching fallback
                query_words = set(text.lower().split())
                for doc in documents:
                    doc_words = set(doc['text_content'].lower().split())
                    overlap = len(query_words & doc_words)
                    similarity = overlap / max(len(query_words), 1)
                    metadata = json.loads(doc['metadata'] or '{}')
                    results.append((doc['document_id'], similarity, metadata))
            
            # Sort by similarity and return top_k
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
    
    def get_context_handles(self, context_type: Optional[str] = None, min_importance: float = 0.0) -> List[Dict[str, Any]]:
        """
        Get context handles with optional filtering.
        
        Args:
            context_type: Filter by context type
            min_importance: Minimum importance score
            
        Returns:
            List of context handle dictionaries
        """
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT h.*, d.metadata as doc_metadata
                FROM context_handles h
                JOIN vector_documents d ON h.document_id = d.document_id
                WHERE h.importance_score >= ?
            """
            params: List[Any] = [min_importance]
            
            if context_type:
                query += " AND h.context_type = ?"
                params.append(context_type)
                
            query += " ORDER BY h.importance_score DESC, h.created_at DESC"
            
            handles = cursor.execute(query, params).fetchall()
            
            return [
                {
                    'handle_id': h['handle_id'],
                    'document_id': h['document_id'],
                    'context_type': h['context_type'],
                    'summary': h['summary'],
                    'key_phrases': json.loads(h['key_phrases'] or '[]'),
                    'importance_score': h['importance_score'],
                    'created_at': h['created_at'],
                    'metadata': json.loads(h['doc_metadata'] or '{}')
                }
                for h in handles
            ]
    
    def get_document_by_handle(self, handle_id: str) -> Optional[Dict[str, Any]]:
        """Get full document content by context handle"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            result = cursor.execute("""
                SELECT d.*, h.context_type, h.summary, h.key_phrases, h.importance_score
                FROM vector_documents d
                JOIN context_handles h ON d.document_id = h.document_id
                WHERE h.handle_id = ?
            """, (handle_id,)).fetchone()
            
            if not result:
                return None
                
            return {
                'document_id': result['document_id'],
                'text_content': result['text_content'],
                'metadata': json.loads(result['metadata'] or '{}'),
                'context_type': result['context_type'],
                'summary': result['summary'],
                'key_phrases': json.loads(result['key_phrases'] or '[]'),
                'importance_score': result['importance_score'],
                'created_at': result['created_at']
            }
    
    def stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            doc_count = cursor.execute("SELECT COUNT(*) FROM vector_documents").fetchone()[0]
            handle_count = cursor.execute("SELECT COUNT(*) FROM context_handles").fetchone()[0]
            
            embedding_stats = cursor.execute("""
                SELECT embedding_type, COUNT(*) as count
                FROM vector_documents
                GROUP BY embedding_type
            """).fetchall()
            
            return {
                'total_documents': doc_count,
                'total_handles': handle_count,
                'embedding_types': dict(embedding_stats),
                'openai_available': self.use_openai,
                'tfidf_available': self.tfidf_enabled,
                'database_path': str(self.db_path)
            }