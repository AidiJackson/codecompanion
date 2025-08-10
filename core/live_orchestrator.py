"""
Live Multi-Agent Orchestrator with Real AI Integration

Coordinates real Claude, GPT-4, and Gemini agents through event-sourced
orchestration with intelligent task routing and quality cascading.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4
import json

from core.event_streaming import (
    RealTimeEventOrchestrator, EventBus, StreamEvent, EventType, EventStreamType
)
from core.intelligent_router import IntelligentTaskRouter
from agents.live_agent_workers import LiveAgentOrchestrator
from schemas.artifacts import ArtifactType
from schemas.ledgers import TaskLedger, TaskStatus, Priority

logger = logging.getLogger(__name__)


class LiveOrchestrator:
    """
    Production orchestrator that coordinates real AI agents through
    event-sourced workflows with intelligent routing and quality cascading.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.event_bus = EventBus(redis_url)
        self.router = IntelligentTaskRouter(self.event_bus)
        self.agent_orchestrator = LiveAgentOrchestrator(self.event_bus)
        
        # Active workflows
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        
        # Quality cascading configuration
        self.quality_cascade = {
            'architecture': ['claude', 'gpt4', 'gemini'],  # Architecture: Claude -> GPT-4 -> Gemini review
            'implementation': ['gpt4', 'claude', 'gemini'],  # Code: GPT-4 -> Claude review -> Gemini test
            'testing': ['gemini', 'gpt4', 'claude'],  # Tests: Gemini -> GPT-4 review -> Claude analysis
            'documentation': ['claude', 'gemini', 'gpt4']  # Docs: Claude -> Gemini review -> GPT-4 polish
        }
        
        logger.info("Live orchestrator initialized with real AI agent integration")
    
    async def start_live_project(self, project_description: str, project_type: str = "web_application") -> str:
        """
        Start a live project with real AI agents
        
        This creates a complete workflow where real AI agents collaborate
        on an actual development project.
        """
        
        correlation_id = f"live_project_{uuid4().hex[:8]}"
        
        # Initialize AI clients for real execution
        from core.ai_clients import RealAIClients, AIClientConfig
        self.ai_clients = RealAIClients(AIClientConfig())
        
        # Create project workflow
        workflow = {
            'correlation_id': correlation_id,
            'description': project_description,
            'project_type': project_type,
            'start_time': datetime.now(timezone.utc),
            'status': 'active',
            'phases': self._generate_project_phases(project_description, project_type),
            'current_phase': 0,
            'artifacts': [],
            'agent_assignments': {},
            'quality_reviews': [],
            'real_agent_results': []
        }
        
        self.active_workflows[correlation_id] = workflow
        
        # Start real agent execution
        try:
            await self._execute_real_agent_workflow(correlation_id, project_description, project_type)
        except Exception as e:
            logger.error(f"Failed to start real agent workflow: {e}")
            workflow['status'] = 'error'
            workflow['error'] = str(e)
        
        # Start agent workers
        await self.agent_orchestrator.start_workers()
        
        # Publish project started event
        project_event = StreamEvent(
            correlation_id=correlation_id,
            event_type=EventType.WORKFLOW_STARTED,
            agent_id="live_orchestrator",
            task_id=f"{correlation_id}_workflow",
            artifact_id=f"{correlation_id}_workflow_spec",
            payload={
                'project_description': project_description,
                'project_type': project_type,
                'phases': workflow['phases'],
                'live_agents': True
            },
            metadata={'orchestrator': 'live_v1', 'real_ai': True}
        )
        
        await self.event_bus.publish_event(EventStreamType.TASKS, project_event)
        
        # Start first phase
        await self._execute_next_phase(correlation_id)
        
        logger.info(f"Started live project {correlation_id}: {project_description}")
        return correlation_id
    
    def _generate_project_phases(self, description: str, project_type: str) -> List[Dict[str, Any]]:
        """Generate project phases based on description and type"""
        
        base_phases = [
            {
                'phase_id': 'requirements',
                'name': 'Requirements Analysis',
                'description': 'Analyze requirements and create specifications',
                'primary_agent': 'claude',
                'task_type': 'specification',
                'expected_artifact': ArtifactType.SPEC_DOC.value,
                'quality_cascade': True
            },
            {
                'phase_id': 'architecture',
                'name': 'System Architecture',
                'description': 'Design system architecture and components',
                'primary_agent': 'claude',
                'task_type': 'architecture',
                'expected_artifact': ArtifactType.DESIGN_DOC.value,
                'quality_cascade': True
            },
            {
                'phase_id': 'implementation',
                'name': 'Core Implementation',
                'description': 'Implement core functionality and features',
                'primary_agent': 'gpt4',
                'task_type': 'implementation',
                'expected_artifact': ArtifactType.CODE_PATCH.value,
                'quality_cascade': True
            },
            {
                'phase_id': 'testing',
                'name': 'Testing & Quality Assurance',
                'description': 'Create comprehensive tests and quality validation',
                'primary_agent': 'gemini',
                'task_type': 'testing',
                'expected_artifact': ArtifactType.TEST_PLAN.value,
                'quality_cascade': True
            }
        ]
        
        # Customize phases based on project type
        if project_type == 'api':
            base_phases.append({
                'phase_id': 'documentation',
                'name': 'API Documentation',
                'description': 'Create comprehensive API documentation',
                'primary_agent': 'claude',
                'task_type': 'documentation',
                'expected_artifact': ArtifactType.RUNBOOK.value,
                'quality_cascade': False
            })
        
        elif project_type == 'ui_application':
            base_phases.insert(2, {
                'phase_id': 'ui_design',
                'name': 'UI Design & Implementation',
                'description': 'Design and implement user interface',
                'primary_agent': 'gpt4',
                'task_type': 'ui_development',
                'expected_artifact': ArtifactType.CODE_PATCH.value,
                'quality_cascade': True
            })
        
        return base_phases
    
    async def _execute_real_agent_workflow(self, correlation_id: str, project_description: str, project_type: str):
        """Execute real AI agent workflow with API calls"""
        from agents.base_agent import AgentInput, AgentType
        
        workflow = self.active_workflows[correlation_id]
        
        try:
            # Phase 1: Project Manager (Claude) - Requirements Analysis
            logger.info(f"Starting Project Manager phase for {correlation_id}")
            pm_input = AgentInput(
                task_id=f"{correlation_id}_requirements",
                correlation_id=correlation_id,
                objective="Analyze project requirements and create detailed specifications",
                context=f"Project: {project_description}\nType: {project_type}",
                requested_artifact=ArtifactType.SPEC_DOC,
                max_processing_time=600,  # 10 minutes in seconds
                submitted_by="live_orchestrator"
            )
            
            pm_result = await self.ai_clients.execute_agent(pm_input, AgentType.PROJECT_MANAGER)
            workflow['real_agent_results'].append({
                'agent': 'Project Manager (Claude)',
                'phase': 'Requirements Analysis',
                'result': pm_result.artifact,
                'status': pm_result.quality_score > 0.5,
                'timestamp': datetime.now().isoformat()
            })
            
            # Phase 2: Code Generator (GPT-4) - Implementation
            logger.info(f"Starting Code Generator phase for {correlation_id}")
            code_input = AgentInput(
                task_id=f"{correlation_id}_implementation",
                correlation_id=correlation_id,
                objective="Implement core functionality based on requirements",
                context=f"Project: {project_description}\nRequirements: {pm_result.artifact}",
                dependency_artifacts=[json.dumps(pm_result.artifact)],
                requested_artifact=ArtifactType.CODE_PATCH,
                max_processing_time=900,  # 15 minutes in seconds
                submitted_by="live_orchestrator"
            )
            
            code_result = await self.ai_clients.execute_agent(code_input, AgentType.CODE_GENERATOR)
            workflow['real_agent_results'].append({
                'agent': 'Code Generator (GPT-4)',
                'phase': 'Implementation',
                'result': code_result.artifact,
                'status': code_result.quality_score > 0.5,
                'timestamp': datetime.now().isoformat()
            })
            
            # Phase 3: UI Designer (Gemini) - Interface Design  
            logger.info(f"Starting UI Designer phase for {correlation_id}")
            ui_input = AgentInput(
                task_id=f"{correlation_id}_ui_design",
                correlation_id=correlation_id,
                objective="Design user interface and user experience",
                context=f"Project: {project_description}\nImplementation: {code_result.artifact}",
                dependency_artifacts=[json.dumps(code_result.artifact)],
                requested_artifact=ArtifactType.DESIGN_DOC,
                max_processing_time=600,  # 10 minutes in seconds
                submitted_by="live_orchestrator"
            )
            
            ui_result = await self.ai_clients.execute_agent(ui_input, AgentType.UI_DESIGNER)
            workflow['real_agent_results'].append({
                'agent': 'UI Designer (Gemini)',
                'phase': 'UI Design',
                'result': ui_result.artifact,
                'status': ui_result.quality_score > 0.5,
                'timestamp': datetime.now().isoformat()
            })
            
            # Phase 4: Test Writer (GPT-4) - Testing
            logger.info(f"Starting Test Writer phase for {correlation_id}")
            test_input = AgentInput(
                task_id=f"{correlation_id}_testing",
                correlation_id=correlation_id,
                objective="Create comprehensive testing strategy and test cases",
                context=f"Project: {project_description}",
                dependency_artifacts=[json.dumps(code_result.artifact), json.dumps(ui_result.artifact)],
                requested_artifact=ArtifactType.TEST_PLAN,
                max_processing_time=720,  # 12 minutes in seconds
                submitted_by="live_orchestrator"
            )
            
            test_result = await self.ai_clients.execute_agent(test_input, AgentType.TEST_WRITER)
            workflow['real_agent_results'].append({
                'agent': 'Test Writer (GPT-4)', 
                'phase': 'Testing Strategy',
                'result': test_result.artifact,
                'status': test_result.quality_score > 0.5,
                'timestamp': datetime.now().isoformat()
            })
            
            # Phase 5: Debugger (Claude) - Code Review and Optimization
            logger.info(f"Starting Debugger phase for {correlation_id}")
            debug_input = AgentInput(
                task_id=f"{correlation_id}_debugging",
                correlation_id=correlation_id,
                objective="Review code quality, identify issues, and optimize performance",
                context=f"Project: {project_description}",
                dependency_artifacts=[json.dumps(code_result.artifact), json.dumps(test_result.artifact)],
                requested_artifact=ArtifactType.SPEC_DOC,
                max_processing_time=600,  # 10 minutes in seconds
                submitted_by="live_orchestrator"
            )
            
            debug_result = await self.ai_clients.execute_agent(debug_input, AgentType.DEBUGGER)
            workflow['real_agent_results'].append({
                'agent': 'Debugger (Claude)',
                'phase': 'Code Review & Optimization',
                'result': debug_result.artifact,
                'status': debug_result.quality_score > 0.5,
                'timestamp': datetime.now().isoformat()
            })
            
            # Update workflow status
            workflow['status'] = 'completed'
            workflow['completion_time'] = datetime.now(timezone.utc)
            workflow['artifacts_created'] = len(workflow['real_agent_results'])
            
            logger.info(f"Completed real agent workflow for {correlation_id}")
            
        except Exception as e:
            logger.error(f"Real agent workflow failed for {correlation_id}: {e}")
            workflow['status'] = 'failed'
            workflow['error'] = str(e)
            raise
    
    async def _execute_next_phase(self, correlation_id: str):
        """Execute the next phase in the workflow"""
        
        workflow = self.active_workflows.get(correlation_id)
        if not workflow or workflow['status'] != 'active':
            return
        
        phases = workflow['phases']
        current_phase_idx = workflow['current_phase']
        
        if current_phase_idx >= len(phases):
            # Project complete
            await self._complete_project(correlation_id)
            return
        
        phase = phases[current_phase_idx]
        
        logger.info(f"Executing phase {phase['name']} for project {correlation_id}")
        
        # Create task for this phase
        task_data = {
            'task_id': f"{correlation_id}_phase_{phase['phase_id']}",
            'correlation_id': correlation_id,
            'objective': phase['name'],
            'description': f"{phase['description']} for project: {workflow['description']}",
            'primary_task_type': phase['task_type'],
            'expected_artifact': phase['expected_artifact'],
            'context': workflow['description'],
            'priority': 'high',
            'phase_info': phase
        }
        
        # Route task to optimal agent
        available_agents = list(self.agent_orchestrator.workers.keys())
        
        if available_agents:
            selected_agent = await self.agent_orchestrator.assign_task_to_best_agent(
                task_data, correlation_id
            )
            
            if selected_agent:
                workflow['agent_assignments'][phase['phase_id']] = selected_agent
                
                # Create task event
                task_event = StreamEvent(
                    correlation_id=correlation_id,
                    event_type=EventType.TASK_CREATED,
                    agent_id=selected_agent,
                    task_id=task_data['task_id'],
                    artifact_id=f"{task_data['task_id']}_artifact",
                    payload=task_data,
                    metadata={'phase': phase['phase_id'], 'live_execution': True}
                )
                
                await self.event_bus.publish_event(EventStreamType.TASKS, task_event)
        
        # Start monitoring this phase
        asyncio.create_task(self._monitor_phase_completion(correlation_id, phase['phase_id']))
    
    async def _monitor_phase_completion(self, correlation_id: str, phase_id: str):
        """Monitor phase completion and trigger next phase or quality cascade"""
        
        # This would typically be handled by event consumers, but for demo
        # we'll use a simple polling approach
        
        while True:
            await asyncio.sleep(5)  # Check every 5 seconds
            
            workflow = self.active_workflows.get(correlation_id)
            if not workflow or workflow['status'] != 'active':
                break
            
            # Check if phase artifacts have been created
            phase_artifacts = [
                artifact for artifact in workflow['artifacts']
                if artifact.get('phase_id') == phase_id
            ]
            
            if phase_artifacts:
                phase = next(p for p in workflow['phases'] if p['phase_id'] == phase_id)
                
                if phase.get('quality_cascade', False):
                    await self._initiate_quality_cascade(correlation_id, phase_id, phase_artifacts[0])
                else:
                    await self._advance_to_next_phase(correlation_id)
                break
    
    async def _initiate_quality_cascade(self, correlation_id: str, phase_id: str, artifact: Dict[str, Any]):
        """Initiate quality cascade for artifact review"""
        
        cascade_type = self._determine_cascade_type(phase_id)
        cascade_agents = self.quality_cascade.get(cascade_type, ['claude', 'gpt4', 'gemini'])
        
        logger.info(f"Initiating quality cascade for {phase_id}: {' -> '.join(cascade_agents)}")
        
        # Start quality review process
        for i, agent_id in enumerate(cascade_agents[1:], 1):  # Skip first agent (creator)
            review_task = {
                'task_id': f"{correlation_id}_review_{phase_id}_{i}",
                'correlation_id': correlation_id,
                'objective': f"Quality review of {artifact['artifact_id']}",
                'description': f"Review and validate {artifact['artifact_type']} for quality and completeness",
                'primary_task_type': 'review',
                'expected_artifact': ArtifactType.EVAL_REPORT.value,
                'context': f"Reviewing artifact created by {artifact['created_by']}",
                'review_target': artifact['artifact_id'],
                'cascade_step': i
            }
            
            # Assign to specific agent
            assignment_event = StreamEvent(
                correlation_id=correlation_id,
                event_type=EventType.TASK_ASSIGNED,
                agent_id=agent_id,
                task_id=review_task['task_id'],
                artifact_id=f"{review_task['task_id']}_artifact",
                payload=review_task,
                metadata={'quality_cascade': True, 'cascade_step': i}
            )
            
            await self.event_bus.publish_event(EventStreamType.TASKS, assignment_event)
            
            # Wait for review completion before next step (simplified for demo)
            await asyncio.sleep(10)
    
    def _determine_cascade_type(self, phase_id: str) -> str:
        """Determine quality cascade type based on phase"""
        
        if 'architecture' in phase_id or 'design' in phase_id:
            return 'architecture'
        elif 'implementation' in phase_id or 'code' in phase_id:
            return 'implementation'
        elif 'test' in phase_id or 'qa' in phase_id:
            return 'testing'
        elif 'doc' in phase_id or 'spec' in phase_id:
            return 'documentation'
        else:
            return 'architecture'  # Default
    
    async def _advance_to_next_phase(self, correlation_id: str):
        """Advance workflow to next phase"""
        
        workflow = self.active_workflows[correlation_id]
        workflow['current_phase'] += 1
        
        # Execute next phase
        await self._execute_next_phase(correlation_id)
    
    async def _complete_project(self, correlation_id: str):
        """Complete the project workflow"""
        
        workflow = self.active_workflows[correlation_id]
        workflow['status'] = 'completed'
        workflow['completion_time'] = datetime.now(timezone.utc)
        
        # Publish project completion event
        completion_event = StreamEvent(
            correlation_id=correlation_id,
            event_type=EventType.WORKFLOW_COMPLETED,
            agent_id="live_orchestrator",
            task_id=f"{correlation_id}_workflow",
            artifact_id=f"{correlation_id}_final_deliverables",
            payload={
                'status': 'completed',
                'total_phases': len(workflow['phases']),
                'total_artifacts': len(workflow['artifacts']),
                'agent_assignments': workflow['agent_assignments'],
                'duration_minutes': (workflow['completion_time'] - workflow['start_time']).total_seconds() / 60
            },
            metadata={'live_project': True, 'real_ai_collaboration': True}
        )
        
        await self.event_bus.publish_event(EventStreamType.TASKS, completion_event)
        
        logger.info(f"Completed live project {correlation_id} with {len(workflow['artifacts'])} artifacts")
    
    async def handle_artifact_created(self, event: StreamEvent):
        """Handle artifact creation events"""
        
        correlation_id = event.correlation_id
        workflow = self.active_workflows.get(correlation_id)
        
        if workflow:
            # Add artifact to workflow
            artifact_data = event.payload.copy()
            artifact_data['phase_id'] = event.metadata.get('phase')
            workflow['artifacts'].append(artifact_data)
            
            logger.info(f"Added artifact {event.artifact_id} to workflow {correlation_id}")
    
    async def handle_task_completed(self, event: StreamEvent):
        """Handle task completion events"""
        
        correlation_id = event.correlation_id
        workflow = self.active_workflows.get(correlation_id)
        
        if workflow and event.agent_id:
            # Update router with agent performance
            await self.router.update_agent_performance(event.agent_id, {
                'success': True,
                'quality_score': event.metadata.get('quality_score', 0.8),
                'cost': event.metadata.get('cost', 0.0),
                'processing_time': event.metadata.get('processing_time', 0.0),
                'task_type': event.payload.get('primary_task_type')
            })
    
    async def handle_task_failed(self, event: StreamEvent):
        """Handle task failure events"""
        
        # Update router with failure
        if event.agent_id:
            await self.router.update_agent_performance(event.agent_id, {
                'success': False,
                'error': event.payload.get('error', 'Unknown error')
            })
        
        # Implement retry logic or escalation
        logger.warning(f"Task failed for agent {event.agent_id}: {event.payload.get('error')}")
    
    def get_live_project_status(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of live project"""
        
        workflow = self.active_workflows.get(correlation_id)
        if not workflow:
            return None
        
        current_phase = workflow['current_phase']
        phases = workflow['phases']
        
        return {
            'correlation_id': correlation_id,
            'status': workflow['status'],
            'description': workflow['description'],
            'current_phase': current_phase,
            'current_phase_name': phases[current_phase]['name'] if current_phase < len(phases) else 'Complete',
            'total_phases': len(phases),
            'progress_percentage': (current_phase / len(phases)) * 100,
            'artifacts_created': len(workflow['artifacts']),
            'agent_assignments': workflow['agent_assignments'],
            'start_time': workflow['start_time'].isoformat(),
            'phases': phases
        }
    
    def get_all_live_projects(self) -> List[Dict[str, Any]]:
        """Get status of all live projects"""
        
        return [
            self.get_live_project_status(correlation_id)
            for correlation_id in self.active_workflows.keys()
        ]
    
    def get_orchestrator_metrics(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator metrics"""
        
        active_projects = len([w for w in self.active_workflows.values() if w['status'] == 'active'])
        completed_projects = len([w for w in self.active_workflows.values() if w['status'] == 'completed'])
        
        return {
            'total_projects': len(self.active_workflows),
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'agent_metrics': self.agent_orchestrator.get_worker_metrics(),
            'routing_stats': self.router.get_routing_stats(),
            'quality_cascades': {
                cascade_type: agents for cascade_type, agents in self.quality_cascade.items()
            }
        }
    
    async def stop_orchestrator(self):
        """Stop the orchestrator and all agents"""
        
        self.agent_orchestrator.stop_workers()
        
        # Mark all active workflows as stopped
        for workflow in self.active_workflows.values():
            if workflow['status'] == 'active':
                workflow['status'] = 'stopped'
        
        logger.info("Live orchestrator stopped")
    
    def get_real_agent_results(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Get real agent execution results for a project"""
        workflow = self.active_workflows.get(correlation_id)
        if workflow:
            return workflow.get('real_agent_results', [])
        return []
    
    def get_project_progress(self, correlation_id: str) -> Dict[str, Any]:
        """Get detailed project progress including real agent results"""
        workflow = self.active_workflows.get(correlation_id)
        if not workflow:
            return {}
        
        real_results = workflow.get('real_agent_results', [])
        total_phases = 5  # We have 5 phases in real execution
        completed_phases = len(real_results)
        
        return {
            'correlation_id': correlation_id,
            'description': workflow.get('description', ''),
            'status': workflow.get('status', 'unknown'),
            'progress_percentage': (completed_phases / total_phases) * 100,
            'phases_completed': completed_phases,
            'total_phases': total_phases,
            'real_agent_results': real_results,
            'start_time': workflow.get('start_time'),
            'completion_time': workflow.get('completion_time'),
            'artifacts_created': len(real_results)
        }