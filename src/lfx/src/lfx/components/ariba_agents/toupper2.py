from typing import Any

import httpx

from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, MultilineInput, Output
from lfx.schema.message import Message


class ToUpper2Component(Component):
    display_name: str = "toUpper2"
    description: str = "toUpper2 - A specialized Ariba agent for text transformation and uppercase conversion tasks."
    icon: str = "bot"
    name: str = "ToUpper2"

    inputs = [
        MessageTextInput(
            name="input_value",
            display_name="Message",
            info="The message or task to send to the toUpper2 agent.",
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
    AGENT_ID = "0c9a6960-4fa4-4f54-88b9-8eeec573e268"

    async def message_response(self) -> Message:
        """Execute the toUpper2 agent and return the response as a Message."""
        if not self.input_value:
            return Message(
                text="Please provide a message or task for the toUpper2 agent to execute.",
                sender="toUpper2",
                sender_name="toUpper2",
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
                    sender="toUpper2",
                    sender_name="toUpper2",
                )

        except httpx.HTTPError as e:
            error_msg = f"HTTP error occurred: {e!s}"
            return Message(
                text=error_msg,
                sender="toUpper2",
                sender_name="toUpper2",
            )
        except Exception as e:
            error_msg = f"Error executing toUpper2 agent: {e!s}"
            return Message(
                text=error_msg,
                sender="toUpper2",
                sender_name="toUpper2",
            )
