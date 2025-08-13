"""
Stability monitoring and health checks for the multi-agent system
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any
from utils.error_handler import logger, rate_limiter
from utils.session_manager import get_session_value, session_manager


class StabilityMonitor:
    """Monitor system stability and performance"""

    def __init__(self):
        self.health_checks = []
        self.performance_metrics = {}
        self.last_check = None

    def run_health_checks(self) -> Dict[str, Any]:
        """Run comprehensive health checks"""
        results = {
            "overall_health": "healthy",
            "checks": {},
            "warnings": [],
            "errors": [],
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Check session state health
            session_health = self._check_session_health()
            results["checks"]["session"] = session_health

            # Check agent health
            agent_health = self._check_agent_health()
            results["checks"]["agents"] = agent_health

            # Check memory usage
            memory_health = self._check_memory_health()
            results["checks"]["memory"] = memory_health

            # Check API rate limiting
            api_health = self._check_api_health()
            results["checks"]["api"] = api_health

            # Check error rates
            error_health = self._check_error_rates()
            results["checks"]["errors"] = error_health

            # Determine overall health
            failed_checks = [
                k for k, v in results["checks"].items() if not v.get("healthy", False)
            ]

            if len(failed_checks) > 2:
                results["overall_health"] = "critical"
                results["errors"].append(
                    f"Multiple system failures: {', '.join(failed_checks)}"
                )
            elif len(failed_checks) > 0:
                results["overall_health"] = "warning"
                results["warnings"].extend(
                    [f"{check} needs attention" for check in failed_checks]
                )

            self.last_check = datetime.now()
            return results

        except Exception as e:
            logger.error(f"Error during health checks: {str(e)}")
            return {
                "overall_health": "critical",
                "checks": {},
                "warnings": [],
                "errors": [f"Health check system failure: {str(e)}"],
                "timestamp": datetime.now().isoformat(),
            }

    def _check_session_health(self) -> Dict[str, Any]:
        """Check session state health"""
        try:
            validation_results = session_manager.validate_state()
            failed_validations = [k for k, v in validation_results.items() if not v]

            return {
                "healthy": len(failed_validations) == 0,
                "details": f"Session validation: {len(failed_validations)} failures",
                "failed_keys": failed_validations,
                "total_keys": len(validation_results),
            }
        except Exception as e:
            return {
                "healthy": False,
                "details": f"Session check failed: {str(e)}",
                "error": str(e),
            }

    def _check_agent_health(self) -> Dict[str, Any]:
        """Check agent system health"""
        try:
            agents = get_session_value("agents", {})
            orchestrator = get_session_value("orchestrator")

            agent_count = len(agents)
            orchestrator_ready = orchestrator is not None

            return {
                "healthy": agent_count >= 5 and orchestrator_ready,
                "details": f"Agents: {agent_count}/5, Orchestrator: {'Ready' if orchestrator_ready else 'Not Ready'}",
                "agent_count": agent_count,
                "orchestrator_ready": orchestrator_ready,
            }
        except Exception as e:
            return {
                "healthy": False,
                "details": f"Agent check failed: {str(e)}",
                "error": str(e),
            }

    def _check_memory_health(self) -> Dict[str, Any]:
        """Check memory usage and cleanup needs"""
        try:
            chat_history = get_session_value("chat_history", [])
            project_files = get_session_value("project_files", {})

            chat_size = len(chat_history)
            files_size = len(project_files)

            # Calculate approximate memory usage
            total_content_size = sum(
                len(str(msg.get("content", ""))) for msg in chat_history
            )
            total_content_size += sum(
                len(str(content)) for content in project_files.values()
            )

            memory_critical = total_content_size > 2000000  # 2MB
            memory_warning = total_content_size > 1000000  # 1MB

            return {
                "healthy": not memory_critical,
                "details": f"Chat: {chat_size} msgs, Files: {files_size}, Size: {total_content_size / 1000:.1f}KB",
                "needs_cleanup": memory_warning,
                "critical": memory_critical,
                "content_size": total_content_size,
            }
        except Exception as e:
            return {
                "healthy": False,
                "details": f"Memory check failed: {str(e)}",
                "error": str(e),
            }

    def _check_api_health(self) -> Dict[str, Any]:
        """Check API rate limiting and availability"""
        try:
            # Check rate limiter status
            active_limits = len(rate_limiter.retry_counts)
            failed_services = list(rate_limiter.retry_counts.keys())

            return {
                "healthy": active_limits == 0,
                "details": f"Rate limited services: {active_limits}",
                "failed_services": failed_services,
                "retry_counts": dict(rate_limiter.retry_counts),
            }
        except Exception as e:
            return {
                "healthy": False,
                "details": f"API check failed: {str(e)}",
                "error": str(e),
            }

    def _check_error_rates(self) -> Dict[str, Any]:
        """Check error rates and patterns"""
        try:
            error_count = get_session_value("error_count", 0)
            session_info = session_manager.get_session_info()

            error_rate_critical = error_count > 10
            error_rate_warning = error_count > 5

            return {
                "healthy": not error_rate_critical,
                "details": f"Error count: {error_count}",
                "error_count": error_count,
                "warning_threshold": error_rate_warning,
                "critical_threshold": error_rate_critical,
                "session_age": session_info.get("initialized_at", "unknown"),
            }
        except Exception as e:
            return {
                "healthy": False,
                "details": f"Error rate check failed: {str(e)}",
                "error": str(e),
            }

    def render_health_dashboard(self):
        """Render health monitoring dashboard"""
        st.markdown("## 🏥 System Health Monitor")

        # Run health checks
        health_results = self.run_health_checks()

        # Overall status
        overall_health = health_results["overall_health"]
        status_colors = {"healthy": "🟢", "warning": "🟡", "critical": "🔴"}

        status_messages = {
            "healthy": "All systems operational",
            "warning": "Some issues detected",
            "critical": "Critical issues require attention",
        }

        st.markdown(
            f"### {status_colors[overall_health]} System Status: {status_messages[overall_health]}"
        )

        # Display individual checks
        if health_results["checks"]:
            cols = st.columns(len(health_results["checks"]))

            for i, (check_name, check_result) in enumerate(
                health_results["checks"].items()
            ):
                with cols[i]:
                    healthy = check_result.get("healthy", False)
                    icon = "✅" if healthy else "❌"
                    st.metric(
                        f"{icon} {check_name.title()}",
                        "Healthy" if healthy else "Issues",
                        help=check_result.get("details", "No details"),
                    )

        # Warnings and errors
        if health_results["warnings"]:
            st.warning("**Warnings:**")
            for warning in health_results["warnings"]:
                st.warning(f"⚠️ {warning}")

        if health_results["errors"]:
            st.error("**Critical Issues:**")
            for error in health_results["errors"]:
                st.error(f"🚨 {error}")

        # Auto-fix suggestions
        if overall_health != "healthy":
            st.markdown("### 🔧 Suggested Actions")

            if any("memory" in check for check in health_results["checks"]):
                if st.button("🧹 Clean Memory"):
                    session_manager.cleanup_memory()
                    st.success("Memory cleanup completed")
                    st.rerun()

            if any("session" in check for check in health_results["checks"]):
                if st.button("🔄 Reset Problematic State"):
                    from utils.session_manager import partial_reset

                    partial_reset()
                    st.success("Partial reset completed")
                    st.rerun()

            if health_results["overall_health"] == "critical":
                st.error("System is in critical state. Emergency reset recommended.")
                if st.button("🚨 Emergency Reset"):
                    from utils.session_manager import emergency_reset

                    emergency_reset()
                    st.success("Emergency reset completed")
                    st.rerun()

        # Performance metrics
        with st.expander("📊 Detailed Metrics", expanded=False):
            st.json(health_results)


# Global monitor instance
stability_monitor = StabilityMonitor()


def render_stability_monitor():
    """Render the stability monitoring interface"""
    return stability_monitor.render_health_dashboard()


def check_system_health() -> Dict[str, Any]:
    """Quick health check function"""
    return stability_monitor.run_health_checks()
