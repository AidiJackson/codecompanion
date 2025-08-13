"""
Streamlit demo showing vector memory integration
"""

import streamlit as st
from memory.integration import VectorMemoryIntegration


def main():
    st.title("🧠 Vector Memory System Demo")
    st.write("Semantic search for agent interactions and project artifacts")

    # Initialize vector integration
    if "vector_integration" not in st.session_state:
        st.session_state.vector_integration = VectorMemoryIntegration(
            "memory/streamlit_demo.db"
        )

    integration = st.session_state.vector_integration

    # Sidebar for adding content
    with st.sidebar:
        st.header("📝 Add Content")

        content_type = st.selectbox(
            "Content Type", ["Agent Interaction", "Project Artifact"]
        )

        if content_type == "Agent Interaction":
            agent_name = st.selectbox(
                "Agent",
                [
                    "ProjectManager",
                    "CodeGenerator",
                    "UIDesigner",
                    "TestWriter",
                    "Debugger",
                ],
            )
            interaction_type = st.selectbox(
                "Type", ["response", "request", "planning", "analysis"]
            )
            content = st.text_area("Interaction Content")

            if st.button("Store Interaction"):
                if content.strip():
                    handle = integration.store_agent_interaction(
                        agent_name=agent_name,
                        interaction_content=content,
                        interaction_type=interaction_type,
                    )
                    st.success(f"Stored! Handle: {handle}")
                else:
                    st.error("Please enter content")

        else:  # Project Artifact
            artifact_type = st.selectbox(
                "Artifact Type", ["code", "documentation", "design", "test"]
            )
            title = st.text_input("Title")
            content = st.text_area("Artifact Content")

            if st.button("Store Artifact"):
                if content.strip() and title.strip():
                    handle = integration.store_project_artifact(
                        artifact_type=artifact_type, content=content, title=title
                    )
                    st.success(f"Stored! Handle: {handle}")
                else:
                    st.error("Please enter both title and content")

    # Main area for search
    st.header("🔍 Semantic Search")

    query = st.text_input("Search Query", placeholder="Enter your search terms...")

    col1, col2 = st.columns(2)

    with col1:
        search_interactions = st.checkbox("Search Interactions", value=True)
        agent_filter = None
        if search_interactions:
            agent_filter = st.selectbox(
                "Filter by Agent",
                ["All Agents"]
                + [
                    "ProjectManager",
                    "CodeGenerator",
                    "UIDesigner",
                    "TestWriter",
                    "Debugger",
                ],
            )

    with col2:
        search_artifacts = st.checkbox("Search Artifacts", value=True)
        artifact_filter = None
        if search_artifacts:
            artifact_filter = st.selectbox(
                "Filter by Type",
                ["All Types"] + ["code", "documentation", "design", "test"],
            )

    if st.button("Search") and query.strip():
        with st.spinner("Searching..."):
            # Search interactions
            if search_interactions:
                st.subheader("🤖 Similar Agent Interactions")
                agent_name = None if agent_filter == "All Agents" else agent_filter
                interactions = integration.find_similar_interactions(
                    query, agent_name=agent_name, top_k=5
                )

                if interactions:
                    for i, result in enumerate(interactions, 1):
                        metadata = result["metadata"]
                        with st.expander(
                            f"{i}. {metadata.get('agent_name', 'Unknown')} - {metadata.get('interaction_type', 'N/A')} (Score: {result['similarity_score']:.3f})"
                        ):
                            # Get full content
                            full_doc = integration.expand_context_handle(
                                result["document_id"]
                            )
                            if full_doc:
                                st.write(
                                    full_doc["text_content"][:500] + "..."
                                    if len(full_doc["text_content"]) > 500
                                    else full_doc["text_content"]
                                )
                                st.caption(f"Document ID: {result['document_id']}")
                else:
                    st.info("No similar interactions found")

            # Search artifacts
            if search_artifacts:
                st.subheader("📦 Similar Project Artifacts")
                artifact_type = (
                    None if artifact_filter == "All Types" else artifact_filter
                )
                artifacts = integration.find_similar_artifacts(
                    query, artifact_type=artifact_type, top_k=5
                )

                if artifacts:
                    for i, result in enumerate(artifacts, 1):
                        metadata = result["metadata"]
                        with st.expander(
                            f"{i}. {metadata.get('title', 'Untitled')} - {metadata.get('artifact_type', 'N/A')} (Score: {result['similarity_score']:.3f})"
                        ):
                            # Get full content
                            full_doc = integration.expand_context_handle(
                                result["document_id"]
                            )
                            if full_doc:
                                st.code(
                                    full_doc["text_content"][:500] + "..."
                                    if len(full_doc["text_content"]) > 500
                                    else full_doc["text_content"]
                                )
                                st.caption(f"Document ID: {result['document_id']}")
                else:
                    st.info("No similar artifacts found")

    # Context Handle Demo
    st.header("🔗 Context Handle System")
    st.write(
        "Get context handles for agent queries (returns only references, not full content)"
    )

    context_query = st.text_input(
        "Context Query", placeholder="What context do you need?"
    )
    agent_requesting = st.selectbox(
        "Agent Requesting Context",
        [
            "DemoAgent",
            "ProjectManager",
            "CodeGenerator",
            "UIDesigner",
            "TestWriter",
            "Debugger",
        ],
    )

    if st.button("Get Context Handles") and context_query.strip():
        with st.spinner("Getting context..."):
            handles = integration.get_context_for_agent(
                agent_requesting, context_query, max_contexts=5
            )

            if handles:
                st.success(
                    f"Provided {len(handles)} context handles to {agent_requesting}"
                )
                for i, handle in enumerate(handles, 1):
                    st.code(f"Handle {i}: {handle}")

                    # Show preview when handle is clicked
                    if st.button(f"Preview Handle {i}", key=f"preview_{i}"):
                        expanded = integration.expand_context_handle(handle)
                        if expanded:
                            with st.expander(f"Content Preview - {handle}"):
                                st.write(f"**Type:** {expanded['context_type']}")
                                st.write(f"**Summary:** {expanded['summary']}")
                                st.write(
                                    f"**Key Phrases:** {', '.join(expanded['key_phrases'])}"
                                )
                                st.write(
                                    f"**Importance:** {expanded['importance_score']:.2f}"
                                )
                                st.write("**Full Content:**")
                                st.text(
                                    expanded["text_content"][:300] + "..."
                                    if len(expanded["text_content"]) > 300
                                    else expanded["text_content"]
                                )
            else:
                st.info("No relevant context found")

    # Statistics
    st.header("📊 Memory Statistics")
    if st.button("Refresh Stats"):
        stats = integration.get_memory_stats()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Documents", stats["total_documents"])
        with col2:
            st.metric("Total Handles", stats["total_handles"])
        with col3:
            st.metric("OpenAI Available", "Yes" if stats["openai_available"] else "No")

        st.write("**Embedding Types:**", stats["embedding_types"])
        st.write("**Database Path:**", stats["database_path"])


if __name__ == "__main__":
    main()
