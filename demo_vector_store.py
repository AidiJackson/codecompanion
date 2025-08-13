"""
Demo script for the local vector memory system.
Shows how to use the VectorStore for document storage and semantic search.
"""

import os
import logging
from memory.vector_store import VectorStore

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_vector_store():
    """Demonstrate vector store functionality"""

    # Initialize vector store with OpenAI API key from environment
    openai_api_key = os.getenv("OPENAI_API_KEY")
    vector_store = VectorStore(
        db_path="memory/demo_vector_memory.db", openai_api_key=openai_api_key
    )

    print("🚀 Vector Store Demo")
    print("=" * 50)

    # Add some sample documents
    sample_docs = [
        {
            "id": "doc1",
            "text": "Python is a high-level programming language known for its simplicity and readability. It's widely used in web development, data science, and artificial intelligence.",
            "metadata": {
                "category": "programming",
                "language": "python",
                "topic": "overview",
            },
        },
        {
            "id": "doc2",
            "text": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
            "metadata": {
                "category": "ai",
                "topic": "machine_learning",
                "difficulty": "intermediate",
            },
        },
        {
            "id": "doc3",
            "text": "SQLite is a lightweight, file-based database engine that doesn't require a separate server process. It's perfect for embedded applications and prototypes.",
            "metadata": {"category": "database", "type": "embedded", "topic": "sqlite"},
        },
        {
            "id": "doc4",
            "text": "Vector databases are specialized storage systems designed to handle high-dimensional vector data, enabling efficient similarity search and semantic retrieval.",
            "metadata": {
                "category": "database",
                "type": "vector",
                "topic": "similarity_search",
            },
        },
        {
            "id": "doc5",
            "text": "Natural language processing combines computational linguistics with machine learning to help computers understand, interpret and generate human language.",
            "metadata": {"category": "ai", "topic": "nlp", "difficulty": "advanced"},
        },
    ]

    print("\n📝 Adding sample documents...")
    handles = []
    for doc in sample_docs:
        handle = vector_store.add(doc["id"], doc["text"], doc["metadata"])
        handles.append(handle)
        print(f"  ✅ Added {doc['id']} -> Handle: {handle}")

    # Show stats
    print("\n📊 Vector Store Stats:")
    stats = vector_store.stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Test queries
    test_queries = [
        "programming languages for beginners",
        "artificial intelligence and learning",
        "database storage solutions",
        "text processing and language understanding",
    ]

    print("\n🔍 Testing semantic search...")
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = vector_store.query(query, top_k=3)

        if results:
            for i, (doc_id, score, metadata) in enumerate(results, 1):
                print(
                    f"  {i}. {doc_id} (score: {score:.3f}) - {metadata.get('topic', 'N/A')}"
                )
        else:
            print("  No results found")

    # Show context handles
    print("\n🔗 Context Handles:")
    handles_data = vector_store.get_context_handles()
    for handle in handles_data[:3]:  # Show first 3
        print(f"  Handle: {handle['handle_id']}")
        print(f"    Summary: {handle['summary'][:80]}...")
        print(f"    Key phrases: {handle['key_phrases']}")
        print(f"    Importance: {handle['importance_score']:.2f}")
        print()

    # Test document retrieval by handle
    if handles:
        print("📄 Document retrieval by handle:")
        sample_handle = handles[0]
        doc = vector_store.get_document_by_handle(sample_handle)
        if doc:
            print(f"  Handle: {sample_handle}")
            print(f"  Document ID: {doc['document_id']}")
            print(f"  Content preview: {doc['text_content'][:100]}...")
            print(f"  Metadata: {doc['metadata']}")

    print(f"\n✅ Demo completed! Vector store saved at: {vector_store.db_path}")
    return vector_store


if __name__ == "__main__":
    demo_vector_store()
