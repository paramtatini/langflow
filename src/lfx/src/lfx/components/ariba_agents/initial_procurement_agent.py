from typing import Any

import httpx

from lfx.custom.custom_component.component import Component
from lfx.io import BoolInput, DropdownInput, IntInput, MessageTextInput, MultilineInput, Output, StrInput
from lfx.schema.message import Message


class InitialProcurementAgentComponent(Component):
    display_name: str = "Initial Procurement Agent"
    description: str = "Initial Procurement Agent - A specialized Ariba agent for initial procurement processes and workflows."
    icon: str = "bot"
    name: str = "InitialProcurementAgent"

    inputs = [
        StrInput(
            name="agent_name",
            display_name="Name",
            info="Agent Name (fetched from PAB)",
            value="",
            required=False,
        ),
        StrInput(
            name="expertise",
            display_name="Expertise",
            info="What the agent is expert in (fetched from PAB)",
            value="",
            required=False,
        ),
        MultilineInput(
            name="initial_instructions",
            display_name="Initial Instructions",
            info="Initial instructions for the agent (fetched from PAB)",
            value="",
            required=False,
        ),
        IntInput(
            name="max_thinking_steps",
            display_name="Maximum Thinking Steps",
            info="Maximum thinking steps (5-100)",
            value=20,
            range_spec={"min": 5, "max": 100, "step": 1},
        ),
        BoolInput(
            name="preprocessing_enabled",
            display_name="Pre-processing",
            info="Enable/disable pre-processing",
            value=True,
        ),
        BoolInput(
            name="postprocessing_enabled",
            display_name="Post-processing",
            info="Enable/disable post-processing",
            value=True,
        ),
        DropdownInput(
            name="llm_provider",
            display_name="LLM Provider",
            info="Select the LLM provider for the agent",
            options=["Google", "MistralAI", "OpenAI"],
            value="OpenAI",
        ),
        DropdownInput(
            name="base_model",
            display_name="Base Model",
            info="Select the base model for the agent",
            options=["GPT4o Mini", "GPT4o", "Claude 3.5 Sonnet", "Gemini 1.5 Pro"],
            value="GPT4o Mini",
        ),
        DropdownInput(
            name="advanced_model",
            display_name="Advanced Model",
            info="Select the advanced model for the agent",
            options=["GPT4o", "Claude 3.5 Sonnet", "Gemini 1.5 Pro"],
            value="GPT4o",
        ),
        MessageTextInput(
            name="input_value",
            display_name="Message",
            info="The message or task to send to the Initial Procurement Agent",
            tool_mode=True,
        ),
        MultilineInput(
            name="additional_instructions",
            display_name="Additional Instructions",
            info="Optional additional instructions to provide context for the agent",
            value="",
            advanced=True,
        ),
    ]

    outputs = [
        Output(display_name="Response", name="response", method="message_response"),
    ]

    # Fixed agent ID for this specific agent
    AGENT_ID = "42040d8d-9591-4146-840a-d97fc6527a27"

    async def get_agent_data_from_api(self) -> dict | None:
        """Fetch agent data from the backend API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:7860/api/v1/sap/ariba_agents",
                    timeout=30.0,
                )
                response.raise_for_status()
                
                agents = response.json()
                
                # Find this specific agent by ID
                for agent in agents:
                    if agent.get("ID") == self.AGENT_ID or agent.get("id") == self.AGENT_ID:
                        return agent
                
                return None
                
        except Exception as e:
            print(f"Error fetching agent data: {e}")
            return None

    async def message_response(self) -> Message:
        """Execute the Initial Procurement Agent and return the response as a Message."""
        if not self.input_value:
            return Message(
                text="Please provide a message or task for the Initial Procurement Agent to execute.",
                sender="Initial Procurement Agent",
                sender_name="Initial Procurement Agent",
            )

        try:
            # Use the backend API endpoint to execute the agent
            async with httpx.AsyncClient() as client:
                payload = {
                    "agent_id": self.AGENT_ID,
                    "message": str(self.input_value.text if hasattr(self.input_value, 'text') else self.input_value),
                    "additional_instructions": self.additional_instructions if hasattr(self, "additional_instructions") else "",
                }

                response = await client.post(
                    "http://localhost:7860/api/v1/sap/ariba_agents/execute",
                    json=payload,
                    timeout=60.0,
                )
                response.raise_for_status()

                result = response.json()
                response_text = result.get("response", "No response from agent")

                return Message(
                    text=response_text,
                    sender="Initial Procurement Agent",
                    sender_name="Initial Procurement Agent",
                )

        except httpx.HTTPError as e:
            error_msg = f"HTTP error occurred: {e!s}"
            return Message(
                text=error_msg,
                sender="Initial Procurement Agent",
                sender_name="Initial Procurement Agent",
            )
        except Exception as e:
            error_msg = f"Error executing Initial Procurement Agent: {e!s}"
            return Message(
                text=error_msg,
                sender="Initial Procurement Agent",
                sender_name="Initial Procurement Agent",
            )

    async def update_build_config(self, build_config, field_value: Any, field_name: str | None = None):
        """Update build configuration with real agent data from API."""
        try:
            # Fetch agent data from API
            agent_data = await self.get_agent_data_from_api()
            
            if agent_data:
                # Update the build config with real agent data
                if "agent_name" in build_config:
                    build_config["agent_name"]["value"] = agent_data.get("name", "Initial Procurement Agent")
                
                if "expertise" in build_config:
                    build_config["expertise"]["value"] = agent_data.get("expertIn", "")
                
                if "initial_instructions" in build_config:
                    build_config["initial_instructions"]["value"] = agent_data.get("initialInstructions", "")
                
                if "max_thinking_steps" in build_config:
                    build_config["max_thinking_steps"]["value"] = agent_data.get("iterations", 20)
                
                if "preprocessing_enabled" in build_config:
                    build_config["preprocessing_enabled"]["value"] = agent_data.get("preprocessingEnabled", True)
                
                if "postprocessing_enabled" in build_config:
                    build_config["postprocessing_enabled"]["value"] = agent_data.get("postprocessingEnabled", True)
                
                # Map model names from PAB format to UI format
                model_mapping = {
                    "OpenAiGpt4oMini": "GPT4o Mini",
                    "OpenAiGpt4o": "GPT4o",
                    "AnthropicClaude35Sonnet": "Claude 3.5 Sonnet",
                    "GoogleGemini15Pro": "Gemini 1.5 Pro",
                }
                
                if "base_model" in build_config:
                    pab_base_model = agent_data.get("baseModel", "OpenAiGpt4oMini")
                    build_config["base_model"]["value"] = model_mapping.get(pab_base_model, "GPT4o Mini")
                
                if "advanced_model" in build_config:
                    pab_advanced_model = agent_data.get("advancedModel", "OpenAiGpt4o")
                    build_config["advanced_model"]["value"] = model_mapping.get(pab_advanced_model, "GPT4o")

        except Exception as e:
            print(f"Error updating build config with agent data: {e}")
            # Continue with default values if API call fails

        return build_config
