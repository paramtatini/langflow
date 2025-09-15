from typing import Any, Dict

import httpx

from lfx.custom.custom_component.component import Component
from lfx.io import (
    BoolInput,
    DropdownInput,
    IntInput,
    MessageTextInput,
    MultilineInput,
    Output,
    StrInput,
)
from lfx.schema.message import Message


class Subagent1Component(Component):
    display_name: str = "Subagent1"
    description: str = "Subagent1 - A specialized Ariba agent for sub-level processing and specialized tasks."
    icon: str = "bot"
    name: str = "Subagent1"

    inputs = [
        StrInput(
            name="agent_name",
            display_name="Name",
            info="The name of the agent",
            value="Subagent1",
            advanced=False,
        ),
        StrInput(
            name="expertise",
            display_name="Expertise",
            info="The area of expertise for this agent",
            value="Sub-level processing and specialized tasks",
            advanced=False,
        ),
        MultilineInput(
            name="initial_instructions",
            display_name="Initial Instructions",
            info="The initial instructions that define the agent's behavior and capabilities",
            value="You are Subagent1, a specialized agent for sub-level processing and specialized tasks.",
            advanced=False,
        ),
        IntInput(
            name="max_thinking_steps",
            display_name="Maximum Thinking Steps",
            info="Maximum number of thinking iterations the agent can perform",
            value=10,
            advanced=True,
        ),
        BoolInput(
            name="preprocessing_enabled",
            display_name="Pre-processing",
            info="Enable preprocessing of input data",
            value=True,
            advanced=True,
        ),
        BoolInput(
            name="postprocessing_enabled",
            display_name="Post-processing",
            info="Enable postprocessing of output data",
            value=True,
            advanced=True,
        ),
        DropdownInput(
            name="llm_provider",
            display_name="LLM Provider",
            info="The language model provider to use",
            options=["OpenAI", "Anthropic", "Google", "Azure"],
            value="OpenAI",
            advanced=True,
        ),
        DropdownInput(
            name="base_model",
            display_name="Base Model",
            info="The base language model to use for standard operations",
            options=["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "claude-3-sonnet", "claude-3-haiku"],
            value="gpt-4o-mini",
            advanced=True,
        ),
        DropdownInput(
            name="advanced_model",
            display_name="Advanced Model",
            info="The advanced language model to use for complex reasoning",
            options=["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "claude-3-sonnet", "claude-3-haiku"],
            value="gpt-4o",
            advanced=True,
        ),
        MessageTextInput(
            name="input_value",
            display_name="Message",
            info="The message or task to send to the Subagent1.",
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

    # Fixed agent ID for this specific agent
    AGENT_ID = "97521a59-b572-4634-b68e-1c7f2da637aa"

    async def update_build_config(self, build_config: Dict, field_value: Any, field_name: str | None = None) -> Dict:
        """Update build configuration with real agent data from API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:7860/api/v1/sap/ariba_agents",
                    timeout=10.0,
                )
                response.raise_for_status()
                agents_data = response.json()

                # Find this specific agent's data
                agent_data = None
                for agent in agents_data:
                    if agent.get("id") == self.AGENT_ID:
                        agent_data = agent
                        break

                if agent_data:
                    # Map PAB model names to UI model names
                    model_mapping = {
                        "PAB_GPT4o": "gpt-4o",
                        "PAB_GPT4o_mini": "gpt-4o-mini",
                        "PAB_GPT35_turbo": "gpt-3.5-turbo",
                        "PAB_Claude3_sonnet": "claude-3-sonnet",
                        "PAB_Claude3_haiku": "claude-3-haiku",
                    }

                    # Update build config with real agent data
                    if "agent_name" in build_config:
                        build_config["agent_name"]["value"] = agent_data.get("name", "Subagent1")
                    
                    if "expertise" in build_config:
                        build_config["expertise"]["value"] = agent_data.get("expertIn", "Sub-level processing and specialized tasks")
                    
                    if "initial_instructions" in build_config:
                        build_config["initial_instructions"]["value"] = agent_data.get("initialInstructions", "You are Subagent1, a specialized agent for sub-level processing and specialized tasks.")
                    
                    if "max_thinking_steps" in build_config:
                        build_config["max_thinking_steps"]["value"] = agent_data.get("iterations", 10)
                    
                    if "preprocessing_enabled" in build_config:
                        build_config["preprocessing_enabled"]["value"] = agent_data.get("preprocessingEnabled", True)
                    
                    if "postprocessing_enabled" in build_config:
                        build_config["postprocessing_enabled"]["value"] = agent_data.get("postprocessingEnabled", True)
                    
                    if "base_model" in build_config:
                        base_model_pab = agent_data.get("baseModel", "PAB_GPT4o_mini")
                        build_config["base_model"]["value"] = model_mapping.get(base_model_pab, "gpt-4o-mini")
                    
                    if "advanced_model" in build_config:
                        advanced_model_pab = agent_data.get("advancedModel", "PAB_GPT4o")
                        build_config["advanced_model"]["value"] = model_mapping.get(advanced_model_pab, "gpt-4o")

        except Exception as e:
            # If API call fails, keep default values
            pass

        return build_config

    async def message_response(self) -> Message:
        """Execute the Subagent1 and return the response as a Message."""
        if not self.input_value:
            return Message(
                text="Please provide a message or task for the Subagent1 to execute.",
                sender="Subagent1",
                sender_name="Subagent1",
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
                    sender="Subagent1",
                    sender_name="Subagent1",
                )

        except httpx.HTTPError as e:
            error_msg = f"HTTP error occurred: {e!s}"
            return Message(
                text=error_msg,
                sender="Subagent1",
                sender_name="Subagent1",
            )
        except Exception as e:
            error_msg = f"Error executing Subagent1: {e!s}"
            return Message(
                text=error_msg,
                sender="Subagent1",
                sender_name="Subagent1",
            )
