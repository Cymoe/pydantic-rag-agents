"""
Message Control Point (MCP) implementation for agent communication.

This module provides a centralized message routing system for inter-agent
communication using an asynchronous publish-subscribe pattern.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Callable, List, Set
import asyncio
import logging

@dataclass
class MessageControlPoint:
    """
    A message control point that handles routing messages between agents.
    
    Attributes:
        name: Unique identifier for this MCP
        handlers: Dictionary mapping message types to handler functions
        queue: Async queue for message processing
        subscribers: Set of topics this MCP is subscribed to
    """
    name: str
    handlers: Dict[str, Callable]
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    subscribers: Set[str] = field(default_factory=set)

    async def publish(self, topic: str, message: Any):
        """Publish a message to a specific topic."""
        if topic in self.handlers:
            await self.queue.put((topic, message))
            logging.debug(f"MCP {self.name} published message to {topic}")

    async def subscribe(self, topic: str, handler: Callable):
        """Subscribe to a topic with a handler function."""
        self.handlers[topic] = handler
        self.subscribers.add(topic)
        logging.debug(f"MCP {self.name} subscribed to {topic}")

    async def unsubscribe(self, topic: str):
        """Unsubscribe from a topic."""
        if topic in self.handlers:
            del self.handlers[topic]
        self.subscribers.discard(topic)
        logging.debug(f"MCP {self.name} unsubscribed from {topic}")

    async def start(self):
        """Start processing messages from the queue."""
        logging.info(f"MCP {self.name} started")
        while True:
            topic, message = await self.queue.get()
            if topic in self.handlers:
                try:
                    await self.handlers[topic](message)
                except Exception as e:
                    logging.error(f"Error in MCP {self.name} handling {topic}: {e}")
            self.queue.task_done()

# Global registry of MCPs
mcp_registry: Dict[str, MessageControlPoint] = {}