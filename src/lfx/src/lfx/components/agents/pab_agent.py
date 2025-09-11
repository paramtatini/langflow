from typing import Any

import httpx
from pydantic import BaseModel

from lfx.custom.custom_component.component import Component
from lfx.io import BoolInput, DropdownInput, IntInput, MessageTextInput, MultilineInput, Output, StrInput
from lfx.schema.message import Message


class PABCredentials(BaseModel):
    client_id: str
    client_secret: str
    token_url: str
    service_url: str


class PABAgentComponent(Component):
    display_name: str = "PAB Agent"
    description: str = (
        "Create and execute tasks using SAP Project Agent Builder (PAB) agents with advanced AI capabilities."
    )
    icon: str = "bot"
    name: str = "PABAgent"

    inputs = [
        DropdownInput(
            name="agent_id",
            display_name="Select Existing PAB Agent",
            info="Select an existing PAB agent to use for task execution, or leave empty to create a new agent.",
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
            info="The message or task to send to the PAB agent.",
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

    async def get_oauth_token(self, credentials: PABCredentials) -> str:
        """Get OAuth token from SAP authentication service."""
        async with httpx.AsyncClient() as client:
            form_data = {
                "grant_type": "client_credentials",
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }

            response = await client.post(credentials.token_url, data=form_data, headers=headers, timeout=30.0)
            response.raise_for_status()

            token_data = response.json()
            return token_data["access_token"]

    async def create_pab_agent(self, credentials: PABCredentials, access_token: str) -> str:
        """Create a new PAB agent with the specified configuration."""
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
                "type": "smart",  # Default type for PAB agents
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
                f"{credentials.service_url}/api/v1/Agents",
                json=agent_payload,
                headers=headers,
                timeout=60.0,
            )
            response.raise_for_status()

            result = response.json()
            return result.get("ID", result.get("id", ""))

    async def execute_pab_agent(
        self, credentials: PABCredentials, agent_id: str, message: str, access_token: str
    ) -> str:
        """Execute a task using the PAB agent."""
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
                f"{credentials.service_url}/api/v1/Agents({agent_id})/execute",
                json=payload,
                headers=headers,
                timeout=60.0,
            )
            response.raise_for_status()

            result = response.json()
            return result.get("response", "No response from agent")

    async def get_stored_credentials(self) -> PABCredentials | None:
        """Get stored PAB credentials from global variables."""
        try:
            # Try to get from global variables first (for backward compatibility)
            import json

            try:
                from langflow.services.variable.utils import get_variable_value
            except ImportError:
                # Fallback for LFX environment
                import os
                async def get_variable_value(name: str, user_id: str = None):
                    return os.getenv(name)

            # Try to get the credentials from the global variable
            credentials_json = await get_variable_value(
                name="SAP_PAB_CREDENTIALS", user_id=getattr(self, "user_id", None)
            )

            if credentials_json:
                credentials_data = json.loads(credentials_json)
                return PABCredentials(**credentials_data)

            return None

        except Exception as e:
            # Log the error for debugging
            print(f"Error getting PAB credentials: {e!s}")
            return None

    async def get_available_agents(self) -> list[dict[str, Any]]:
        """Get available PAB agents from stored data."""
        try:
            # Try to get from global variables first (for backward compatibility)
            import json

            try:
                from langflow.services.variable.utils import get_variable_value
            except ImportError:
                # Fallback for LFX environment
                import os
                async def get_variable_value(name: str, user_id: str = None):
                    return os.getenv(name)

            # Try to get the agents from the global variable
            agents_json = await get_variable_value(name="SAP_PAB_AGENTS", user_id=getattr(self, "user_id", None))

            if agents_json:
                agents_data = json.loads(agents_json)
                return agents_data

            return []

        except Exception as e:
            # Log the error for debugging
            print(f"Error getting PAB agents: {e!s}")
            return []

    async def message_response(self) -> Message:
        """Execute the PAB agent and return the response as a Message."""
        if not self.input_value:
            return Message(
                text="Please provide a message or task for the agent to execute.",
                sender="PAB Agent",
                sender_name="PAB Agent",
            )

        try:
            # Get stored credentials
            credentials = await self.get_stored_credentials()
            if not credentials:
                return Message(
                    text="PAB credentials not found. Please configure your SAP PAB credentials in Settings > SAP AI Credentials.",
                    sender="PAB Agent",
                    sender_name="PAB Agent",
                )

            # Get OAuth token
            access_token = await self.get_oauth_token(credentials)

            # Determine which agent to use
            agent_id = self.agent_id
            agent_name = "PAB Agent"

            # If no existing agent selected, create a new one
            if not agent_id and self.agent_name:
                if not self.expertise or not self.initial_instructions:
                    return Message(
                        text="To create a new agent, please provide: Agent Name, Expertise, and Initial Instructions.",
                        sender="PAB Agent",
                        sender_name="PAB Agent",
                    )

                # Create new agent
                agent_id = await self.create_pab_agent(credentials, access_token)
                agent_name = self.agent_name

                if not agent_id:
                    return Message(
                        text="Failed to create new PAB agent. Please check your configuration and try again.",
                        sender="PAB Agent",
                        sender_name="PAB Agent",
                    )

                # Refresh the agents list to include the new agent
                try:
                    import json

                    try:
                        from langflow.services.variable.utils import update_variable_value
                    except ImportError:
                        # Fallback for LFX environment
                        async def update_variable_value(name: str, value: str, user_id: str = None):
                            print(f"Warning: Cannot update variable {name} in LFX environment")
                            return False

                    # Get current agents
                    agents = await self.get_available_agents()

                    # Add the new agent to the list
                    new_agent = {
                        "ID": agent_id,
                        "name": self.agent_name,
                        "type": "smart",
                        "safetyCheck": True,
                        "expertIn": self.expertise,
                        "initialInstructions": self.initial_instructions,
                        "iterations": self.max_thinking_steps,
                        "baseModel": self.base_model,
                        "advancedModel": self.advanced_model,
                        "preprocessingEnabled": self.preprocessing_enabled,
                        "postprocessingEnabled": self.postprocessing_enabled,
                        "createdAt": "",  # Will be set by PAB service
                        "modifiedAt": "",  # Will be set by PAB service
                    }
                    agents.append(new_agent)

                    # Update the stored agents list
                    await update_variable_value(
                        name="SAP_PAB_AGENTS", value=json.dumps(agents), user_id=getattr(self, "user_id", None)
                    )

                except Exception as e:
                    # Log error but continue with execution
                    print(f"Warning: Could not update agents list: {e}")

            elif not agent_id:
                return Message(
                    text="Please either select an existing PAB agent or provide agent details to create a new one.",
                    sender="PAB Agent",
                    sender_name="PAB Agent",
                )

            # Prepare the message
            message_text = self.input_value
            if isinstance(self.input_value, Message):
                message_text = self.input_value.text

            # Execute the agent
            response_text = await self.execute_pab_agent(
                credentials=credentials, agent_id=agent_id, message=str(message_text), access_token=access_token
            )

            return Message(
                text=response_text,
                sender="PAB Agent",
                sender_name=f"PAB Agent ({agent_name})",
            )

        except httpx.HTTPError as e:
            error_msg = f"HTTP error occurred: {e!s}"
            return Message(
                text=error_msg,
                sender="PAB Agent",
                sender_name="PAB Agent",
            )
        except Exception as e:
            error_msg = f"Error executing PAB agent: {e!s}"
            return Message(
                text=error_msg,
                sender="PAB Agent",
                sender_name="PAB Agent",
            )

    async def update_build_config(self, build_config, field_value: Any, field_name: str | None = None):
        """Update build configuration, particularly for agent selection."""
        if field_name == "agent_id":
            # Update available agents when component is loaded
            try:
                agents = await self.get_available_agents()
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
