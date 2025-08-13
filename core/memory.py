"""
Project memory system for storing and retrieving agent interactions and context
"""

import json
import sqlite3
import os
from typing import Dict, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Represents a memory entry in the system"""

    entry_id: str
    timestamp: datetime
    agent_name: str
    interaction_type: str  # 'request', 'response', 'handoff', 'context'
    content: str
    metadata: Dict[str, Any]
    project_id: str = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Create from dictionary"""
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class ProjectMemory:
    """Memory system for storing project context and agent interactions"""

    def __init__(self, db_path: str = "project_memory.db"):
        self.db_path = db_path
        self.current_context: Dict[str, Any] = {}
        self.session_memory: List[MemoryEntry] = []
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for persistent memory"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS memory_entries (
                        entry_id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        agent_name TEXT NOT NULL,
                        interaction_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata TEXT,
                        project_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS project_context (
                        project_id TEXT PRIMARY KEY,
                        context_data TEXT NOT NULL,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS agent_knowledge (
                        knowledge_id TEXT PRIMARY KEY,
                        agent_name TEXT NOT NULL,
                        knowledge_type TEXT NOT NULL,
                        knowledge_data TEXT NOT NULL,
                        confidence_score REAL DEFAULT 1.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create indexes for better performance
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_timestamp ON memory_entries(timestamp)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_agent ON memory_entries(agent_name)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_project ON memory_entries(project_id)"
                )

                conn.commit()
                logger.info("Memory database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize memory database: {e}")

    def add_interaction(
        self,
        request: str,
        response: str,
        agent_name: str,
        project_id: str = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Add an agent interaction to memory"""

        entry_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now()

        # Create memory entry
        entry = MemoryEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            agent_name=agent_name,
            interaction_type="interaction",
            content=json.dumps({"request": request, "response": response}),
            metadata=metadata or {},
            project_id=project_id,
        )

        # Add to session memory
        self.session_memory.append(entry)

        # Store in database
        self._store_memory_entry(entry)

        # Update current context
        self._update_context_from_interaction(request, response, agent_name)

        logger.debug(f"Added interaction to memory: {agent_name}")
        return entry_id

    def add_handoff(
        self,
        from_agent: str,
        to_agent: str,
        content: str,
        context: Dict[str, Any] = None,
        project_id: str = None,
    ) -> str:
        """Add agent handoff to memory"""

        entry_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now()

        handoff_data = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "content": content,
            "context": context or {},
        }

        entry = MemoryEntry(
            entry_id=entry_id,
            timestamp=timestamp,
            agent_name=f"{from_agent}->{to_agent}",
            interaction_type="handoff",
            content=json.dumps(handoff_data),
            metadata={"handoff": True},
            project_id=project_id,
        )

        self.session_memory.append(entry)
        self._store_memory_entry(entry)

        logger.info(f"Added handoff to memory: {from_agent} -> {to_agent}")
        return entry_id

    def update_context(self, key: str, value: Any, agent_name: str = None):
        """Update current context"""
        self.current_context[key] = {
            "value": value,
            "updated_by": agent_name,
            "updated_at": datetime.now().isoformat(),
        }

        # Store context update in memory
        if agent_name:
            entry = MemoryEntry(
                entry_id=str(uuid.uuid4())[:8],
                timestamp=datetime.now(),
                agent_name=agent_name,
                interaction_type="context_update",
                content=json.dumps({key: value}),
                metadata={"context_key": key},
            )
            self.session_memory.append(entry)
            self._store_memory_entry(entry)

    def get_context(self, key: str = None) -> Any:
        """Get current context or specific key"""
        if key:
            context_item = self.current_context.get(key)
            return context_item["value"] if context_item else None

        # Return simplified context (just values)
        return {k: v["value"] for k, v in self.current_context.items()}

    def get_agent_history(
        self, agent_name: str, limit: int = 50, interaction_type: str = None
    ) -> List[Dict[str, Any]]:
        """Get interaction history for a specific agent"""

        # First check session memory
        session_entries = [
            entry.to_dict()
            for entry in self.session_memory
            if entry.agent_name == agent_name
            and (not interaction_type or entry.interaction_type == interaction_type)
        ]

        # Then check database for older entries
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                query = """
                    SELECT * FROM memory_entries 
                    WHERE agent_name = ?
                """
                params = [agent_name]

                if interaction_type:
                    query += " AND interaction_type = ?"
                    params.append(interaction_type)

                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                rows = conn.execute(query, params).fetchall()

                db_entries = []
                for row in rows:
                    entry_dict = dict(row)
                    entry_dict["metadata"] = json.loads(entry_dict["metadata"] or "{}")
                    db_entries.append(entry_dict)

                # Combine and deduplicate
                all_entries = session_entries + db_entries
                seen_ids = set()
                unique_entries = []

                for entry in all_entries:
                    if entry["entry_id"] not in seen_ids:
                        unique_entries.append(entry)
                        seen_ids.add(entry["entry_id"])

                # Sort by timestamp and limit
                unique_entries.sort(key=lambda x: x["timestamp"], reverse=True)
                return unique_entries[:limit]

        except Exception as e:
            logger.error(f"Error retrieving agent history: {e}")
            return session_entries[:limit]

    def get_recent_interactions(
        self, limit: int = 20, minutes_back: int = 60
    ) -> List[Dict[str, Any]]:
        """Get recent interactions across all agents"""

        cutoff_time = datetime.now() - timedelta(minutes=minutes_back)

        # Session memory
        recent_session = [
            entry.to_dict()
            for entry in self.session_memory
            if entry.timestamp >= cutoff_time
        ]

        # Database memory
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                rows = conn.execute(
                    """
                    SELECT * FROM memory_entries 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """,
                    (cutoff_time.isoformat(), limit),
                ).fetchall()

                db_entries = []
                for row in rows:
                    entry_dict = dict(row)
                    entry_dict["metadata"] = json.loads(entry_dict["metadata"] or "{}")
                    db_entries.append(entry_dict)

                # Combine and deduplicate
                all_entries = recent_session + db_entries
                seen_ids = set()
                unique_entries = []

                for entry in all_entries:
                    if entry["entry_id"] not in seen_ids:
                        unique_entries.append(entry)
                        seen_ids.add(entry["entry_id"])

                unique_entries.sort(key=lambda x: x["timestamp"], reverse=True)
                return unique_entries[:limit]

        except Exception as e:
            logger.error(f"Error retrieving recent interactions: {e}")
            return recent_session[:limit]

    def search_memory(
        self, query: str, agent_name: str = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search memory for specific content"""
        query_lower = query.lower()
        results = []

        # Search session memory
        for entry in self.session_memory:
            if query_lower in entry.content.lower():
                if not agent_name or entry.agent_name == agent_name:
                    results.append(entry.to_dict())

        # Search database
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                sql_query = """
                    SELECT * FROM memory_entries 
                    WHERE content LIKE ?
                """
                params = [f"%{query}%"]

                if agent_name:
                    sql_query += " AND agent_name = ?"
                    params.append(agent_name)

                sql_query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                rows = conn.execute(sql_query, params).fetchall()

                for row in rows:
                    entry_dict = dict(row)
                    entry_dict["metadata"] = json.loads(entry_dict["metadata"] or "{}")

                    # Avoid duplicates
                    if not any(
                        r["entry_id"] == entry_dict["entry_id"] for r in results
                    ):
                        results.append(entry_dict)

        except Exception as e:
            logger.error(f"Error searching memory: {e}")

        return results[:limit]

    def get_knowledge_for_agent(self, agent_name: str) -> Dict[str, Any]:
        """Get accumulated knowledge for a specific agent"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                rows = conn.execute(
                    """
                    SELECT * FROM agent_knowledge 
                    WHERE agent_name = ?
                    ORDER BY confidence_score DESC, created_at DESC
                """,
                    (agent_name,),
                ).fetchall()

                knowledge = {}
                for row in rows:
                    knowledge_type = row["knowledge_type"]
                    if knowledge_type not in knowledge:
                        knowledge[knowledge_type] = []

                    knowledge[knowledge_type].append(
                        {
                            "data": json.loads(row["knowledge_data"]),
                            "confidence": row["confidence_score"],
                            "created_at": row["created_at"],
                        }
                    )

                return knowledge

        except Exception as e:
            logger.error(f"Error retrieving agent knowledge: {e}")
            return {}

    def store_agent_knowledge(
        self,
        agent_name: str,
        knowledge_type: str,
        knowledge_data: Dict[str, Any],
        confidence_score: float = 1.0,
    ):
        """Store knowledge learned by an agent"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO agent_knowledge 
                    (knowledge_id, agent_name, knowledge_type, knowledge_data, confidence_score)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        str(uuid.uuid4())[:8],
                        agent_name,
                        knowledge_type,
                        json.dumps(knowledge_data),
                        confidence_score,
                    ),
                )
                conn.commit()

        except Exception as e:
            logger.error(f"Error storing agent knowledge: {e}")

    def clear_context(self):
        """Clear current context (useful for new projects)"""
        self.current_context = {}
        self.session_memory = []
        logger.info("Context and session memory cleared")

    def save_project_context(self, project_id: str):
        """Save current context to database for a project"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                context_json = json.dumps(self.current_context)

                conn.execute(
                    """
                    INSERT OR REPLACE INTO project_context 
                    (project_id, context_data, last_updated)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                    (project_id, context_json),
                )

                conn.commit()
                logger.info(f"Saved context for project {project_id}")

        except Exception as e:
            logger.error(f"Error saving project context: {e}")

    def load_project_context(self, project_id: str) -> bool:
        """Load context for a specific project"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                row = conn.execute(
                    """
                    SELECT context_data FROM project_context 
                    WHERE project_id = ?
                """,
                    (project_id,),
                ).fetchone()

                if row:
                    self.current_context = json.loads(row["context_data"])
                    logger.info(f"Loaded context for project {project_id}")
                    return True
                else:
                    logger.warning(f"No context found for project {project_id}")
                    return False

        except Exception as e:
            logger.error(f"Error loading project context: {e}")
            return False

    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Total entries
                total_entries = conn.execute(
                    "SELECT COUNT(*) FROM memory_entries"
                ).fetchone()[0]

                # Entries by agent
                agent_counts = dict(
                    conn.execute("""
                    SELECT agent_name, COUNT(*) 
                    FROM memory_entries 
                    GROUP BY agent_name
                """).fetchall()
                )

                # Entries by type
                type_counts = dict(
                    conn.execute("""
                    SELECT interaction_type, COUNT(*) 
                    FROM memory_entries 
                    GROUP BY interaction_type
                """).fetchall()
                )

                # Recent activity (last 24 hours)
                recent_cutoff = (datetime.now() - timedelta(days=1)).isoformat()
                recent_count = conn.execute(
                    """
                    SELECT COUNT(*) FROM memory_entries 
                    WHERE timestamp >= ?
                """,
                    (recent_cutoff,),
                ).fetchone()[0]

                return {
                    "total_entries": total_entries,
                    "session_entries": len(self.session_memory),
                    "context_items": len(self.current_context),
                    "entries_by_agent": agent_counts,
                    "entries_by_type": type_counts,
                    "recent_activity_24h": recent_count,
                    "database_size_kb": os.path.getsize(self.db_path) / 1024
                    if os.path.exists(self.db_path)
                    else 0,
                }

        except Exception as e:
            logger.error(f"Error getting memory statistics: {e}")
            return {"error": str(e)}

    def _store_memory_entry(self, entry: MemoryEntry):
        """Store memory entry in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO memory_entries 
                    (entry_id, timestamp, agent_name, interaction_type, content, metadata, project_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        entry.entry_id,
                        entry.timestamp.isoformat(),
                        entry.agent_name,
                        entry.interaction_type,
                        entry.content,
                        json.dumps(entry.metadata),
                        entry.project_id,
                    ),
                )
                conn.commit()

        except Exception as e:
            logger.error(f"Error storing memory entry: {e}")

    def _update_context_from_interaction(
        self, request: str, response: str, agent_name: str
    ):
        """Update context based on agent interaction"""
        # Extract key information from interactions
        request_lower = request.lower()

        # Track project files mentioned
        if "file" in request_lower or "code" in request_lower:
            self.update_context(
                "last_code_interaction",
                {
                    "agent": agent_name,
                    "request": request[:200],
                    "response_preview": response[:200],
                },
                agent_name,
            )

        # Track project goals and requirements
        if any(
            keyword in request_lower
            for keyword in ["project", "goal", "requirement", "build"]
        ):
            self.update_context(
                "project_goals",
                {"latest_goal": request[:300], "defined_by": agent_name},
                agent_name,
            )

        # Track technology decisions
        if any(
            tech in request_lower
            for tech in ["python", "javascript", "react", "vue", "fastapi"]
        ):
            tech_mentioned = [
                tech
                for tech in ["python", "javascript", "react", "vue", "fastapi"]
                if tech in request_lower
            ]
            self.update_context(
                "technologies_mentioned",
                {"technologies": tech_mentioned, "mentioned_by": agent_name},
                agent_name,
            )

    def export_memory(self, file_path: str, project_id: str = None) -> bool:
        """Export memory to JSON file"""
        try:
            export_data = {
                "current_context": self.current_context,
                "session_memory": [entry.to_dict() for entry in self.session_memory],
                "export_timestamp": datetime.now().isoformat(),
            }

            # Add database entries if project_id specified
            if project_id:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    rows = conn.execute(
                        """
                        SELECT * FROM memory_entries 
                        WHERE project_id = ?
                        ORDER BY timestamp
                    """,
                        (project_id,),
                    ).fetchall()

                    export_data["project_memory"] = [dict(row) for row in rows]

            with open(file_path, "w") as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Memory exported to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting memory: {e}")
            return False

    def import_memory(self, file_path: str) -> bool:
        """Import memory from JSON file"""
        try:
            with open(file_path, "r") as f:
                import_data = json.load(f)

            # Import context
            if "current_context" in import_data:
                self.current_context.update(import_data["current_context"])

            # Import session memory
            if "session_memory" in import_data:
                for entry_dict in import_data["session_memory"]:
                    entry = MemoryEntry.from_dict(entry_dict)
                    self.session_memory.append(entry)

            # Import project memory to database
            if "project_memory" in import_data:
                with sqlite3.connect(self.db_path) as conn:
                    for entry_dict in import_data["project_memory"]:
                        conn.execute(
                            """
                            INSERT OR REPLACE INTO memory_entries 
                            (entry_id, timestamp, agent_name, interaction_type, content, metadata, project_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                entry_dict["entry_id"],
                                entry_dict["timestamp"],
                                entry_dict["agent_name"],
                                entry_dict["interaction_type"],
                                entry_dict["content"],
                                entry_dict["metadata"],
                                entry_dict["project_id"],
                            ),
                        )
                    conn.commit()

            logger.info(f"Memory imported from {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error importing memory: {e}")
            return False
