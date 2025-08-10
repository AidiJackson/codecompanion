"""
Test script to demonstrate TF-IDF fallback functionality when OpenAI embeddings are not available.
"""

import logging
from memory.vector_store import VectorStore

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_tfidf_fallback():
    """Test vector store with TF-IDF fallback (no OpenAI key)"""
    
    print("🧪 Testing TF-IDF Fallback Mode")
    print("=" * 50)
    
    # Initialize without OpenAI key to force TF-IDF mode
    vector_store = VectorStore(
        db_path="memory/test_tfidf_memory.db",
        openai_api_key=None  # Force TF-IDF mode
    )
    
    # Add sample documents
    sample_docs = [
        {
            "id": "python_doc",
            "text": "Python programming language is excellent for data science and machine learning applications. It has libraries like pandas, numpy, and scikit-learn.",
            "metadata": {"category": "programming", "language": "python"}
        },
        {
            "id": "javascript_doc", 
            "text": "JavaScript is the programming language of the web. It runs in browsers and enables interactive web applications with frameworks like React and Vue.",
            "metadata": {"category": "programming", "language": "javascript"}
        },
        {
            "id": "database_doc",
            "text": "Databases store and organize data efficiently. SQL databases like PostgreSQL and MySQL are relational, while NoSQL databases like MongoDB handle unstructured data.",
            "metadata": {"category": "database", "type": "overview"}
        }
    ]
    
    print("\n📝 Adding documents...")
    handles = []
    for doc in sample_docs:
        handle = vector_store.add(doc["id"], doc["text"], doc["metadata"])
        handles.append(handle)
        print(f"  ✅ Added {doc['id']} -> Handle: {handle}")
    
    # Show stats
    print(f"\n📊 Vector Store Stats:")
    stats = vector_store.stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test search queries
    test_queries = [
        "programming languages",
        "web development", 
        "data storage",
        "machine learning python"
    ]
    
    print(f"\n🔍 Testing TF-IDF similarity search...")
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = vector_store.query(query, top_k=3)
        
        if results:
            for i, (doc_id, score, metadata) in enumerate(results, 1):
                print(f"  {i}. {doc_id} (TF-IDF score: {score:.3f}) - {metadata.get('category', 'N/A')}")
        else:
            print("  No results found")
    
    print(f"\n✅ TF-IDF fallback test completed!")
    return vector_store

if __name__ == "__main__":
    test_tfidf_fallback()