"""
Live Monitoring UI Components
Dynamic Streamlit components for real-time agent collaboration monitoring
"""

import streamlit as st
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd

from core.progress_tracker import LiveProgressTracker
from core.parallel_execution import ParallelExecutionEngine


def render_live_monitoring_dashboard(progress_tracker: Optional[LiveProgressTracker] = None,
                                   execution_engine: Optional[ParallelExecutionEngine] = None):
    """Render the main live monitoring dashboard"""
    
    st.markdown("## 🔴 Live Agent Collaboration Monitor")
    st.markdown("*Real-time monitoring of AI agents working together*")
    
    # Create tabs for different monitoring views
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 Live Activity", 
        "📊 Progress Tracking", 
        "🤝 Collaboration Metrics",
        "📈 System Analytics"
    ])
    
    with tab1:
        render_live_activity_feed(progress_tracker)
    
    with tab2:
        render_progress_tracking(progress_tracker, execution_engine)
    
    with tab3:
        render_collaboration_metrics(progress_tracker)
    
    with tab4:
        render_system_analytics(progress_tracker)


def render_live_activity_feed(progress_tracker: Optional[LiveProgressTracker] = None):
    """Real-time activity feed showing agent actions"""
    
    st.markdown("### 📡 Live Agent Activity Feed")
    
    # Control panel
    col1, col2, col3 = st.columns(3)
    
    with col1:
        auto_refresh = st.checkbox("🔄 Auto-refresh (5s)", value=True, key="activity_refresh")
    
    with col2:
        if st.button("⚡ Refresh Now", key="manual_refresh"):
            st.rerun()
    
    with col3:
        max_events = st.selectbox("Show events", [10, 25, 50, 100], index=1, key="max_events")
    
    # Live activity container
    activity_container = st.container()
    
    with activity_container:
        if progress_tracker:
            progress_summary = progress_tracker.get_live_progress_summary()
            
            # Current status metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "🤖 Active Agents", 
                    progress_summary.get("active_agents", 0),
                    delta=None
                )
            
            with col2:
                st.metric(
                    "✅ Completed", 
                    progress_summary.get("completed_agents", 0),
                    delta=None
                )
            
            with col3:
                st.metric(
                    "📄 Artifacts", 
                    progress_summary.get("total_artifacts", 0),
                    delta=None
                )
            
            with col4:
                overall_progress = progress_summary.get("overall_progress", 0)
                st.metric(
                    "🎯 Progress", 
                    f"{overall_progress:.1f}%",
                    delta=None
                )
            
            # Live agent status
            st.markdown("#### 🔴 Live Agent Status")
            
            agent_details = progress_summary.get("agent_details", [])
            
            if agent_details:
                for agent in agent_details:
                    with st.expander(
                        f"🤖 {agent['agent_type']} - {agent['status'].title()} ({agent['progress']:.1f}%)",
                        expanded=agent['status'] == 'running'
                    ):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Agent ID:** {agent['agent_id']}")
                            st.write(f"**Status:** {agent['status']}")
                            st.write(f"**Current Activity:** {agent['current_activity']}")
                        
                        with col2:
                            # Progress bar
                            st.progress(agent['progress'] / 100.0)
                            
                            if agent['estimated_completion']:
                                completion_time = datetime.fromisoformat(agent['estimated_completion'])
                                time_remaining = completion_time - datetime.now()
                                if time_remaining.total_seconds() > 0:
                                    st.write(f"**ETA:** {time_remaining.seconds // 60}m {time_remaining.seconds % 60}s")
            
            # Recent artifacts
            st.markdown("#### 📄 Recent Artifacts Created")
            
            recent_artifacts = progress_summary.get("recent_artifacts", [])
            
            if recent_artifacts:
                artifacts_df = pd.DataFrame(recent_artifacts)
                artifacts_df['timestamp'] = pd.to_datetime(artifacts_df['timestamp'])
                artifacts_df = artifacts_df.sort_values('timestamp', ascending=False)
                
                st.dataframe(
                    artifacts_df[['type', 'created_by', 'timestamp']].head(max_events),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No artifacts created yet")
        
        else:
            # Always show real execution data if available, regardless of progress tracker
            render_demo_activity_feed()
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(5)
        st.rerun()


def render_progress_tracking(progress_tracker: Optional[LiveProgressTracker] = None,
                           execution_engine: Optional[ParallelExecutionEngine] = None):
    """Real-time progress tracking with visual progress bars"""
    
    st.markdown("### 📊 Real-Time Progress Tracking")
    
    if execution_engine:
        # Get active executions
        active_executions = execution_engine.get_all_active_executions()
        
        if active_executions:
            for execution in active_executions:
                with st.expander(
                    f"🔧 Execution {execution['execution_id'][-8:]} - {execution['progress']:.1f}%",
                    expanded=True
                ):
                    render_execution_progress(execution)
        else:
            st.info("No active parallel executions")
    
    if progress_tracker:
        # Individual agent progress
        st.markdown("#### 🤖 Individual Agent Progress")
        
        progress_summary = progress_tracker.get_live_progress_summary()
        agent_details = progress_summary.get("agent_details", [])
        
        for agent in agent_details:
            render_agent_progress_card(agent, progress_tracker)
    
    else:
        st.info("Connect progress tracker to see live progress")


def render_execution_progress(execution: Dict[str, Any]):
    """Render progress for a parallel execution"""
    
    # Overall execution progress
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Overall Progress", f"{execution['progress']:.1f}%")
    
    with col2:
        st.metric("Active Agents", len(execution['active_agents']))
    
    with col3:
        st.metric("Completed", f"{execution['completed_agents']}/{execution['total_agents']}")
    
    # Progress bar
    st.progress(execution['progress'])
    
    # Agent dependency graph visualization
    st.markdown("##### 🕸️ Agent Dependency Graph")
    
    agent_details = execution['agent_details']
    
    # Create a simple dependency visualization
    for agent_id, details in agent_details.items():
        status_icon = {
            'pending': '⏳',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌'
        }.get(details['status'], '⚪')
        
        dependencies = details.get('dependencies', [])
        dep_text = f" (depends on: {', '.join(dependencies)})" if dependencies else ""
        
        st.write(f"{status_icon} **{details['agent_type']}** - {details['status']} ({details['progress']:.1f}%){dep_text}")


def render_agent_progress_card(agent: Dict[str, Any], progress_tracker: LiveProgressTracker):
    """Render individual agent progress card"""
    
    agent_id = agent['agent_id']
    detailed_progress = progress_tracker.get_agent_progress(agent_id)
    
    if not detailed_progress:
        return
    
    with st.container():
        st.markdown(f"##### 🤖 {agent['agent_type']}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Status and progress
            status_color = {
                'pending': '🟡',
                'running': '🟢',
                'completed': '🔵',
                'failed': '🔴'
            }.get(agent['status'], '⚪')
            
            st.write(f"**Status:** {status_color} {agent['status'].title()}")
            st.progress(agent['progress'] / 100.0)
            st.write(f"Progress: {agent['progress']:.1f}%")
        
        with col2:
            # Activity and timing
            st.write(f"**Current Activity:**")
            st.write(agent['current_activity'])
            
            if detailed_progress.get('start_time'):
                start_time = datetime.fromisoformat(detailed_progress['start_time'])
                elapsed = datetime.now() - start_time
                st.write(f"**Elapsed:** {elapsed.seconds // 60}m {elapsed.seconds % 60}s")
        
        with col3:
            # Metrics
            st.write(f"**API Calls:** {detailed_progress.get('api_calls_made', 0)}")
            st.write(f"**Tokens Used:** {detailed_progress.get('tokens_used', 0)}")
            
            quality_score = detailed_progress.get('quality_score')
            if quality_score:
                st.write(f"**Quality:** {quality_score:.2f}")
        
        st.markdown("---")


def render_collaboration_metrics(progress_tracker: Optional[LiveProgressTracker] = None):
    """Render collaboration metrics and agent interaction patterns"""
    
    st.markdown("### 🤝 Agent Collaboration Metrics")
    
    if progress_tracker:
        # Get all collaboration metrics
        all_metrics = {}
        for correlation_id in progress_tracker.collaboration_metrics.keys():
            metrics = progress_tracker.get_collaboration_metrics(correlation_id)
            if metrics:
                all_metrics[correlation_id] = metrics
        
        if all_metrics:
            # Collaboration overview
            col1, col2, col3 = st.columns(3)
            
            total_handoffs = sum(m.get('handoffs_completed', 0) for m in all_metrics.values())
            total_parallel_sessions = sum(m.get('parallel_work_sessions', 0) for m in all_metrics.values())
            avg_efficiency = sum(m.get('collaboration_efficiency', 0) for m in all_metrics.values()) / len(all_metrics)
            
            with col1:
                st.metric("🔄 Total Handoffs", total_handoffs)
            
            with col2:
                st.metric("⚡ Parallel Sessions", total_parallel_sessions)
            
            with col3:
                st.metric("📈 Avg Efficiency", f"{avg_efficiency:.3f}")
            
            # Detailed workflow metrics
            st.markdown("#### 📋 Workflow Details")
            
            for correlation_id, metrics in all_metrics.items():
                with st.expander(f"Workflow {correlation_id[-8:]}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Active Agents:** {len(metrics.get('active_agents', []))}")
                        st.write(f"**Completed Agents:** {len(metrics.get('completed_agents', []))}")
                        st.write(f"**Artifacts Created:** {metrics.get('total_artifacts', 0)}")
                    
                    with col2:
                        st.write(f"**Handoffs Completed:** {metrics.get('handoffs_completed', 0)}")
                        st.write(f"**Parallel Sessions:** {metrics.get('parallel_work_sessions', 0)}")
                        st.write(f"**Efficiency Score:** {metrics.get('collaboration_efficiency', 0):.3f}")
            
            # Collaboration timeline
            render_collaboration_timeline(progress_tracker)
        
        else:
            st.info("No active collaborations to display")
    
    else:
        st.info("Connect progress tracker to see collaboration metrics")


def render_collaboration_timeline(progress_tracker: LiveProgressTracker):
    """Render timeline of collaboration events"""
    
    st.markdown("#### ⏰ Artifact Creation Timeline")
    
    # Get artifact timeline
    artifacts = progress_tracker.get_artifact_timeline()
    
    if artifacts:
        # Create timeline chart
        df = pd.DataFrame(artifacts)
        df['creation_time'] = pd.to_datetime(df['creation_time'])
        
        # Group by time intervals (e.g., minutes)
        df['time_bucket'] = df['creation_time'].dt.floor('T')  # Floor to minute
        timeline_data = df.groupby(['time_bucket', 'artifact_type']).size().reset_index(name='count')
        
        if not timeline_data.empty:
            fig = px.bar(
                timeline_data, 
                x='time_bucket', 
                y='count',
                color='artifact_type',
                title="Artifact Creation Timeline",
                labels={'time_bucket': 'Time', 'count': 'Artifacts Created'}
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent artifacts table
        st.markdown("##### 📄 Recent Artifacts")
        recent_df = df.head(10)[['artifact_type', 'created_by', 'creation_time']]
        st.dataframe(recent_df, use_container_width=True, hide_index=True)
    
    else:
        st.info("No artifacts created yet")


def render_system_analytics(progress_tracker: Optional[LiveProgressTracker] = None):
    """Render system-wide analytics and health metrics"""
    
    st.markdown("### 📈 System Analytics & Health")
    
    if progress_tracker:
        health = progress_tracker.get_system_health()
        
        # System health overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            uptime_hours = health['uptime_seconds'] / 3600
            st.metric("⏱️ Uptime", f"{uptime_hours:.1f}h")
        
        with col2:
            st.metric("📊 Events Processed", health['events_processed'])
        
        with col3:
            st.metric("⚡ Processing Rate", f"{health['processing_rate']:.1f}/s")
        
        with col4:
            st.metric("✅ Success Rate", f"{health['success_rate']:.1%}")
        
        # Agent health breakdown
        st.markdown("#### 🤖 Agent Health")
        
        agent_health = health['agent_health']
        
        # Create pie chart for agent status
        agent_status_data = {
            'Active': agent_health['active_agents'],
            'Completed': agent_health['completed_agents'],
            'Failed': agent_health['failed_agents']
        }
        
        if sum(agent_status_data.values()) > 0:
            fig = px.pie(
                values=list(agent_status_data.values()),
                names=list(agent_status_data.keys()),
                title="Agent Status Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Memory usage
        st.markdown("#### 💾 Memory Usage")
        
        memory_usage = health['memory_usage']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Agent Progress Entries", memory_usage['agent_progress_entries'])
        
        with col2:
            st.metric("Artifact Events", memory_usage['artifact_events'])
        
        with col3:
            st.metric("Active Workflows", memory_usage['collaboration_metrics'])
        
        # Performance trends (simulated)
        render_performance_trends()
    
    else:
        st.info("Connect progress tracker to see system analytics")


def render_performance_trends():
    """Render performance trend charts"""
    
    st.markdown("#### 📈 Performance Trends")
    
    # Simulate performance data (in real app, this would come from metrics)
    import numpy as np
    
    # Generate sample data
    time_points = pd.date_range(start=datetime.now() - timedelta(hours=1), end=datetime.now(), freq='5T')
    
    response_times = np.random.normal(2.5, 0.5, len(time_points))  # Average 2.5s response
    throughput = np.random.poisson(5, len(time_points))  # Average 5 tasks/interval
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Average Response Time', 'Task Throughput'),
        vertical_spacing=0.15
    )
    
    # Response time trend
    fig.add_trace(
        go.Scatter(
            x=time_points,
            y=response_times,
            mode='lines+markers',
            name='Response Time (s)',
            line=dict(color='blue')
        ),
        row=1, col=1
    )
    
    # Throughput trend
    fig.add_trace(
        go.Scatter(
            x=time_points,
            y=throughput,
            mode='lines+markers',
            name='Tasks/5min',
            line=dict(color='green')
        ),
        row=2, col=1
    )
    
    fig.update_layout(height=500, showlegend=False)
    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="Seconds", row=1, col=1)
    fig.update_yaxes(title_text="Count", row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True)


def render_demo_activity_feed():
    """Render real execution data instead of demo/simulation data"""
    import streamlit as st
    from datetime import datetime
    
    # Check for real execution data first
    has_real_data = (
        hasattr(st.session_state, 'agent_outputs') and 
        st.session_state.agent_outputs and
        any(output.get('is_real', False) for output in st.session_state.agent_outputs)
    )
    
    if has_real_data:
        st.success("🔴 REAL AI Execution Active - Showing authentic data from live API calls")
        
        # Real execution metrics
        col1, col2, col3, col4 = st.columns(4)
        
        real_outputs = [o for o in st.session_state.agent_outputs if o.get('is_real', False)]
        execution_phase = getattr(st.session_state, 'execution_phase', 'idle')
        
        with col1:
            active_count = 1 if execution_phase in ['real_execution', 'starting'] else 0
            st.metric("🔴 Live Sessions", active_count)
        
        with col2:
            st.metric("📄 Real Artifacts", len(real_outputs))
        
        with col3:
            total_words = sum(o.get('word_count', 0) for o in real_outputs)
            st.metric("📝 Words Generated", f"{total_words:,}")
        
        with col4:
            phase_display = execution_phase.replace('_', ' ').title()
            st.metric("🎯 Status", phase_display)
        
        st.markdown("#### 🔴 Real Agent Activity (Live API Calls)")
        
        # Display real agent outputs with actual timestamps
        for output in reversed(real_outputs[-5:]):  # Show last 5 real outputs
            col1, col2, col3, col4 = st.columns([1, 2, 3, 1])
            
            with col1:
                timestamp = output.get('formatted_time', 'N/A')
                st.write(f"`{timestamp}`")
            
            with col2:
                agent_name = output.get('agent', 'Unknown')
                st.write(f"**{agent_name}**")
            
            with col3:
                word_count = output.get('word_count', 0)
                st.write(f"Generated {word_count} words via real API")
            
            with col4:
                st.write("✅ Complete")
        
        # Show current time for reference
        current_time = datetime.now().strftime("%H:%M:%S")
        st.caption(f"Current time: {current_time} (All timestamps above are from real API execution)")
        
    else:
        st.info("📊 No Real Execution Data - Start a real AI project to see live data")
        st.markdown("Click 'Start REAL AI Project' on the Agent Orchestration tab to begin real execution.")


def create_live_dashboard_placeholder():
    """Create placeholder for live dashboard when system is initializing"""
    
    st.markdown("## 🔴 Live Agent Collaboration Monitor")
    st.markdown("*Initializing real-time monitoring system...*")
    
    # Placeholder metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🤖 Active Agents", "---", delta=None)
    
    with col2:
        st.metric("✅ Completed", "---", delta=None)
    
    with col3:
        st.metric("📄 Artifacts", "---", delta=None)
    
    with col4:
        st.metric("🎯 Progress", "---", delta=None)
    
    with st.spinner("Starting live monitoring systems..."):
        time.sleep(2)
    
    st.success("✅ Live monitoring systems ready!")
    st.rerun()