from typing import Any
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel

from lfx.custom.custom_component.component import Component
from lfx.io import BoolInput, DropdownInput, IntInput, MessageTextInput, MultilineInput, Output, StrInput
from lfx.schema.message import Message


class PABCredentials(BaseModel):
    """PAB credentials model supporting both service key and direct format."""
    client_id: str
    client_secret: str
    token_url: str
    agent_api_url: str


class AribaAgentComponent(Component):
    display_name: str = "Ariba Agent"
    description: str = (
        "Execute tasks using SAP Ariba virtual agents powered by Project Agent Builder (PAB). "
        "These agents are developed using PAB Agent runtime and have the same capabilities as PAB agents."
    )
    icon: str = "bot"
    name: str = "AribaAgent"

    inputs = [
        DropdownInput(
            name="agent_id",
            display_name="Select Ariba Agent",
            info="Select an existing Ariba agent to use for task execution.",
            options=[],
            value="",
            real_time_refresh=True,
            advanced=False,
        ),
        StrInput(
            name="agent_name",
            display_name="Name",
            info="Enter Agent Name (required for creating new agents).",
            value="",
            required=False,
        ),
        StrInput(
            name="expertise",
            display_name="Expertise",
            info="Short description of what the agent is an expert in.",
            value="",
            required=False,
        ),
        MultilineInput(
            name="initial_instructions",
            display_name="Initial Instructions",
            info="Initial instructions that are used for every new chat session.",
            value="",
            required=False,
        ),
        IntInput(
            name="max_thinking_steps",
            display_name="Maximum Thinking Steps",
            info="Maximum thinking steps (5-100).",
            value=20,
            range_spec={"min": 5, "max": 100, "step": 1},
        ),
        BoolInput(
            name="preprocessing_enabled",
            display_name="Pre-processing",
            info="Enable/disable pre-processing.",
            value=True,
        ),
        BoolInput(
            name="postprocessing_enabled",
            display_name="Post-processing",
            info="Enable/disable post-processing.",
            value=True,
        ),
        MultilineInput(
            name="orchestration_config",
            display_name="Orchestration Module Configuration",
            info="JSON configuration for orchestration modules (masking, filtering, etc.).",
            value='{\n  "masking_module_config": {"masking_providers": [...]},\n  "filtering_module_config": {...}\n}',
            advanced=True,
        ),
        DropdownInput(
            name="llm_provider",
            display_name="LLM Provider",
            info="Select the LLM provider for the agent.",
            options=["Google", "MistralAI", "OpenAI"],
            value="OpenAI",
        ),
        DropdownInput(
            name="base_model",
            display_name="Base Model",
            info="Select the base model for the agent.",
            options=["GPT4o Mini", "GPT4o", "Claude 3.5 Sonnet", "Gemini 1.5 Pro"],
            value="GPT4o Mini",
        ),
        DropdownInput(
            name="advanced_model",
            display_name="Advanced Model",
            info="Select the advanced model for the agent.",
            options=["GPT4o", "Claude 3.5 Sonnet", "Gemini 1.5 Pro"],
            value="GPT4o",
        ),
        MessageTextInput(
            name="input_value",
            display_name="Message",
            info="The message or task to send to the Ariba agent.",
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

    async def get_credentials_from_backend(self) -> PABCredentials | None:
        """Get PAB credentials from the backend API endpoint."""
        try:
            # Use the backend API endpoint to get credentials
            async with httpx.AsyncClient() as client:
                # In a real scenario, we would need proper authentication
                # For now, we'll simulate the API call structure
                response = await client.get(
                    "http://localhost:7860/api/v1/sap/pab/credentials",
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    credentials_data = response.json()
                    
                    # Handle service key format
                    if "service_urls" in credentials_data and "uaa" in credentials_data:
                        service_urls = credentials_data["service_urls"]
                        uaa = credentials_data["uaa"]
                        
                        return PABCredentials(
                            client_id=uaa["clientid"],
                            client_secret=uaa["clientsecret"],
                            token_url=f"{uaa['url']}/oauth/token",
                            agent_api_url=service_urls.get("agent_api_url", "")
                        )
                    
                    # Handle direct format
                    elif all(key in credentials_data for key in ["client_id", "client_secret", "token_url", "agent_api_url"]):
                        return PABCredentials(**credentials_data)
                
                return None
                
        except Exception as e:
            print(f"Error getting credentials from backend: {e}")
            return None

    async def get_oauth_token(self, credentials: PABCredentials) -> str:
        """Get OAuth token from SAP XSUAA service using client credentials flow."""
        async with httpx.AsyncClient() as client:
            # Prepare form data for OAuth token request
            form_data = {
                "grant_type": "client_credentials",
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }

            # Make the OAuth token request
            response = await client.post(
                credentials.token_url,
                data=urlencode(form_data),
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()

            token_data = response.json()
            return token_data.get("access_token", "")

    async def fetch_available_agents(self, credentials: PABCredentials, access_token: str) -> list[dict[str, Any]]:
        """Fetch available agents from PAB API."""
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }

            # Make the API request to get agents
            agents_url = f"{credentials.agent_api_url}/api/v1/Agents"
            
            response = await client.get(
                agents_url,
                headers=headers,
                timeout=60.0
            )
            response.raise_for_status()

            agents_data = response.json()
            
            # Ensure we return a list
            if isinstance(agents_data, list):
                return agents_data
            elif isinstance(agents_data, dict) and "value" in agents_data:
                # Handle OData response format
                return agents_data["value"]
            else:
                return [agents_data] if agents_data else []

    async def create_ariba_agent(self, credentials: PABCredentials, access_token: str) -> str:
        """Create a new Ariba agent with the specified configuration."""
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            # Map LLM provider and model names to PAB API format
            model_mapping = {
                "GPT4o Mini": "OpenAiGpt4oMini",
                "GPT4o": "OpenAiGpt4o",
                "Claude 3.5 Sonnet": "AnthropicClaude35Sonnet",
                "Gemini 1.5 Pro": "GoogleGemini15Pro",
            }

            base_model = model_mapping.get(self.base_model, "OpenAiGpt4oMini")
            advanced_model = model_mapping.get(self.advanced_model, "OpenAiGpt4o")

            # Parse orchestration config if provided
            orchestration_config = {}
            if hasattr(self, "orchestration_config") and self.orchestration_config:
                try:
                    import json
                    orchestration_config = json.loads(self.orchestration_config)
                except json.JSONDecodeError:
                    # Use default empty config if parsing fails
                    orchestration_config = {}

            # Prepare the agent creation payload
            agent_payload = {
                "name": self.agent_name,
                "type": "smart",  # Default type for Ariba agents
                "safetyCheck": True,  # Default safety check enabled
                "expertIn": self.expertise,
                "initialInstructions": self.initial_instructions,
                "iterations": self.max_thinking_steps,
                "baseModel": base_model,
                "advancedModel": advanced_model,
                "preprocessingEnabled": self.preprocessing_enabled,
                "postprocessingEnabled": self.postprocessing_enabled,
                **orchestration_config,  # Include any orchestration configuration
            }

            # Create the agent
            response = await client.post(
                f"{credentials.agent_api_url}/api/v1/Agents",
                json=agent_payload,
                headers=headers,
                timeout=60.0,
            )
            response.raise_for_status()

            result = response.json()
            return result.get("ID", result.get("id", ""))

    async def execute_ariba_agent(
        self, credentials: PABCredentials, agent_id: str, message: str, access_token: str
    ) -> str:
        """Execute a task using the Ariba agent."""
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            # Prepare the message payload for the agent
            payload = {
                "message": message,
                "additional_instructions": self.additional_instructions
                if hasattr(self, "additional_instructions")
                else "",
            }

            # Execute the agent (this endpoint may vary based on PAB API)
            response = await client.post(
                f"{credentials.agent_api_url}/api/v1/Agents({agent_id})/execute",
                json=payload,
                headers=headers,
                timeout=60.0,
            )
            response.raise_for_status()

            result = response.json()
            return result.get("response", "No response from agent")

    async def message_response(self) -> Message:
        """Execute the Ariba agent and return the response as a Message."""
        if not self.input_value:
            return Message(
                text="Please provide a message or task for the agent to execute.",
                sender="Ariba Agent",
                sender_name="Ariba Agent",
            )

        try:
            # Get credentials from backend API
            credentials = await self.get_credentials_from_backend()
            if not credentials:
                return Message(
                    text="PAB credentials not found. Please configure your SAP PAB credentials in Settings > SAP AI Credentials.",
                    sender="Ariba Agent",
                    sender_name="Ariba Agent",
                )

            # Get OAuth token
            access_token = await self.get_oauth_token(credentials)

            # Determine which agent to use
            agent_id = self.agent_id
            agent_name = "Ariba Agent"

            # If no existing agent selected, create a new one
            if not agent_id and self.agent_name:
                if not self.expertise or not self.initial_instructions:
                    return Message(
                        text="To create a new agent, please provide: Agent Name, Expertise, and Initial Instructions.",
                        sender="Ariba Agent",
                        sender_name="Ariba Agent",
                    )

                # Create new agent
                agent_id = await self.create_ariba_agent(credentials, access_token)
                agent_name = self.agent_name

                if not agent_id:
                    return Message(
                        text="Failed to create new Ariba agent. Please check your configuration and try again.",
                        sender="Ariba Agent",
                        sender_name="Ariba Agent",
                    )

            elif not agent_id:
                return Message(
                    text="Please either select an existing Ariba agent or provide agent details to create a new one.",
                    sender="Ariba Agent",
                    sender_name="Ariba Agent",
                )

            # Prepare the message
            message_text = self.input_value
            if isinstance(self.input_value, Message):
                message_text = self.input_value.text

            # Execute the agent
            response_text = await self.execute_ariba_agent(
                credentials=credentials, agent_id=agent_id, message=str(message_text), access_token=access_token
            )

            return Message(
                text=response_text,
                sender="Ariba Agent",
                sender_name=f"Ariba Agent ({agent_name})",
            )

        except httpx.HTTPError as e:
            error_msg = f"HTTP error occurred: {e!s}"
            return Message(
                text=error_msg,
                sender="Ariba Agent",
                sender_name="Ariba Agent",
            )
        except Exception as e:
            error_msg = f"Error executing Ariba agent: {e!s}"
            return Message(
                text=error_msg,
                sender="Ariba Agent",
                sender_name="Ariba Agent",
            )

    async def update_build_config(self, build_config, field_value: Any, field_name: str | None = None):
        """Update build configuration, particularly for agent selection."""
        if field_name == "agent_id":
            # Update available agents when component is loaded
            try:
                credentials = await self.get_credentials_from_backend()
                if credentials:
                    access_token = await self.get_oauth_token(credentials)
                    agents = await self.fetch_available_agents(credentials, access_token)
                    
                    agent_options = [
                        {"label": agent.get("name", agent.get("ID", "Unknown")), "value": agent.get("ID", "")}
                        for agent in agents
                    ]

                    if "agent_id" in build_config:
                        build_config["agent_id"]["options"] = [opt["value"] for opt in agent_options]

            except Exception:
                # If we can't get agents, keep empty options
                if "agent_id" in build_config:
                    build_config["agent_id"]["options"] = []

        return build_config
