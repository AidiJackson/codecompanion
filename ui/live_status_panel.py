"""
Live Status Panel for Real-time System Monitoring

Provides real-time status information including:
- Event bus connectivity and configuration
- AI model availability 
- Database artifact polling with live timeline
- System health monitoring
"""

import streamlit as st
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

from settings import settings
from storage.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class LiveStatusPanel:
    """Real-time status panel with database polling and system monitoring"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.last_poll_time = None
        logger.info("📊 LiveStatusPanel initialized")
    
    def get_event_bus_status(self) -> Dict[str, Any]:
        """Get current event bus status and connectivity"""
        status = {
            "type": settings.EVENT_BUS,
            "redis_connected": False,
            "health": "unknown"
        }
        
        if settings.EVENT_BUS == "redis" and settings.REDIS_URL:
            try:
                from bus import bus
                # Try to ping Redis through the bus
                import asyncio
                import redis
                
                client = redis.from_url(str(settings.REDIS_URL), decode_responses=True)
                client.ping()
                status["redis_connected"] = True
                status["health"] = "healthy"
                
            except Exception as e:
                logger.warning(f"Redis health check failed: {e}")
                status["redis_connected"] = False
                status["health"] = "unreachable"
        
        elif settings.EVENT_BUS == "mock":
            status["health"] = "mock_mode"
            
        return status
    
    def get_ai_models_status(self) -> Dict[str, bool]:
        """Get AI model availability from settings"""
        return settings.get_available_models()
    
    def get_recent_artifacts(self, task_id: Optional[str] = None, 
                           hours_back: int = 24) -> List[Dict[str, Any]]:
        """Poll database for recent artifacts with live updates"""
        
        try:
            # Calculate time threshold
            since_time = datetime.now() - timedelta(hours=hours_back)
            
            # Query database for recent artifacts
            artifacts = self.db_manager.get_recent_artifacts(
                since_timestamp=since_time,
                task_id=task_id
            )
            
            # Convert to display format
            artifact_list = []
            for artifact in artifacts:
                artifact_list.append({
                    "id": artifact.get("id", "unknown"),
                    "type": artifact.get("artifact_type", "unknown"),
                    "agent": artifact.get("agent_name", "system"),
                    "confidence": artifact.get("confidence_score", 0.0),
                    "created_at": artifact.get("created_at", datetime.now()),
                    "content_length": len(str(artifact.get("content", ""))),
                    "metadata": artifact.get("metadata", {}),
                    "quality_score": artifact.get("quality_score", 0.0)
                })
            
            self.last_poll_time = datetime.now()
            logger.debug(f"📊 Polled {len(artifact_list)} artifacts from database")
            
            return sorted(artifact_list, key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"❌ Error polling artifacts: {e}")
            return []
    
    def get_evaluation_reports(self, task_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get evaluation reports with error highlighting"""
        
        try:
            artifacts = self.get_recent_artifacts(task_id=task_id)
            
            # Filter for evaluation reports
            eval_reports = []
            for artifact in artifacts:
                if artifact["type"] in ["evaluation", "review", "error_report"]:
                    
                    # Check for errors in content or metadata
                    has_errors = False
                    error_count = 0
                    
                    metadata = artifact.get("metadata", {})
                    if isinstance(metadata, dict):
                        has_errors = metadata.get("has_errors", False)
                        error_count = metadata.get("error_count", 0)
                    
                    eval_reports.append({
                        **artifact,
                        "has_errors": has_errors,
                        "error_count": error_count,
                        "severity": metadata.get("severity", "info")
                    })
            
            return eval_reports
            
        except Exception as e:
            logger.error(f"❌ Error getting evaluation reports: {e}")
            return []
    
    def render_status_panel(self):
        """Render the live status panel in Streamlit"""
        
        st.subheader("🔍 Live System Status")
        
        # Create columns for status information
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Event Bus**")
            bus_status = self.get_event_bus_status()
            
            if bus_status["health"] == "healthy":
                st.success(f"✅ {bus_status['type'].upper()}")
                st.write(f"Redis: {'Connected' if bus_status['redis_connected'] else 'Disconnected'}")
            elif bus_status["health"] == "mock_mode":
                st.warning("⚠️ MOCK MODE")
                st.write("Development only")
            else:
                st.error(f"❌ {bus_status['type'].upper()}")
                st.write("Connection failed")
        
        with col2:
            st.write("**AI Models**")
            models = self.get_ai_models_status()
            
            model_names = {"claude": "Claude", "gpt-4": "GPT-4", "gemini": "Gemini"}
            available_count = sum(models.values())
            
            if available_count == len(models):
                st.success(f"✅ All Models ({available_count}/3)")
            elif available_count > 0:
                st.warning(f"⚠️ Partial ({available_count}/3)")
            else:
                st.error("❌ No Models")
            
            for key, name in model_names.items():
                status = "🟢" if models.get(key, False) else "🔴"
                st.write(f"{status} {name}")
        
        with col3:
            st.write("**Database**")
            try:
                # Test database connectivity
                artifacts_count = len(self.get_recent_artifacts(hours_back=24))
                st.success("✅ Connected")
                st.write(f"Recent artifacts: {artifacts_count}")
                
                if self.last_poll_time:
                    st.write(f"Last polled: {self.last_poll_time.strftime('%H:%M:%S')}")
                    
            except Exception as e:
                st.error("❌ Database Error")
                st.write(str(e)[:50])
    
    def render_live_timeline(self, task_id: Optional[str] = None, auto_refresh: bool = True):
        """Render live timeline of artifacts with auto-refresh"""
        
        st.subheader("📊 Live Artifact Timeline")
        
        # Auto-refresh controls
        if auto_refresh:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write("Auto-refreshing every 1 second...")
            with col2:
                if st.button("🔄 Refresh Now"):
                    st.rerun()
        
        # Get recent artifacts
        artifacts = self.get_recent_artifacts(task_id=task_id)
        
        if not artifacts:
            st.info("No artifacts found. Waiting for AI agents to produce results...")
            if auto_refresh:
                time.sleep(1)
                st.rerun()
            return
        
        # Display artifacts in timeline format
        for i, artifact in enumerate(artifacts):
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
                
                with col1:
                    # Artifact type and agent
                    type_emoji = {
                        "code": "💻",
                        "documentation": "📖", 
                        "design": "🎨",
                        "test": "🧪",
                        "evaluation": "📋",
                        "error_report": "⚠️"
                    }
                    emoji = type_emoji.get(artifact["type"], "📄")
                    
                    st.write(f"{emoji} **{artifact['type'].title()}**")
                    st.write(f"by {artifact['agent']}")
                
                with col2:
                    # Quality metrics
                    confidence = artifact["confidence"]
                    quality = artifact["quality_score"]
                    
                    if confidence > 0.8:
                        st.success(f"Confidence: {confidence:.1%}")
                    elif confidence > 0.6:
                        st.warning(f"Confidence: {confidence:.1%}")
                    else:
                        st.error(f"Confidence: {confidence:.1%}")
                    
                    if quality > 0:
                        st.write(f"Quality: {quality:.1f}/10")
                
                with col3:
                    # Timing information
                    created_at = artifact["created_at"]
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    
                    time_ago = datetime.now() - created_at
                    if time_ago.total_seconds() < 60:
                        st.write(f"🕐 {int(time_ago.total_seconds())}s ago")
                    elif time_ago.total_seconds() < 3600:
                        st.write(f"🕐 {int(time_ago.total_seconds()//60)}m ago")
                    else:
                        st.write(f"🕐 {created_at.strftime('%H:%M')}")
                
                with col4:
                    # Content info and actions
                    content_len = artifact["content_length"]
                    st.write(f"📏 {content_len} chars")
                    
                    if st.button(f"View Details", key=f"details_{artifact['id']}"):
                        # Show artifact details in expander
                        with st.expander(f"Artifact Details - {artifact['id']}", expanded=True):
                            st.json({
                                "id": artifact["id"],
                                "type": artifact["type"],
                                "agent": artifact["agent"],
                                "created_at": str(artifact["created_at"]),
                                "metadata": artifact["metadata"]
                            })
                
                st.divider()
        
        # Auto-refresh mechanism
        if auto_refresh and len(artifacts) > 0:
            time.sleep(1)
            st.rerun()
    
    def render_evaluation_alerts(self, task_id: Optional[str] = None):
        """Render prominent alerts for evaluation reports with errors"""
        
        eval_reports = self.get_evaluation_reports(task_id=task_id)
        error_reports = [r for r in eval_reports if r.get("has_errors", False)]
        
        if error_reports:
            st.error("🚨 **Evaluation Errors Detected**")
            
            for report in error_reports:
                with st.expander(f"❌ Error Report - {report['agent']}", expanded=True):
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.write(f"**Errors:** {report.get('error_count', 0)}")
                        st.write(f"**Severity:** {report.get('severity', 'unknown').upper()}")
                        st.write(f"**Time:** {report['created_at']}")
                    
                    with col2:
                        st.write(f"**Agent:** {report['agent']}")
                        st.write(f"**Type:** {report['type']}")
                        st.write(f"**ID:** {report['id']}")
                    
                    if report.get("metadata", {}):
                        st.json(report["metadata"])


def render_live_monitoring_dashboard(db_manager: DatabaseManager, 
                                   task_id: Optional[str] = None):
    """Main function to render the complete live monitoring dashboard"""
    
    # Initialize status panel
    status_panel = LiveStatusPanel(db_manager)
    
    # Render all components
    status_panel.render_status_panel()
    
    st.divider()
    
    # Check for evaluation errors first
    status_panel.render_evaluation_alerts(task_id=task_id)
    
    # Render live timeline
    status_panel.render_live_timeline(task_id=task_id, auto_refresh=True)


if __name__ == "__main__":
    # Test the status panel
    import logging
    logging.basicConfig(level=logging.INFO)
    
    from storage.database_manager import DatabaseManager
    
    db = DatabaseManager()
    
    print("Testing LiveStatusPanel...")
    
    panel = LiveStatusPanel(db)
    
    print("Event bus status:", panel.get_event_bus_status())
    print("AI models status:", panel.get_ai_models_status())
    print("Recent artifacts:", len(panel.get_recent_artifacts()))