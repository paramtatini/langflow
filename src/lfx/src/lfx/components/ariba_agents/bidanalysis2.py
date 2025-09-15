from typing import Any

import httpx

from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, MultilineInput, Output
from lfx.schema.message import Message


class BidAnalysis2Component(Component):
    display_name: str = "BidAnalysis2"
    description: str = "BidAnalysis2 - A specialized Ariba agent for advanced bid analysis and evaluation tasks."
    icon: str = "bot"
    name: str = "BidAnalysis2"

    inputs = [
        MessageTextInput(
            name="input_value",
            display_name="Message",
            info="The message or task to send to the BidAnalysis2 agent.",
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
    AGENT_ID = "4b5bddf6-a656-4a47-9f76-827aefbeec74"

    async def message_response(self) -> Message:
        """Execute the BidAnalysis2 agent and return the response as a Message."""
        if not self.input_value:
            return Message(
                text="Please provide a message or task for the BidAnalysis2 agent to execute.",
                sender="BidAnalysis2",
                sender_name="BidAnalysis2",
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
                    sender="BidAnalysis2",
                    sender_name="BidAnalysis2",
                )

        except httpx.HTTPError as e:
            error_msg = f"HTTP error occurred: {e!s}"
            return Message(
                text=error_msg,
                sender="BidAnalysis2",
                sender_name="BidAnalysis2",
            )
        except Exception as e:
            error_msg = f"Error executing BidAnalysis2 agent: {e!s}"
            return Message(
                text=error_msg,
                sender="BidAnalysis2",
                sender_name="BidAnalysis2",
            )
