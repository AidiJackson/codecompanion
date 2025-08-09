"""
Agent communication protocols and message handling
"""
import json
import uuid
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of messages between agents"""
    REQUEST = "request"
    RESPONSE = "response"
    HANDOFF = "handoff"
    STATUS_UPDATE = "status_update"
    ERROR = "error"
    BROADCAST = "broadcast"

class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class Message:
    """Message structure for agent communication"""
    message_id: str
    sender: str
    recipient: str
    message_type: MessageType
    content: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = None
    correlation_id: str = None
    requires_response: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['message_type'] = self.message_type.value
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['message_type'] = MessageType(data['message_type'])
        data['priority'] = MessagePriority(data['priority'])
        return cls(**data)

class MessageQueue:
    """Message queue for handling agent communications"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.messages: List[Message] = []
        self.handlers: Dict[MessageType, List[Callable]] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
    
    def add_message(self, message: Message) -> bool:
        """Add message to queue"""
        if len(self.messages) >= self.max_size:
            # Remove oldest low priority messages
            self.messages = [m for m in self.messages if m.priority != MessagePriority.LOW]
            
            if len(self.messages) >= self.max_size:
                logger.warning("Message queue full, dropping oldest message")
                self.messages.pop(0)
        
        # Insert message based on priority
        inserted = False
        for i, existing_msg in enumerate(self.messages):
            if message.priority.value > existing_msg.priority.value:
                self.messages.insert(i, message)
                inserted = True
                break
        
        if not inserted:
            self.messages.append(message)
        
        logger.debug(f"Added message {message.message_id} to queue")
        return True
    
    def get_messages(self, recipient: str = None, message_type: MessageType = None) -> List[Message]:
        """Get messages from queue with optional filtering"""
        messages = self.messages.copy()
        
        if recipient:
            messages = [m for m in messages if m.recipient == recipient or m.recipient == "all"]
        
        if message_type:
            messages = [m for m in messages if m.message_type == message_type]
        
        return messages
    
    def remove_message(self, message_id: str) -> bool:
        """Remove message from queue"""
        for i, message in enumerate(self.messages):
            if message.message_id == message_id:
                self.messages.pop(i)
                logger.debug(f"Removed message {message_id} from queue")
                return True
        return False
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register handler for specific message type"""
        if message_type not in self.handlers:
            self.handlers[message_type] = []
        self.handlers[message_type].append(handler)
    
    def process_messages(self, agent_name: str = None):
        """Process messages for a specific agent or all messages"""
        messages_to_process = self.get_messages(agent_name)
        
        for message in messages_to_process:
            try:
                # Find handlers for message type
                handlers = self.handlers.get(message.message_type, [])
                
                for handler in handlers:
                    handler(message)
                
                # Remove processed message
                self.remove_message(message.message_id)
                
            except Exception as e:
                logger.error(f"Error processing message {message.message_id}: {e}")

class AgentCommunication:
    """Central communication system for agent interactions"""
    
    def __init__(self):
        self.message_queue = MessageQueue()
        self.active_conversations: Dict[str, List[Message]] = {}
        self.agent_status: Dict[str, Dict[str, Any]] = {}
        self.handoff_history: List[Dict[str, Any]] = []
        self.broadcast_subscribers: List[str] = []
    
    def send_message(self, 
                    sender: str, 
                    recipient: str, 
                    message_type: MessageType,
                    content: Dict[str, Any],
                    priority: MessagePriority = MessagePriority.NORMAL,
                    correlation_id: str = None) -> str:
        """Send a message between agents"""
        
        message = Message(
            message_id=str(uuid.uuid4())[:8],
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            content=content,
            priority=priority,
            correlation_id=correlation_id
        )
        
        # Add to queue
        self.message_queue.add_message(message)
        
        # Track conversation
        conv_key = f"{sender}-{recipient}"
        if conv_key not in self.active_conversations:
            self.active_conversations[conv_key] = []
        self.active_conversations[conv_key].append(message)
        
        logger.info(f"Message sent from {sender} to {recipient}: {message_type.value}")
        return message.message_id
    
    def send_handoff(self, 
                    from_agent: str, 
                    to_agent: str, 
                    content: str,
                    context: Dict[str, Any] = None) -> str:
        """Send handoff message between agents"""
        
        handoff_data = {
            "handoff_content": content,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
            "reason": "Agent collaboration handoff"
        }
        
        message_id = self.send_message(
            sender=from_agent,
            recipient=to_agent,
            message_type=MessageType.HANDOFF,
            content=handoff_data,
            priority=MessagePriority.HIGH
        )
        
        # Track handoff history
        self.handoff_history.append({
            "message_id": message_id,
            "from_agent": from_agent,
            "to_agent": to_agent,
            "timestamp": datetime.now().isoformat(),
            "content_preview": content[:100] + "..." if len(content) > 100 else content
        })
        
        logger.info(f"Handoff from {from_agent} to {to_agent}")
        return message_id
    
    def broadcast_message(self, 
                         sender: str, 
                         content: Dict[str, Any],
                         priority: MessagePriority = MessagePriority.NORMAL) -> List[str]:
        """Broadcast message to all subscribed agents"""
        
        message_ids = []
        
        for recipient in self.broadcast_subscribers:
            if recipient != sender:  # Don't send to self
                message_id = self.send_message(
                    sender=sender,
                    recipient=recipient,
                    message_type=MessageType.BROADCAST,
                    content=content,
                    priority=priority
                )
                message_ids.append(message_id)
        
        logger.info(f"Broadcast from {sender} to {len(message_ids)} recipients")
        return message_ids
    
    def update_agent_status(self, 
                           agent_name: str, 
                           status: str,
                           current_task: str = None,
                           progress: int = 0,
                           additional_info: Dict[str, Any] = None):
        """Update agent status"""
        
        status_info = {
            "status": status,
            "current_task": current_task,
            "progress": progress,
            "last_updated": datetime.now().isoformat(),
            "additional_info": additional_info or {}
        }
        
        self.agent_status[agent_name] = status_info
        
        # Broadcast status update if significant
        if status in ["working", "completed", "error"]:
            self.broadcast_message(
                sender="system",
                content={
                    "type": "status_update",
                    "agent": agent_name,
                    "status": status_info
                },
                priority=MessagePriority.LOW
            )
        
        logger.debug(f"Updated status for {agent_name}: {status}")
    
    def get_agent_status(self, agent_name: str = None) -> Dict[str, Any]:
        """Get agent status"""
        if agent_name:
            return self.agent_status.get(agent_name, {})
        return self.agent_status.copy()
    
    def get_conversation_history(self, 
                                agent1: str, 
                                agent2: str = None,
                                limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history between agents"""
        
        if agent2:
            # Get conversation between two specific agents
            conv_keys = [f"{agent1}-{agent2}", f"{agent2}-{agent1}"]
            messages = []
            
            for key in conv_keys:
                if key in self.active_conversations:
                    messages.extend(self.active_conversations[key])
        else:
            # Get all conversations involving the agent
            messages = []
            for conv_key, conv_messages in self.active_conversations.items():
                if agent1 in conv_key:
                    messages.extend(conv_messages)
        
        # Sort by timestamp and limit
        messages.sort(key=lambda m: m.timestamp, reverse=True)
        messages = messages[:limit]
        
        return [message.to_dict() for message in messages]
    
    def get_handoff_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent handoff history"""
        return self.handoff_history[-limit:] if self.handoff_history else []
    
    def subscribe_to_broadcasts(self, agent_name: str):
        """Subscribe agent to broadcast messages"""
        if agent_name not in self.broadcast_subscribers:
            self.broadcast_subscribers.append(agent_name)
            logger.info(f"{agent_name} subscribed to broadcasts")
    
    def unsubscribe_from_broadcasts(self, agent_name: str):
        """Unsubscribe agent from broadcast messages"""
        if agent_name in self.broadcast_subscribers:
            self.broadcast_subscribers.remove(agent_name)
            logger.info(f"{agent_name} unsubscribed from broadcasts")
    
    def create_collaboration_session(self, 
                                   session_name: str,
                                   participating_agents: List[str],
                                   goal: str) -> Dict[str, Any]:
        """Create a collaboration session for multiple agents"""
        
        session_id = str(uuid.uuid4())[:8]
        session_info = {
            "session_id": session_id,
            "name": session_name,
            "participants": participating_agents,
            "goal": goal,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "messages": []
        }
        
        # Notify all participants
        for agent in participating_agents:
            self.send_message(
                sender="system",
                recipient=agent,
                message_type=MessageType.REQUEST,
                content={
                    "type": "collaboration_invitation",
                    "session_info": session_info
                },
                priority=MessagePriority.HIGH
            )
        
        logger.info(f"Created collaboration session {session_id} with {len(participating_agents)} agents")
        return session_info
    
    def get_communication_stats(self) -> Dict[str, Any]:
        """Get communication statistics"""
        
        total_messages = sum(len(msgs) for msgs in self.active_conversations.values())
        
        # Count messages by type
        message_type_counts = {}
        for messages in self.active_conversations.values():
            for message in messages:
                msg_type = message.message_type.value
                message_type_counts[msg_type] = message_type_counts.get(msg_type, 0) + 1
        
        # Most active conversations
        conversation_activity = {
            conv_key: len(messages) 
            for conv_key, messages in self.active_conversations.items()
        }
        
        most_active = sorted(conversation_activity.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_messages": total_messages,
            "active_conversations": len(self.active_conversations),
            "message_types": message_type_counts,
            "handoffs_completed": len(self.handoff_history),
            "broadcast_subscribers": len(self.broadcast_subscribers),
            "most_active_conversations": most_active,
            "queue_size": len(self.message_queue.messages)
        }
    
    def cleanup_old_messages(self, days_old: int = 7):
        """Clean up old messages and conversations"""
        cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
        
        # Clean up old conversations
        for conv_key in list(self.active_conversations.keys()):
            messages = self.active_conversations[conv_key]
            recent_messages = [
                msg for msg in messages 
                if msg.timestamp.timestamp() > cutoff_time
            ]
            
            if recent_messages:
                self.active_conversations[conv_key] = recent_messages
            else:
                del self.active_conversations[conv_key]
        
        # Clean up old handoff history
        self.handoff_history = [
            handoff for handoff in self.handoff_history
            if datetime.fromisoformat(handoff['timestamp']).timestamp() > cutoff_time
        ]
        
        logger.info(f"Cleaned up messages older than {days_old} days")

# Global communication instance
communication_system = AgentCommunication()

# Helper functions for easy access
def send_agent_message(sender: str, recipient: str, content: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL) -> str:
    """Helper function to send message"""
    return communication_system.send_message(sender, recipient, MessageType.REQUEST, content, priority)

def send_agent_handoff(from_agent: str, to_agent: str, content: str, context: Dict[str, Any] = None) -> str:
    """Helper function to send handoff"""
    return communication_system.send_handoff(from_agent, to_agent, content, context)

def update_status(agent_name: str, status: str, task: str = None, progress: int = 0):
    """Helper function to update agent status"""
    return communication_system.update_agent_status(agent_name, status, task, progress)
