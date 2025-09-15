from typing import Any

import httpx

from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, MultilineInput, Output
from lfx.schema.message import Message


class EnhancedProcurementAgentComponent(Component):
    display_name: str = "Enhanced Procurement Agent"
    description: str = "Enhanced Procurement Agent - A specialized Ariba agent for advanced procurement processes and optimization."
    icon: str = "bot"
    name: str = "EnhancedProcurementAgent"

    inputs = [
        MessageTextInput(
            name="input_value",
            display_name="Message",
            info="The message or task to send to the Enhanced Procurement Agent.",
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
    AGENT_ID = "bdb207f1-54bb-40e4-bce0-d2ef6ecd41bf"

    async def message_response(self) -> Message:
        """Execute the Enhanced Procurement Agent and return the response as a Message."""
        if not self.input_value:
            return Message(
                text="Please provide a message or task for the Enhanced Procurement Agent to execute.",
                sender="Enhanced Procurement Agent",
                sender_name="Enhanced Procurement Agent",
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
                    sender="Enhanced Procurement Agent",
                    sender_name="Enhanced Procurement Agent",
                )

        except httpx.HTTPError as e:
            error_msg = f"HTTP error occurred: {e!s}"
            return Message(
                text=error_msg,
                sender="Enhanced Procurement Agent",
                sender_name="Enhanced Procurement Agent",
            )
        except Exception as e:
            error_msg = f"Error executing Enhanced Procurement Agent: {e!s}"
            return Message(
                text=error_msg,
                sender="Enhanced Procurement Agent",
                sender_name="Enhanced Procurement Agent",
            )
