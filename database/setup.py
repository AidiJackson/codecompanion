"""
Database Setup and Initialization Module

Creates SQLite database with required tables for persistence, learning, and state management.
"""

import sqlite3
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def initialize_database(db_path: str = "data/codecompanion.db") -> str:
    """
    Create SQLite database with required tables
    
    Args:
        db_path: Path to the database file
        
    Returns:
        Path to the created database
    """
    db_path_obj = Path(db_path)
    db_path_obj.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Agent Performance Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                success_rate REAL DEFAULT 0.0,
                avg_quality_score REAL DEFAULT 0.0,
                total_executions INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(model_name, task_type)
            )
        """)
        
        # Artifacts Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                quality_score REAL DEFAULT 0.0,
                word_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Project Sessions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                project_description TEXT,
                project_type TEXT,
                complexity TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                total_artifacts INTEGER DEFAULT 0,
                total_events INTEGER DEFAULT 0
            )
        """)
        
        # Bandit Learning Table  
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bandit_arms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                task_category TEXT NOT NULL,
                alpha REAL DEFAULT 1.0,
                beta REAL DEFAULT 1.0,
                total_pulls INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                reward_sum REAL DEFAULT 0.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(model_name, task_category)
            )
        """)
        
        # Timeline Events Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timeline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                event_message TEXT NOT NULL,
                agent_name TEXT,
                event_type TEXT DEFAULT 'info',
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Quality Metrics Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                artifact_id INTEGER,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                evaluation_method TEXT,
                evaluated_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (artifact_id) REFERENCES artifacts (id)
            )
        """)
        
        # Model Router Performance Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS router_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                routing_decision TEXT NOT NULL,
                task_type TEXT NOT NULL,
                complexity_level TEXT,
                chosen_model TEXT NOT NULL,
                alternative_models TEXT,
                execution_time REAL,
                success BOOLEAN,
                quality_score REAL,
                cost_efficiency REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Learning Outcomes Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                task_type TEXT NOT NULL,
                input_context TEXT,
                output_result TEXT,
                quality_feedback REAL,
                user_feedback TEXT,
                improvement_suggestions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_project_id ON artifacts(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_agent_name ON artifacts(agent_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeline_session_id ON timeline_events(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_performance_model ON agent_performance(model_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bandit_arms_model ON bandit_arms(model_name, task_category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_router_performance_model ON router_performance(chosen_model)")
        
        conn.commit()
        logger.info(f"✅ Database initialized successfully at {db_path}")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    finally:
        conn.close()
    
    return db_path


def reset_database(db_path: str = "data/codecompanion.db"):
    """
    Reset database by dropping all tables and recreating them
    
    Args:
        db_path: Path to the database file
    """
    db_path_obj = Path(db_path)
    
    if db_path_obj.exists():
        db_path_obj.unlink()
        logger.info(f"Deleted existing database at {db_path}")
    
    initialize_database(db_path)
    logger.info("Database reset completed")


if __name__ == "__main__":
    # Initialize database when run directly
    initialize_database()