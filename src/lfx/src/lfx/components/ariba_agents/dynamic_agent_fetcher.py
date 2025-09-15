"""
Dynamic Ariba Agent Fetcher

This module creates virtual components for each Ariba agent fetched from the backend API.
Each agent becomes an individual component in the Ariba_agents group.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import httpx

from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, MultilineInput, Output
from lfx.schema.message import Message

logger = logging.getLogger(__name__)


async def fetch_ariba_agents_from_backend() -> List[Dict[str, Any]]:
    """Fetch Ariba agents from the backend API endpoint."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Call the backend API endpoint
            response = await client.get("http://localhost:7860/api/v1/sap/ariba_agents")
            
            if response.status_code == 200:
                agents = response.json()
                logger.info(f"Successfully fetched {len(agents)} Ariba agents from backend")
                return agents
            else:
                logger.warning(f"Failed to fetch agents: HTTP {response.status_code} - {response.text}")
                return []
                
    except httpx.ConnectError as e:
        logger.error(f"Connection error fetching Ariba agents from backend: {e}")
        return []
    except httpx.TimeoutException as e:
        logger.error(f"Timeout error fetching Ariba agents from backend: {e}")
        return []
    except Exception as e:
        logger.error(f"Error fetching Ariba agents from backend: {e}")
        return []


def create_dynamic_agent_component(agent_data: Dict[str, Any]) -> type:
    """Create a dynamic component class for a specific Ariba agent."""
    
    agent_id = agent_data.get("ID", "")
    agent_name = agent_data.get("name", "Unknown Agent")
    agent_expertise = agent_data.get("expertIn", "")
    agent_instructions = agent_data.get("initialInstructions", "")
    
    class DynamicAribaAgentComponent(Component):
        display_name: str = agent_name
        description: str = f"Ariba Agent: {agent_name}. Expert in: {agent_expertise}"
        icon: str = "bot"
        name: str = f"AribaAgent_{agent_id.replace('-', '_')}"
        
        inputs = [
            MessageTextInput(
                name="input_value",
                display_name="Message",
                info=f"Send a message to {agent_name}. This agent is expert in: {agent_expertise}",
                tool_mode=True,
            ),
            MultilineInput(
                name="additional_instructions",
                display_name="Additional Instructions",
                info="Optional additional instructions to provide context for the agent.",
                value="",
                advanced=True,
            ),
        ]

        outputs = [
            Output(display_name="Response", name="response", method="message_response"),
        ]

        def __init__(self):
            super().__init__()
            self.agent_data = agent_data
            self.agent_id = agent_id
            self.agent_name = agent_name

        async def execute_ariba_agent_via_backend(self, message: str) -> str:
            """Execute the agent via backend API."""
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    # Prepare the payload for the agent execution
                    payload = {
                        "agent_id": self.agent_id,
                        "message": message,
                        "additional_instructions": getattr(self, "additional_instructions", "")
                    }
                    
                    # Call backend API to execute the agent
                    response = await client.post(
                        "http://localhost:7860/api/v1/sap/ariba_agents/execute",
                        json=payload,
                        timeout=60.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return result.get("response", "No response from agent")
                    else:
                        return f"Error executing agent: HTTP {response.status_code}"
                        
            except Exception as e:
                logger.error(f"Error executing agent {self.agent_id}: {e}")
                return f"Error executing agent: {str(e)}"

        async def message_response(self) -> Message:
            """Execute the Ariba agent and return the response as a Message."""
            if not self.input_value:
                return Message(
                    text=f"Please provide a message for {self.agent_name} to process.",
                    sender=self.agent_name,
                    sender_name=self.agent_name,
                )

            try:
                # Prepare the message
                message_text = self.input_value
                if isinstance(self.input_value, Message):
                    message_text = self.input_value.text

                # Execute the agent via backend
                response_text = await self.execute_ariba_agent_via_backend(str(message_text))

                return Message(
                    text=response_text,
                    sender=self.agent_name,
                    sender_name=f"{self.agent_name} (Ariba Agent)",
                )

            except Exception as e:
                error_msg = f"Error executing {self.agent_name}: {str(e)}"
                logger.error(error_msg)
                return Message(
                    text=error_msg,
                    sender=self.agent_name,
                    sender_name=self.agent_name,
                )

    # Set the class name dynamically
    DynamicAribaAgentComponent.__name__ = f"AribaAgent_{agent_id.replace('-', '_')}"
    DynamicAribaAgentComponent.__qualname__ = f"AribaAgent_{agent_id.replace('-', '_')}"
    
    return DynamicAribaAgentComponent


async def get_dynamic_agent_components() -> Dict[str, type]:
    """Get all dynamic agent components by fetching from backend API."""
    agents = await fetch_ariba_agents_from_backend()
    components = {}
    
    for agent in agents:
        agent_id = agent.get("ID", "")
        if agent_id:
            component_name = f"AribaAgent_{agent_id.replace('-', '_')}"
            components[component_name] = create_dynamic_agent_component(agent)
    
    return components


# Cache for dynamic components to avoid repeated API calls
_dynamic_components_cache = None
_cache_timestamp = None


async def get_cached_dynamic_components() -> Dict[str, type]:
    """Get dynamic components with caching to avoid repeated API calls."""
    global _dynamic_components_cache, _cache_timestamp
    
    import time
    current_time = time.time()
    
    # Cache for 5 minutes
    if (_dynamic_components_cache is None or 
        _cache_timestamp is None or 
        current_time - _cache_timestamp > 300):
        
        _dynamic_components_cache = await get_dynamic_agent_components()
        _cache_timestamp = current_time
    
    return _dynamic_components_cache
