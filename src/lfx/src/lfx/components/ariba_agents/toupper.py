from typing import Any

import httpx

from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, MultilineInput, Output
from lfx.schema.message import Message


class ToUpperComponent(Component):
    display_name: str = "toUpper"
    description: str = "toUpper - A specialized Ariba agent for text transformation and uppercase conversion tasks."
    icon: str = "bot"
    name: str = "ToUpper"

    inputs = [
        MessageTextInput(
            name="input_value",
            display_name="Message",
            info="The message or task to send to the toUpper agent.",
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
    AGENT_ID = "4ed3f502-4d52-49e4-a343-87ef272e48e7"

    async def message_response(self) -> Message:
        """Execute the toUpper agent and return the response as a Message."""
        if not self.input_value:
            return Message(
                text="Please provide a message or task for the toUpper agent to execute.",
                sender="toUpper",
                sender_name="toUpper",
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
                    sender="toUpper",
                    sender_name="toUpper",
                )

        except httpx.HTTPError as e:
            error_msg = f"HTTP error occurred: {e!s}"
            return Message(
                text=error_msg,
                sender="toUpper",
                sender_name="toUpper",
            )
        except Exception as e:
            error_msg = f"Error executing toUpper agent: {e!s}"
            return Message(
                text=error_msg,
                sender="toUpper",
                sender_name="toUpper",
            )
