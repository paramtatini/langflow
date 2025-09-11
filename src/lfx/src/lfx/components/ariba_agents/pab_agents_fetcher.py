from typing import Any

import httpx
from pydantic import BaseModel

from lfx.custom.custom_component.component import Component
from lfx.io import BoolInput, Output, StrInput
from lfx.schema.message import Message


class PABCredentials(BaseModel):
    """PAB credentials model supporting both service key and direct format."""
    client_id: str
    client_secret: str
    token_url: str
    agent_api_url: str


class PABAgentsFetcherComponent(Component):
    display_name: str = "PAB Agents Fetcher"
    description: str = (
        "Fetch available PAB agents from SAP Project Agent Builder service. "
        "This component retrieves the list of virtual agents configured in PAB."
    )
    icon: str = "users"
    name: str = "PABAgentsFetcher"

    inputs = [
        BoolInput(
            name="auto_fetch",
            display_name="Auto Fetch on Load",
            info="Automatically fetch agents when component is loaded",
            value=True,
            advanced=False,
        ),
        StrInput(
            name="access_token",
            display_name="Access Token",
            info="OAuth access token for PAB API authentication (optional if using stored credentials)",
            value="",
            advanced=True,
        ),
    ]

    outputs = [
        Output(display_name="Agents List", name="agents_list", method="get_agents_list"),
        Output(display_name="Agents Response", name="agents_response", method="message_response"),
    ]

    async def get_stored_credentials(self) -> PABCredentials | None:
        """Get stored PAB credentials from database or environment."""
        try:
            # Try to get from global variables (for backward compatibility)
            import json
            import os

            try:
                from langflow.services.variable.utils import get_variable_value
            except ImportError:
                # Fallback for LFX environment
                async def get_variable_value(name: str, user_id: str = None):
                    return os.getenv(name)

            # Try to get the credentials from the global variable
            credentials_json = await get_variable_value(
                name="SAP_PAB_CREDENTIALS", user_id=getattr(self, "user_id", None)
            )

            if credentials_json:
                credentials_data = json.loads(credentials_json)
                
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
            # Log the error for debugging
            print(f"Error getting PAB credentials: {e!s}")
            return None

    async def get_oauth_token(self, credentials: PABCredentials) -> str:
        """Get OAuth token from SAP XSUAA service."""
        from urllib.parse import urlencode
        
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

    async def fetch_pab_agents(self, agent_api_url: str, access_token: str) -> list[dict[str, Any]]:
        """Fetch PAB agents from the API using the access token."""
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }

            # Make the API request to get agents
            # Based on PDF documentation: GET /api/v1/Agents
            agents_url = f"{agent_api_url}/api/v1/Agents"
            
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

    async def get_agents_list(self) -> list[dict[str, Any]]:
        """Get the list of PAB agents."""
        try:
            # Use provided access token if available
            access_token = self.access_token if hasattr(self, "access_token") and self.access_token else None
            
            # Get stored credentials
            credentials = await self.get_stored_credentials()
            if not credentials:
                raise ValueError("PAB credentials not found. Please configure your SAP PAB credentials in Settings > SAP AI Credentials.")

            # Get access token if not provided
            if not access_token:
                access_token = await self.get_oauth_token(credentials)

            if not access_token:
                raise ValueError("Failed to obtain access token")

            # Fetch agents from PAB API
            agents = await self.fetch_pab_agents(credentials.agent_api_url, access_token)
            
            # Store agents in global variables for other components to use
            try:
                import json
                
                try:
                    from langflow.services.variable.utils import update_variable_value
                except ImportError:
                    # Fallback for LFX environment
                    async def update_variable_value(name: str, value: str, user_id: str = None):
                        print(f"Warning: Cannot update variable {name} in LFX environment")
                        return False

                # Update the stored agents list
                await update_variable_value(
                    name="SAP_PAB_AGENTS", 
                    value=json.dumps(agents), 
                    user_id=getattr(self, "user_id", None)
                )
            except Exception as e:
                print(f"Warning: Could not update agents list: {e}")

            return agents

        except Exception as e:
            raise ValueError(f"Error fetching PAB agents: {e!s}")

    async def message_response(self) -> Message:
        """Fetch PAB agents and return detailed response as a Message."""
        try:
            # Get agents list
            agents = await self.get_agents_list()
            
            if not agents:
                return Message(
                    text="No PAB agents found. The agents list is empty.",
                    sender="PAB Agents Fetcher",
                    sender_name="PAB Agents Fetcher Component",
                )

            # Create response message with agents summary
            agents_count = len(agents)
            agents_summary = []
            
            for agent in agents[:5]:  # Show first 5 agents
                agent_id = agent.get("ID", "Unknown ID")
                agent_name = agent.get("name", "Unknown Name")
                agent_type = agent.get("type", "Unknown Type")
                expert_in = agent.get("expertIn", "No expertise defined")
                
                agents_summary.append(f"• {agent_name} (ID: {agent_id})")
                agents_summary.append(f"  Type: {agent_type}")
                agents_summary.append(f"  Expert in: {expert_in[:100]}{'...' if len(expert_in) > 100 else ''}")
                agents_summary.append("")

            more_agents = ""
            if agents_count > 5:
                more_agents = f"\n... and {agents_count - 5} more agents"

            response_text = f"""PAB Agents Retrieved Successfully:
Total Agents Found: {agents_count}

Agent Details:
{chr(10).join(agents_summary)}{more_agents}

All agents have been stored and are available for use in other components."""

            return Message(
                text=response_text,
                sender="PAB Agents Fetcher",
                sender_name="PAB Agents Fetcher Component",
            )

        except httpx.HTTPError as e:
            error_msg = f"HTTP error occurred while fetching PAB agents: {e!s}"
            return Message(
                text=error_msg,
                sender="PAB Agents Fetcher",
                sender_name="PAB Agents Fetcher Component",
            )
        except Exception as e:
            error_msg = f"Error fetching PAB agents: {e!s}"
            return Message(
                text=error_msg,
                sender="PAB Agents Fetcher",
                sender_name="PAB Agents Fetcher Component",
            )

    async def update_build_config(self, build_config, field_value: Any, field_name: str | None = None):
        """Update build configuration, particularly for auto-fetching agents."""
        if field_name == "auto_fetch" and field_value:
            # Auto-fetch agents when component is loaded
            try:
                await self.get_agents_list()
            except Exception as e:
                print(f"Warning: Could not auto-fetch agents: {e}")

        return build_config
