"""
Quality Monitoring Dashboard

This module provides a comprehensive Streamlit-based dashboard for monitoring
quality metrics, consensus validation results, and learning system performance.
"""

import logging
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from core.quality_cascade import QualityCascade, TaskComplexity, CascadeStage
from core.consensus_validator import ConsensusValidator, ValidationDomain, ConsensusMethod
from core.learning_engine import ContinuousLearner, LearningMode
from storage.performance_store import PerformanceStore, MetricType, AggregationPeriod

logger = logging.getLogger(__name__)


class QualityMonitoringDashboard:
    """
    Comprehensive quality monitoring dashboard with real-time metrics
    and performance analytics
    """
    
    def __init__(self):
        self.quality_cascade = QualityCascade()
        self.consensus_validator = ConsensusValidator()
        self.continuous_learner = ContinuousLearner()
        self.performance_store = PerformanceStore()
        
        # Initialize session state for dashboard data
        if 'dashboard_data' not in st.session_state:
            st.session_state.dashboard_data = {}
    
    def render_dashboard(self):
        """Render the complete quality monitoring dashboard"""
        
        st.title("🎯 Quality Assurance & Learning Dashboard")
        
        # Sidebar controls
        self._render_sidebar()
        
        # Main dashboard tabs
        tabs = st.tabs([
            "📊 Quality Overview", 
            "🔄 Cascade Pipeline", 
            "🤝 Consensus Validation",
            "🧠 Learning Analytics",
            "📈 Performance Trends",
            "⚙️ System Configuration"
        ])
        
        with tabs[0]:
            self._render_quality_overview()
        
        with tabs[1]:
            self._render_cascade_pipeline()
        
        with tabs[2]:
            self._render_consensus_validation()
        
        with tabs[3]:
            self._render_learning_analytics()
        
        with tabs[4]:
            self._render_performance_trends()
        
        with tabs[5]:
            self._render_system_configuration()
    
    def _render_sidebar(self):
        """Render dashboard sidebar with controls"""
        
        st.sidebar.header("Dashboard Controls")
        
        # Time range selection
        time_range = st.sidebar.selectbox(
            "Time Range",
            ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days"],
            index=2
        )
        
        # Model filter
        available_models = ["All", "gpt-4", "claude", "gemini"]
        selected_model = st.sidebar.selectbox("Model Filter", available_models)
        
        # Auto-refresh option
        auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
        
        if auto_refresh:
            st.rerun()
        
        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Data"):
            st.session_state.dashboard_data.clear()
            st.rerun()
        
        # Store selections in session state
        st.session_state.time_range = time_range
        st.session_state.selected_model = selected_model
    
    def _render_quality_overview(self):
        """Render quality overview section"""
        
        st.subheader("Quality Metrics Overview")
        
        # Get quality statistics
        quality_stats = self.performance_store.get_quality_statistics()
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Overall Quality Score",
                f"{quality_stats['overall']['avg_quality']:.3f}",
                delta=None
            )
        
        with col2:
            st.metric(
                "Total Evaluations",
                f"{quality_stats['overall']['total_metrics']:,}",
                delta=None
            )
        
        with col3:
            best_model = max(quality_stats['by_model'].items(), 
                           key=lambda x: x[1]['avg_quality'], default=("N/A", {"avg_quality": 0}))
            st.metric(
                "Best Performing Model",
                best_model[0],
                delta=f"{best_model[1]['avg_quality']:.3f}"
            )
        
        with col4:
            quality_range = (quality_stats['overall']['max_quality'] - 
                           quality_stats['overall']['min_quality'])
            st.metric(
                "Quality Score Range",
                f"{quality_range:.3f}",
                delta=None
            )
        
        # Model performance comparison
        if quality_stats['by_model']:
            st.subheader("Model Performance Comparison")
            
            models = list(quality_stats['by_model'].keys())
            avg_qualities = [quality_stats['by_model'][model]['avg_quality'] for model in models]
            metric_counts = [quality_stats['by_model'][model]['metric_count'] for model in models]
            
            # Create comparison chart
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=("Average Quality Score", "Number of Evaluations"),
                specs=[[{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # Quality scores
            fig.add_trace(
                go.Bar(
                    x=models,
                    y=avg_qualities,
                    name="Avg Quality",
                    marker_color="lightblue"
                ),
                row=1, col=1
            )
            
            # Metric counts
            fig.add_trace(
                go.Bar(
                    x=models,
                    y=metric_counts,
                    name="Evaluations",
                    marker_color="lightgreen"
                ),
                row=1, col=2
            )
            
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent quality trends
        st.subheader("Recent Quality Trends")
        
        # Get recent metrics for trend analysis
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        recent_metrics = self.performance_store.get_metrics(
            metric_type=MetricType.QUALITY_SCORE,
            start_time=start_time,
            end_time=end_time,
            limit=500
        )
        
        if recent_metrics:
            # Create DataFrame for plotting
            df_metrics = pd.DataFrame([
                {
                    "timestamp": metric.timestamp,
                    "model_name": metric.model_name,
                    "quality_score": metric.value,
                    "task_type": metric.task_type
                }
                for metric in recent_metrics
            ])
            
            # Time series plot
            fig = px.line(
                df_metrics.groupby(['timestamp', 'model_name'])['quality_score'].mean().reset_index(),
                x='timestamp',
                y='quality_score',
                color='model_name',
                title="Quality Score Trends Over Time"
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recent quality metrics available for trending.")
    
    def _render_cascade_pipeline(self):
        """Render cascade pipeline monitoring"""
        
        st.subheader("Quality Cascade Pipeline")
        
        # Get current cascade status
        active_cascades = self.quality_cascade.get_all_active_cascades()
        quality_stats = self.quality_cascade.get_quality_statistics()
        
        # Pipeline summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Active Cascades", quality_stats["active_cascades"])
        
        with col2:
            st.metric(
                "Average Quality Score",
                f"{quality_stats['average_quality_score']:.3f}"
            )
        
        with col3:
            if quality_stats["quality_score_range"]:
                range_str = f"{quality_stats['quality_score_range']['min']:.2f} - {quality_stats['quality_score_range']['max']:.2f}"
            else:
                range_str = "N/A"
            st.metric("Quality Range", range_str)
        
        # Stage distribution
        if quality_stats["stages_distribution"]:
            st.subheader("Current Pipeline Stages")
            
            stages = list(quality_stats["stages_distribution"].keys())
            counts = list(quality_stats["stages_distribution"].values())
            
            fig = px.pie(
                values=counts,
                names=stages,
                title="Distribution of Artifacts by Cascade Stage"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Complexity distribution
        if quality_stats["complexity_distribution"]:
            st.subheader("Task Complexity Distribution")
            
            complexity_levels = list(quality_stats["complexity_distribution"].keys())
            complexity_counts = list(quality_stats["complexity_distribution"].values())
            
            fig = px.bar(
                x=complexity_levels,
                y=complexity_counts,
                title="Tasks by Complexity Level",
                color=complexity_counts,
                color_continuous_scale="viridis"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Active cascades table
        if active_cascades:
            st.subheader("Active Cascade Processes")
            
            cascade_df = pd.DataFrame([
                {
                    "Artifact ID": cascade["artifact_id"],
                    "Current Stage": cascade["current_stage"],
                    "Complexity": cascade["complexity"],
                    "Quality Score": f"{cascade['quality_score']:.3f}",
                    "Reviews": cascade["reviews_count"],
                    "Human Review": "Yes" if cascade["requires_human_review"] else "No",
                    "Created": cascade["created_at"][:19].replace("T", " ")
                }
                for cascade in active_cascades
            ])
            
            st.dataframe(cascade_df, use_container_width=True)
        else:
            st.info("No active cascade processes currently running.")
        
        # Cascade configuration
        with st.expander("Cascade Configuration"):
            st.subheader("Confidence Thresholds by Complexity")
            
            # Display threshold matrix
            thresholds_data = []
            for complexity in TaskComplexity:
                for stage in CascadeStage:
                    if stage in [CascadeStage.INITIAL_AGENT, CascadeStage.PEER_REVIEW, 
                               CascadeStage.QUALITY_CHECK, CascadeStage.FINAL_APPROVAL]:
                        threshold = self.quality_cascade.confidence_thresholds.get(complexity, {}).get(stage, 0.0)
                        thresholds_data.append({
                            "Complexity": complexity.value,
                            "Stage": stage.value,
                            "Threshold": threshold
                        })
            
            if thresholds_data:
                threshold_df = pd.DataFrame(thresholds_data)
                pivot_df = threshold_df.pivot(index="Stage", columns="Complexity", values="Threshold")
                st.dataframe(pivot_df, use_container_width=True)
    
    def _render_consensus_validation(self):
        """Render consensus validation monitoring"""
        
        st.subheader("Multi-Model Consensus Validation")
        
        # Get consensus statistics
        consensus_stats = self.consensus_validator.get_consensus_statistics()
        
        if consensus_stats["total_validations"] > 0:
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Validations", consensus_stats["total_validations"])
            
            with col2:
                pass_rate = consensus_stats["overall_pass_rate"]
                st.metric("Overall Pass Rate", f"{pass_rate:.1%}")
            
            with col3:
                st.metric(
                    "Avg Consensus Score", 
                    f"{consensus_stats['avg_consensus_score']:.3f}"
                )
            
            with col4:
                st.metric(
                    "Avg Processing Time",
                    f"{consensus_stats['avg_processing_time']:.2f}s"
                )
            
            # Domain performance
            st.subheader("Performance by Domain")
            
            if consensus_stats["domain_pass_rates"]:
                domain_data = []
                for domain, stats in consensus_stats["domain_pass_rates"].items():
                    domain_data.append({
                        "Domain": domain.replace("_", " ").title(),
                        "Total Validations": stats["total"],
                        "Passed": stats["passed"],
                        "Pass Rate": stats["pass_rate"]
                    })
                
                domain_df = pd.DataFrame(domain_data)
                
                # Pass rate by domain chart
                fig = px.bar(
                    domain_df,
                    x="Domain",
                    y="Pass Rate",
                    title="Validation Pass Rate by Domain",
                    color="Pass Rate",
                    color_continuous_scale="RdYlGn"
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Domain details table
                st.dataframe(domain_df, use_container_width=True)
            
            # Model expertise weights
            st.subheader("Domain Expertise Weights")
            
            selected_domain = st.selectbox(
                "Select Domain",
                list(ValidationDomain),
                format_func=lambda x: x.value.replace("_", " ").title()
            )
            
            if selected_domain:
                weights = self.consensus_validator.get_domain_expertise_weights(selected_domain)
                
                if weights:
                    models = list(weights.keys())
                    weight_values = list(weights.values())
                    
                    fig = px.pie(
                        values=weight_values,
                        names=models,
                        title=f"Model Expertise Weights for {selected_domain.value.replace('_', ' ').title()}"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No consensus validation data available yet.")
        
        # Validation history
        with st.expander("Recent Validation History"):
            recent_validations = self.consensus_validator.get_validation_history(limit=10)
            
            if recent_validations:
                validation_data = []
                for validation in recent_validations:
                    validation_data.append({
                        "Artifact ID": validation.artifact_id,
                        "Domain": validation.domain.value.replace("_", " ").title(),
                        "Consensus Score": f"{validation.consensus_score:.3f}",
                        "Quality Score": f"{validation.final_quality_score:.3f}",
                        "Passed": "✅" if validation.validation_passed else "❌",
                        "Method": validation.consensus_method.value.replace("_", " ").title(),
                        "Models": len(validation.model_validations),
                        "Timestamp": validation.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    })
                
                validation_df = pd.DataFrame(validation_data)
                st.dataframe(validation_df, use_container_width=True)
            else:
                st.info("No recent validation history available.")
    
    def _render_learning_analytics(self):
        """Render learning system analytics"""
        
        st.subheader("Continuous Learning Analytics")
        
        # Get learning statistics
        learning_stats = self.continuous_learner.get_learning_statistics()
        
        # Key learning metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Decisions", learning_stats["total_decisions"])
        
        with col2:
            st.metric("Successful Adaptations", learning_stats["successful_adaptations"])
        
        with col3:
            adaptation_rate = (learning_stats["successful_adaptations"] / 
                             max(learning_stats["total_decisions"], 1) * 100)
            st.metric("Adaptation Rate", f"{adaptation_rate:.1f}%")
        
        with col4:
            st.metric("Learning Mode", learning_stats["learning_mode"].replace("_", " ").title())
        
        # Current routing weights
        st.subheader("Current Routing Weights")
        
        weights = learning_stats["current_routing_weights"]
        
        if weights:
            models = list(weights.keys())
            weight_values = list(weights.values())
            
            fig = go.Figure(data=[
                go.Bar(x=models, y=weight_values, marker_color='lightcoral')
            ])
            
            fig.update_layout(
                title="Current Model Routing Weights",
                yaxis_title="Weight",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Model performance summary
        if learning_stats["model_performance_summary"]:
            st.subheader("Model Performance Summary")
            
            perf_data = []
            for model, metrics in learning_stats["model_performance_summary"].items():
                perf_data.append({
                    "Model": model,
                    "Task Types": metrics["total_task_types"],
                    "Avg Quality": f"{metrics['avg_quality_across_tasks']:.3f}",
                    "Avg Success Rate": f"{metrics['avg_success_rate']:.1%}",
                })
            
            perf_df = pd.DataFrame(perf_data)
            st.dataframe(perf_df, use_container_width=True)
        
        # Learning analytics from performance store
        learning_analytics = self.performance_store.get_learning_analytics(days_back=30)
        
        if learning_analytics["outcome_statistics"]:
            st.subheader("Learning Outcomes (Last 30 Days)")
            
            outcome_data = []
            for outcome_type, stats in learning_analytics["outcome_statistics"].items():
                outcome_data.append({
                    "Outcome Type": outcome_type.replace("_", " ").title(),
                    "Count": stats["count"],
                    "Avg Prediction Error": f"{stats['avg_prediction_error']:.4f}",
                    "Avg Absolute Error": f"{stats['avg_abs_prediction_error']:.4f}",
                    "Adaptations Applied": stats["adaptations_applied"]
                })
            
            outcome_df = pd.DataFrame(outcome_data)
            st.dataframe(outcome_df, use_container_width=True)
        
        # Prediction accuracy trends
        if learning_analytics["accuracy_trends"]:
            st.subheader("Prediction Accuracy Trends")
            
            trends_df = pd.DataFrame(learning_analytics["accuracy_trends"])
            
            fig = px.line(
                trends_df,
                x="date",
                y="avg_absolute_error",
                title="Daily Average Prediction Error",
                markers=True
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # Meta-learning status
        with st.expander("Meta-Learning Status"):
            st.write(f"**Meta-learner Trained:** {'Yes' if learning_stats['meta_learner_trained'] else 'No'}")
            if learning_stats["last_meta_training"]:
                st.write(f"**Last Meta-Training:** {learning_stats['last_meta_training']}")
            else:
                st.write("**Last Meta-Training:** Never")
    
    def _render_performance_trends(self):
        """Render performance trends section"""
        
        st.subheader("Performance Trends")
        
        # Get performance trends
        trends = self.performance_store.get_model_performance_trends(days_back=30)
        
        if trends:
            # Model selection for detailed view
            selected_model = st.selectbox(
                "Select Model for Detailed Analysis",
                ["All Models"] + list(trends.keys())
            )
            
            if selected_model == "All Models":
                # Combined trends
                all_data = []
                for model, model_trends in trends.items():
                    for trend in model_trends:
                        if trend["metric_type"] == "quality_score":
                            all_data.append({
                                "timestamp": trend["timestamp"],
                                "model": model,
                                "quality_score": trend["value"],
                                "task_type": trend["task_type"]
                            })
                
                if all_data:
                    trends_df = pd.DataFrame(all_data)
                    trends_df["timestamp"] = pd.to_datetime(trends_df["timestamp"])
                    
                    # Aggregate by day and model
                    daily_trends = (trends_df.groupby([trends_df["timestamp"].dt.date, "model"])
                                   ["quality_score"].mean().reset_index())
                    daily_trends["timestamp"] = pd.to_datetime(daily_trends["timestamp"])
                    
                    fig = px.line(
                        daily_trends,
                        x="timestamp",
                        y="quality_score",
                        color="model",
                        title="Quality Score Trends by Model"
                    )
                    
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                # Individual model trends
                model_data = trends[selected_model]
                
                # Filter for quality scores
                quality_data = [trend for trend in model_data if trend["metric_type"] == "quality_score"]
                
                if quality_data:
                    model_df = pd.DataFrame(quality_data)
                    model_df["timestamp"] = pd.to_datetime(model_df["timestamp"])
                    
                    # Group by task type
                    fig = px.line(
                        model_df,
                        x="timestamp",
                        y="value",
                        color="task_type",
                        title=f"Quality Trends for {selected_model}"
                    )
                    
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Task type performance summary
                    task_summary = (model_df.groupby("task_type")["value"]
                                   .agg(["count", "mean", "std"]).reset_index())
                    task_summary.columns = ["Task Type", "Count", "Avg Quality", "Std Dev"]
                    
                    st.subheader(f"Task Type Summary for {selected_model}")
                    st.dataframe(task_summary, use_container_width=True)
        else:
            st.info("No performance trend data available.")
        
        # Aggregated metrics
        st.subheader("Aggregated Performance Metrics")
        
        # Compute recent aggregated metrics
        aggregated = self.performance_store.compute_aggregated_metrics(
            period=AggregationPeriod.DAILY,
            start_time=datetime.now() - timedelta(days=7),
            end_time=datetime.now()
        )
        
        if aggregated:
            agg_data = []
            for agg in aggregated:
                agg_data.append({
                    "Model": agg.model_name,
                    "Task Type": agg.task_type,
                    "Metric Type": agg.metric_type.value.replace("_", " ").title(),
                    "Mean": f"{agg.mean_value:.3f}",
                    "Std Dev": f"{agg.std_deviation:.3f}",
                    "Min": f"{agg.min_value:.3f}",
                    "Max": f"{agg.max_value:.3f}",
                    "Samples": agg.sample_count
                })
            
            agg_df = pd.DataFrame(agg_data)
            st.dataframe(agg_df, use_container_width=True)
        else:
            st.info("Computing aggregated metrics...")
    
    def _render_system_configuration(self):
        """Render system configuration section"""
        
        st.subheader("System Configuration & Controls")
        
        # Quality cascade configuration
        with st.expander("Quality Cascade Settings"):
            st.write("**Confidence Thresholds**")
            
            # Allow editing of thresholds (in a real system)
            complexity_level = st.selectbox(
                "Complexity Level",
                list(TaskComplexity),
                format_func=lambda x: x.value.title()
            )
            
            if complexity_level:
                thresholds = self.quality_cascade.confidence_thresholds.get(complexity_level, {})
                
                st.write(f"Current thresholds for {complexity_level.value}:")
                for stage, threshold in thresholds.items():
                    st.write(f"- {stage.value}: {threshold}")
        
        # Consensus validator configuration
        with st.expander("Consensus Validator Settings"):
            st.write("**Domain Expertise Weights**")
            
            domain = st.selectbox(
                "Domain",
                list(ValidationDomain),
                format_func=lambda x: x.value.replace("_", " ").title()
            )
            
            if domain:
                weights = self.consensus_validator.get_domain_expertise_weights(domain)
                
                st.write(f"Current weights for {domain.value}:")
                for model, weight in weights.items():
                    st.write(f"- {model}: {weight}")
        
        # Learning engine configuration
        with st.expander("Learning Engine Settings"):
            learning_stats = self.continuous_learner.get_learning_statistics()
            
            st.write(f"**Learning Mode:** {learning_stats['learning_mode']}")
            st.write(f"**Meta-learner Status:** {'Trained' if learning_stats['meta_learner_trained'] else 'Not Trained'}")
            
            if st.button("Reset Learning System"):
                self.continuous_learner.reset_learning()
                st.success("Learning system has been reset.")
        
        # Data management
        with st.expander("Data Management"):
            st.subheader("Database Cleanup")
            
            days_to_keep = st.number_input(
                "Days of data to keep",
                min_value=1,
                max_value=365,
                value=90
            )
            
            if st.button("Clean Old Data"):
                deleted_count = self.performance_store.cleanup_old_metrics(days_to_keep)
                st.success(f"Cleaned up {deleted_count} old records.")
            
            st.subheader("Data Export")
            
            if st.button("Export Metrics Data"):
                export_file = f"metrics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                if self.performance_store.export_metrics(export_file):
                    st.success(f"Metrics exported to {export_file}")
                else:
                    st.error("Failed to export metrics")


def quality_monitoring_dashboard():
    """Main function to render the quality monitoring dashboard"""
    
    # Initialize dashboard
    dashboard = QualityMonitoringDashboard()
    
    # Render the complete dashboard
    dashboard.render_dashboard()


# Run the dashboard if called directly
if __name__ == "__main__":
    quality_monitoring_dashboard()