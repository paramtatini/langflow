from typing import Any
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel

from lfx.custom.custom_component.component import Component
from lfx.io import Output, StrInput
from lfx.schema.message import Message


class PABCredentials(BaseModel):
    """PAB credentials model supporting both service key and direct format."""
    client_id: str
    client_secret: str
    token_url: str
    agent_api_url: str


class OAuthTokenComponent(Component):
    display_name: str = "OAuth Token"
    description: str = (
        "Retrieve OAuth access token from SAP XSUAA service using PAB credentials. "
        "This component fetches the bearer token required for PAB API calls."
    )
    icon: str = "key"
    name: str = "OAuthToken"

    inputs = [
        StrInput(
            name="credentials_source",
            display_name="Credentials Source",
            info="Source of PAB credentials (e.g., 'database', 'environment', or JSON string)",
            value="database",
            advanced=False,
        ),
    ]

    outputs = [
        Output(display_name="Access Token", name="access_token", method="get_access_token"),
        Output(display_name="Token Response", name="token_response", method="message_response"),
    ]

    async def get_stored_credentials(self) -> PABCredentials | None:
        """Get stored PAB credentials from database or environment."""
        try:
            # Try to get from Langflow API first
            try:
                import httpx
                
                # Get credentials from the SAP API endpoint
                async with httpx.AsyncClient() as client:
                    # This would need proper authentication in a real scenario
                    # For now, we'll try to get from environment or return None
                    pass
            except Exception:
                pass

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

    async def get_oauth_token(self, credentials: PABCredentials) -> dict[str, Any]:
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
            return token_data

    async def get_access_token(self) -> str:
        """Get the access token as a string."""
        try:
            # Get stored credentials
            credentials = await self.get_stored_credentials()
            if not credentials:
                raise ValueError("PAB credentials not found. Please configure your SAP PAB credentials in Settings > SAP AI Credentials.")

            # Get OAuth token
            token_data = await self.get_oauth_token(credentials)
            return token_data.get("access_token", "")

        except Exception as e:
            raise ValueError(f"Error retrieving OAuth token: {e!s}")

    async def message_response(self) -> Message:
        """Get OAuth token and return detailed response as a Message."""
        try:
            # Get stored credentials
            credentials = await self.get_stored_credentials()
            if not credentials:
                return Message(
                    text="PAB credentials not found. Please configure your SAP PAB credentials in Settings > SAP AI Credentials.",
                    sender="OAuth Token",
                    sender_name="OAuth Token Component",
                )

            # Get OAuth token
            token_data = await self.get_oauth_token(credentials)
            
            # Create response message with token details
            access_token = token_data.get("access_token", "")
            expires_in = token_data.get("expires_in", 0)
            token_type = token_data.get("token_type", "Bearer")
            
            response_text = f"""OAuth Token Retrieved Successfully:
- Token Type: {token_type}
- Expires In: {expires_in} seconds
- Token URL: {credentials.token_url}
- Agent API URL: {credentials.agent_api_url}
- Access Token: {access_token[:20]}...{access_token[-10:] if len(access_token) > 30 else access_token}"""

            return Message(
                text=response_text,
                sender="OAuth Token",
                sender_name="OAuth Token Component",
            )

        except httpx.HTTPError as e:
            error_msg = f"HTTP error occurred while retrieving OAuth token: {e!s}"
            return Message(
                text=error_msg,
                sender="OAuth Token",
                sender_name="OAuth Token Component",
            )
        except Exception as e:
            error_msg = f"Error retrieving OAuth token: {e!s}"
            return Message(
                text=error_msg,
                sender="OAuth Token",
                sender_name="OAuth Token Component",
            )
