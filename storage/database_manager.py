"""
Database Manager for CodeCompanion Orchestra

Provides a comprehensive interface for database operations including:
- Artifact management
- Timeline events
- Agent performance tracking
- Learning outcomes
- Quality metrics
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Central database manager for all persistence operations
    """
    
    def __init__(self, db_path: str = "data/codecompanion.db"):
        self.db_path = db_path
        self.initialize_db()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def initialize_db(self):
        """Initialize database if it doesn't exist"""
        try:
            from database.setup import initialize_database
            initialize_database(self.db_path)
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    # ==================== ARTIFACT MANAGEMENT ====================
    
    def save_artifact(self, project_id: str, artifact_type: str, title: str, 
                     content: str, agent_name: str, quality_score: float = 0.0) -> int:
        """
        Save AI-generated artifact to database
        
        Returns:
            artifact_id: ID of the saved artifact
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            word_count = len(content.split()) if content else 0
            
            cursor.execute("""
                INSERT INTO artifacts (project_id, artifact_type, title, content, 
                                     agent_name, quality_score, word_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (project_id, artifact_type, title, content, agent_name, 
                  quality_score, word_count))
            
            artifact_id = cursor.lastrowid or 0
            
            # Update project session artifact count
            cursor.execute("""
                UPDATE project_sessions 
                SET total_artifacts = total_artifacts + 1
                WHERE session_id = ?
            """, (project_id,))
            
            conn.commit()
            logger.info(f"Saved artifact '{title}' by {agent_name} (ID: {artifact_id})")
            return artifact_id
            
        except Exception as e:
            logger.error(f"Failed to save artifact: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_recent_artifacts(self, since_timestamp: Optional[datetime] = None,
                           task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent artifacts with optional filtering by time and task ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = """
                SELECT id, artifact_type, title, content, agent_name, 
                       quality_score, word_count, created_at, 
                       COALESCE(metadata, '{}') as metadata,
                       COALESCE(0.8, quality_score/10.0) as confidence_score
                FROM artifacts 
                WHERE 1=1
            """
            params = []
            
            if since_timestamp:
                query += " AND created_at >= ?"
                params.append(since_timestamp.isoformat())
            
            if task_id:
                query += " AND (metadata LIKE ? OR title LIKE ?)"
                params.extend([f'%{task_id}%', f'%{task_id}%'])
                
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            artifacts = []
            for row in rows:
                # Parse metadata if it's a JSON string
                metadata = row['metadata']
                if isinstance(metadata, str) and metadata.strip():
                    try:
                        metadata = json.loads(metadata)
                    except json.JSONDecodeError:
                        metadata = {}
                else:
                    metadata = {}
                
                artifacts.append({
                    'id': row['id'],
                    'artifact_type': row['artifact_type'],
                    'title': row['title'],
                    'content': row['content'],
                    'agent_name': row['agent_name'],
                    'quality_score': row['quality_score'],
                    'confidence_score': row['confidence_score'],
                    'word_count': row['word_count'],
                    'created_at': row['created_at'],
                    'metadata': metadata
                })
            
            return artifacts
            
        except Exception as e:
            logger.error(f"Error fetching recent artifacts: {e}")
            return []
        finally:
            conn.close()

    def get_project_artifacts(self, project_id: str) -> List[Dict]:
        """Get all artifacts for a project"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, title, content, agent_name, quality_score, 
                       created_at, word_count, artifact_type
                FROM artifacts 
                WHERE project_id = ?
                ORDER BY created_at DESC
            """, (project_id,))
            
            artifacts = []
            for row in cursor.fetchall():
                artifacts.append({
                    'id': row['id'],
                    'title': row['title'],
                    'content': row['content'],
                    'agent_name': row['agent_name'],
                    'quality_score': row['quality_score'],
                    'created_at': row['created_at'],
                    'word_count': row['word_count'],
                    'artifact_type': row['artifact_type']
                })
            
            return artifacts
            
        except Exception as e:
            logger.error(f"Failed to get project artifacts: {e}")
            return []
        finally:
            conn.close()
    
    def update_artifact_quality(self, artifact_id: int, quality_score: float):
        """Update quality score for an artifact"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE artifacts 
                SET quality_score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (quality_score, artifact_id))
            
            conn.commit()
            logger.info(f"Updated quality score for artifact {artifact_id}: {quality_score}")
            
        except Exception as e:
            logger.error(f"Failed to update artifact quality: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    # ==================== TIMELINE EVENTS ====================
    
    def save_timeline_event(self, session_id: str, timestamp: str, 
                           message: str, agent_name: Optional[str] = None, 
                           event_type: str = "info", metadata: Optional[Dict] = None) -> int:
        """Save timeline event to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO timeline_events (session_id, timestamp, event_message, 
                                           agent_name, event_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, timestamp, message, agent_name, event_type, metadata_json))
            
            event_id = cursor.lastrowid or 0
            
            # Update project session event count
            cursor.execute("""
                UPDATE project_sessions 
                SET total_events = total_events + 1
                WHERE session_id = ?
            """, (session_id,))
            
            conn.commit()
            logger.debug(f"Saved timeline event for session {session_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to save timeline event: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_timeline_events(self, session_id: str, limit: int = 100) -> List[Dict]:
        """Get timeline events for a session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT timestamp, event_message, agent_name, event_type, 
                       metadata, created_at
                FROM timeline_events 
                WHERE session_id = ?
                ORDER BY created_at ASC
                LIMIT ?
            """, (session_id, limit))
            
            events = []
            for row in cursor.fetchall():
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                events.append({
                    'timestamp': row['timestamp'],
                    'message': row['event_message'],
                    'agent_name': row['agent_name'],
                    'event_type': row['event_type'],
                    'metadata': metadata,
                    'created_at': row['created_at']
                })
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get timeline events: {e}")
            return []
        finally:
            conn.close()
    
    # ==================== AGENT PERFORMANCE ====================
    
    def update_agent_performance(self, model_name: str, task_type: str, 
                                success: bool, quality_score: float = 0.0):
        """Update agent performance metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get current stats
            cursor.execute("""
                SELECT total_executions, success_count, avg_quality_score
                FROM agent_performance 
                WHERE model_name = ? AND task_type = ?
            """, (model_name, task_type))
            
            row = cursor.fetchone()
            
            if row:
                total_executions = row['total_executions']
                success_count = row['success_count']
                avg_quality = row['avg_quality_score']
                
                new_total = total_executions + 1
                new_success = success_count + (1 if success else 0)
                new_avg_quality = ((avg_quality * total_executions) + quality_score) / new_total
                new_success_rate = new_success / new_total
                
                cursor.execute("""
                    UPDATE agent_performance 
                    SET success_rate = ?, avg_quality_score = ?, 
                        total_executions = ?, success_count = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE model_name = ? AND task_type = ?
                """, (new_success_rate, new_avg_quality, new_total, new_success,
                      model_name, task_type))
            else:
                # Insert new record
                success_rate = 1.0 if success else 0.0
                cursor.execute("""
                    INSERT INTO agent_performance 
                    (model_name, task_type, success_rate, avg_quality_score, 
                     total_executions, success_count)
                    VALUES (?, ?, ?, ?, 1, ?)
                """, (model_name, task_type, success_rate, quality_score, 
                      1 if success else 0))
            
            conn.commit()
            logger.info(f"Updated performance for {model_name} on {task_type}")
            
        except Exception as e:
            logger.error(f"Failed to update agent performance: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_agent_performance(self, model_name: Optional[str] = None) -> List[Dict]:
        """Get agent performance metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if model_name:
                cursor.execute("""
                    SELECT model_name, task_type, success_rate, avg_quality_score,
                           total_executions, success_count, last_updated
                    FROM agent_performance 
                    WHERE model_name = ?
                    ORDER BY total_executions DESC
                """, (model_name,))
            else:
                cursor.execute("""
                    SELECT model_name, task_type, success_rate, avg_quality_score,
                           total_executions, success_count, last_updated
                    FROM agent_performance 
                    ORDER BY total_executions DESC
                """)
            
            performance = []
            for row in cursor.fetchall():
                performance.append({
                    'model_name': row['model_name'],
                    'task_type': row['task_type'],
                    'success_rate': row['success_rate'],
                    'avg_quality_score': row['avg_quality_score'],
                    'total_executions': row['total_executions'],
                    'success_count': row['success_count'],
                    'last_updated': row['last_updated']
                })
            
            return performance
            
        except Exception as e:
            logger.error(f"Failed to get agent performance: {e}")
            return []
        finally:
            conn.close()
    
    # ==================== PROJECT SESSIONS ====================
    
    def create_project_session(self, session_id: Optional[str] = None, project_description: Optional[str] = None,
                              project_type: Optional[str] = None, complexity: Optional[str] = None) -> str:
        """Create a new project session"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO project_sessions 
                (session_id, project_description, project_type, complexity)
                VALUES (?, ?, ?, ?)
            """, (session_id, project_description, project_type, complexity))
            
            conn.commit()
            logger.info(f"Created project session: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create project session: {e}")
            raise
        finally:
            conn.close()
    
    def get_project_session(self, session_id: str) -> Optional[Dict]:
        """Get project session information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT session_id, project_description, project_type, complexity,
                       status, created_at, completed_at, total_artifacts, total_events
                FROM project_sessions 
                WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'session_id': row['session_id'],
                    'project_description': row['project_description'],
                    'project_type': row['project_type'],
                    'complexity': row['complexity'],
                    'status': row['status'],
                    'created_at': row['created_at'],
                    'completed_at': row['completed_at'],
                    'total_artifacts': row['total_artifacts'],
                    'total_events': row['total_events']
                }
            return None
            
        except Exception as e:
            logger.error(f"Failed to get project session: {e}")
            return None
        finally:
            conn.close()
    
    def complete_project_session(self, session_id: str):
        """Mark project session as completed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE project_sessions 
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            """, (session_id,))
            
            conn.commit()
            logger.info(f"Completed project session: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to complete project session: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    # ==================== BANDIT LEARNING ====================
    
    def update_bandit_arm(self, model_name: str, task_category: str, 
                         success: bool, reward: Optional[float] = None):
        """Update bandit learning parameters"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get current parameters
            cursor.execute("""
                SELECT alpha, beta, total_pulls, success_count, reward_sum
                FROM bandit_arms 
                WHERE model_name = ? AND task_category = ?
            """, (model_name, task_category))
            
            row = cursor.fetchone()
            reward = reward if reward is not None else (1.0 if success else 0.0)
            
            if row:
                alpha = row['alpha']
                beta = row['beta']
                total_pulls = row['total_pulls']
                success_count = row['success_count']
                reward_sum = row['reward_sum']
                
                # Update parameters (Beta distribution)
                new_alpha = alpha + (1 if success else 0)
                new_beta = beta + (0 if success else 1)
                new_total = total_pulls + 1
                new_success = success_count + (1 if success else 0)
                new_reward_sum = reward_sum + reward
                
                cursor.execute("""
                    UPDATE bandit_arms 
                    SET alpha = ?, beta = ?, total_pulls = ?, 
                        success_count = ?, reward_sum = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE model_name = ? AND task_category = ?
                """, (new_alpha, new_beta, new_total, new_success, new_reward_sum,
                      model_name, task_category))
            else:
                # Insert new arm
                alpha = 1.0 + (1 if success else 0)
                beta = 1.0 + (0 if success else 1)
                
                cursor.execute("""
                    INSERT INTO bandit_arms 
                    (model_name, task_category, alpha, beta, total_pulls, 
                     success_count, reward_sum)
                    VALUES (?, ?, ?, ?, 1, ?, ?)
                """, (model_name, task_category, alpha, beta, 
                      1 if success else 0, reward))
            
            conn.commit()
            logger.debug(f"Updated bandit arm: {model_name} - {task_category}")
            
        except Exception as e:
            logger.error(f"Failed to update bandit arm: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_bandit_arms(self) -> List[Dict]:
        """Get all bandit arms for learning"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT model_name, task_category, alpha, beta, total_pulls,
                       success_count, reward_sum, last_updated
                FROM bandit_arms 
                ORDER BY total_pulls DESC
            """)
            
            arms = []
            for row in cursor.fetchall():
                arms.append({
                    'model_name': row['model_name'],
                    'task_category': row['task_category'],
                    'alpha': row['alpha'],
                    'beta': row['beta'],
                    'total_pulls': row['total_pulls'],
                    'success_count': row['success_count'],
                    'reward_sum': row['reward_sum'],
                    'last_updated': row['last_updated']
                })
            
            return arms
            
        except Exception as e:
            logger.error(f"Failed to get bandit arms: {e}")
            return []
        finally:
            conn.close()
    
    # ==================== UTILITY METHODS ====================
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        try:
            # Count records in each table
            # Using whitelist of valid table names for security
            valid_tables = {'artifacts', 'timeline_events', 'agent_performance', 
                           'project_sessions', 'bandit_arms', 'quality_metrics'}
            tables = ['artifacts', 'timeline_events', 'agent_performance', 
                     'project_sessions', 'bandit_arms', 'quality_metrics']
            
            for table in tables:
                # Validate table name against whitelist
                if table not in valid_tables:
                    logger.warning(f"Skipping invalid table name: {table}")
                    continue
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()['count']
            
            # Get recent activity
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM artifacts 
                WHERE created_at >= date('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """)
            
            stats['recent_artifacts'] = [
                {'date': row['date'], 'count': row['count']} 
                for row in cursor.fetchall()
            ]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
        finally:
            conn.close()
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Cleanup old data to maintain database performance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Clean old timeline events
            cursor.execute("""
                DELETE FROM timeline_events 
                WHERE created_at < date('now', '-' || ? || ' days')
            """, (days_to_keep,))
            
            deleted_events = cursor.rowcount
            
            # Clean old quality metrics
            cursor.execute("""
                DELETE FROM quality_metrics 
                WHERE created_at < date('now', '-' || ? || ' days')
            """, (days_to_keep,))
            
            deleted_metrics = cursor.rowcount
            
            conn.commit()
            logger.info(f"Cleaned up {deleted_events} events and {deleted_metrics} metrics")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            conn.rollback()
        finally:
            conn.close()