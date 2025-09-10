import json
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from lfx.log.logger import logger
from pydantic import BaseModel, ValidationError

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.deps import get_variable_service

router = APIRouter(prefix="/sap", tags=["SAP"])


class PABServiceKey(BaseModel):
    service_urls: dict = {}
    uaa: dict

    class Config:
        extra = "allow"  # Allow additional fields


class PABCredentials(BaseModel):
    client_id: str
    client_secret: str
    token_url: str
    service_url: str

    @classmethod
    def from_service_key(cls, service_key: PABServiceKey) -> "PABCredentials":
        """Convert SAP service key format to internal credentials format."""
        uaa = service_key.uaa

        # Extract agent API URL from service_urls
        service_url = None
        if service_key.service_urls and "agent_api_url" in service_key.service_urls:
            service_url = service_key.service_urls["agent_api_url"]

        if not service_url:
            raise ValueError("No agent_api_url found in service_urls")

        # Construct token URL using UAA URL + /oauth/token
        token_url = f"{uaa['url'].rstrip('/')}/oauth/token"

        return cls(
            client_id=uaa["clientid"],
            client_secret=uaa["clientsecret"],
            token_url=token_url,
            service_url=service_url.rstrip("/"),
        )


class PABAgent(BaseModel):
    ID: str
    name: str
    type: str
    safetyCheck: bool
    expertIn: str
    initialInstructions: str
    iterations: int
    baseModel: str
    advancedModel: str
    preprocessingEnabled: bool
    postprocessingEnabled: bool
    createdAt: str
    modifiedAt: str


class SavePABCredentialsResponse(BaseModel):
    success: bool
    message: str
    agents: list[PABAgent] = []


async def get_oauth_token(credentials: PABCredentials) -> str:
    """Get OAuth token from SAP authentication service."""
    async with httpx.AsyncClient() as client:
        # Don't URL encode - httpx handles this automatically for form data
        form_data = {
            "grant_type": "client_credentials",
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        # Enhanced debug information
        logger.info("=== OAuth Token Request Debug Info ===")
        logger.info(f"Token URL: {credentials.token_url}")
        logger.info(
            f"Client ID: {credentials.client_id[:10]}...{credentials.client_id[-4:] if len(credentials.client_id) > 14 else ''}"
        )
        logger.info(
            f"Client Secret: {'*' * (len(credentials.client_secret) - 4)}{credentials.client_secret[-4:] if len(credentials.client_secret) > 4 else '****'}"
        )
        logger.info(f"Grant Type: {form_data['grant_type']}")
        logger.info(f"Request Headers: {headers}")
        logger.info(f"Service URL (for reference): {credentials.service_url}")
        logger.info("=====================================")

        try:
            logger.info("Sending OAuth token request...")
            response = await client.post(credentials.token_url, data=form_data, headers=headers, timeout=30.0)

            logger.info(f"OAuth response status: {response.status_code}")
            logger.info(f"OAuth response headers: {dict(response.headers)}")

            if response.status_code != 200:
                response_text = response.text
                logger.error(f"OAuth error response body: {response_text}")
                logger.error(f"OAuth error response headers: {dict(response.headers)}")
                raise HTTPException(
                    status_code=400, detail=f"OAuth failed with status {response.status_code}: {response_text}"
                )

            response.raise_for_status()

            token_data = response.json()
            logger.info("Successfully obtained OAuth token")
            logger.info(f"Token response keys: {list(token_data.keys())}")

            # Log token info (without exposing the actual token)
            if "access_token" in token_data:
                token = token_data["access_token"]
                logger.info(f"Access token length: {len(token)} characters")
                logger.info(f"Access token preview: {token[:20]}...{token[-10:] if len(token) > 30 else ''}")

                # Log additional token metadata if present
                if "token_type" in token_data:
                    logger.info(f"Token type: {token_data['token_type']}")
                if "expires_in" in token_data:
                    logger.info(f"Token expires in: {token_data['expires_in']} seconds")
                if "scope" in token_data:
                    logger.info(f"Token scope: {token_data['scope']}")

                return token
            logger.error(f"Missing access_token in response. Available keys: {list(token_data.keys())}")
            raise HTTPException(status_code=400, detail="Invalid token response format - missing access_token")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during OAuth: {e!s}")
            logger.error(f"Request URL: {credentials.token_url}")
            logger.error("Request method: POST")
            raise HTTPException(status_code=400, detail=f"Failed to get OAuth token: {e!s}")
        except KeyError as e:
            logger.error(f"Missing key in token response: {e!s}")
            logger.error(f"Full response data: {token_data}")
            raise HTTPException(status_code=400, detail="Invalid token response format - missing access_token")
        except Exception as e:
            logger.error(f"Unexpected error during OAuth: {e!s}")
            logger.error(f"Error type: {type(e).__name__}")
            raise HTTPException(status_code=500, detail=f"Unexpected OAuth error: {e!s}")


async def fetch_pab_agents(credentials: PABCredentials, access_token: str) -> list[PABAgent]:
    """Fetch PAB agents from SAP service."""
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }

        try:
            # Use the agent_api_url directly and append /api/v1/Agents
            service_url = credentials.service_url.rstrip("/")
            agents_url = f"{service_url}/api/v1/Agents"

            logger.info(f"Fetching agents from: {agents_url}")

            response = await client.get(agents_url, headers=headers, timeout=30.0)

            logger.info(f"Agents API response status: {response.status_code}")
            logger.info(f"Agents API response headers: {dict(response.headers)}")

            if response.status_code != 200:
                response_text = response.text
                logger.error(f"Agents API error response: {response_text}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to fetch agents. Status: {response.status_code}, Response: {response_text}",
                )

            response.raise_for_status()

            response_data = response.json()
            logger.info(f"Response data type: {type(response_data)}")

            # Handle different response formats
            agents_data = []
            if isinstance(response_data, list):
                # Direct array response
                agents_data = response_data
                logger.info(f"Using direct array response with {len(agents_data)} agents")
            elif isinstance(response_data, dict):
                logger.info(f"Response keys: {list(response_data.keys())}")
                # Try different wrapper properties
                for key in ["value", "agents", "data", "results", "items", "content"]:
                    if key in response_data and isinstance(response_data[key], list):
                        agents_data = response_data[key]
                        logger.info(f"Using response.{key} with {len(agents_data)} agents")
                        break

                if not agents_data and response_data:
                    # Single agent object, wrap in array
                    agents_data = [response_data]
                    logger.info("Wrapping single object in array")
            else:
                logger.error(f"Unexpected response format: {type(response_data)}")
                raise HTTPException(status_code=400, detail=f"Unexpected response format: {type(response_data)}")

            # Parse agents with better error handling
            parsed_agents = []
            for i, agent_data in enumerate(agents_data):
                try:
                    if isinstance(agent_data, dict):
                        parsed_agent = PABAgent(**agent_data)
                        parsed_agents.append(parsed_agent)
                    else:
                        logger.warning(f"Agent {i} is not a dict: {type(agent_data)}, skipping")
                except Exception as e:
                    logger.warning(f"Failed to parse agent {i}: {e!s}, data: {agent_data}")
                    continue

            logger.info(f"Successfully parsed {len(parsed_agents)} agents out of {len(agents_data)} total")
            return parsed_agents

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching agents: {e!s}")
            raise HTTPException(status_code=400, detail=f"Unexpected error fetching agents: {e!s}")


@router.post("/pab/credentials", response_model=SavePABCredentialsResponse)
async def save_pab_credentials(
    request_data: dict[str, Any],
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Save PAB credentials and fetch available agents."""
    try:
        logger.info("=== PAB CREDENTIALS SAVE REQUEST STARTED ===")
        logger.info("Received PAB credentials save request")
        logger.info(f"Request data keys: {list(request_data.keys())}")
        logger.info(f"Request data (first 200 chars): {str(request_data)[:200]}...")
        logger.info(f"Current user ID: {current_user.id}")
        logger.info("===============================================")
    except Exception as e:
        logger.error(f"Error in initial logging: {e!s}")
        raise HTTPException(status_code=500, detail=f"Error in initial logging: {e!s}")

    try:
        logger.info("Starting credentials parsing...")

        # Try to parse as service key first, then fall back to direct credentials
        credentials = None
        try:
            logger.info("Attempting to parse as SAP service key format...")
            # First try to parse as SAP service key format
            service_key = PABServiceKey(**request_data)
            logger.info("Service key model created successfully, converting to credentials...")
            credentials = PABCredentials.from_service_key(service_key)
            logger.info(
                f"Service key validated and converted successfully: client_id={credentials.client_id[:10]}..., token_url={credentials.token_url}, service_url={credentials.service_url}"
            )
        except (ValidationError, ValueError) as service_key_error:
            logger.info(f"Service key validation failed: {service_key_error!s}, trying direct credentials format")
            try:
                logger.info("Attempting to parse as direct credentials format...")
                # Fall back to direct credentials format
                credentials = PABCredentials(**request_data)
                logger.info(
                    f"Direct credentials validated successfully: client_id={credentials.client_id[:10]}..., token_url={credentials.token_url}, service_url={credentials.service_url}"
                )
            except ValidationError as cred_error:
                logger.error(
                    f"Both service key and direct credentials validation failed. Service key error: {service_key_error!s}, Credentials error: {cred_error!s}"
                )
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid format. Expected either SAP service key format with 'service_urls' and 'uaa' objects, or direct credentials with 'client_id', 'client_secret', 'token_url', and 'service_url'. Errors: Service key: {service_key_error!s}, Direct: {cred_error!s}",
                )

        if not credentials:
            logger.error("Credentials parsing failed - credentials is None")
            raise HTTPException(status_code=422, detail="Failed to parse credentials")

        logger.info("Credentials parsing completed successfully")

    except HTTPException as http_exc:
        logger.error(f"HTTP exception during parsing: {http_exc!s}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing request: {e!s}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error parsing request: {e!s}")

    variable_service = get_variable_service()

    try:
        # Get OAuth token with enhanced debug info
        logger.info("=== Starting OAuth Token Process ===")
        logger.info("Parsed credentials summary:")
        logger.info(
            f"  - Client ID: {credentials.client_id[:10]}...{credentials.client_id[-4:] if len(credentials.client_id) > 14 else ''}"
        )
        logger.info(f"  - Token URL: {credentials.token_url}")
        logger.info(f"  - Service URL: {credentials.service_url}")
        logger.info("====================================")

        access_token = await get_oauth_token(credentials)
        logger.info("OAuth token obtained successfully - proceeding to fetch agents")

        # Fetch agents
        agents = await fetch_pab_agents(credentials, access_token)
        logger.info(f"Successfully fetched {len(agents)} agents from PAB service")

        # Save credentials as encrypted variable
        credentials_json = credentials.model_dump_json()
        logger.info("=== Saving Credentials to Database ===")
        logger.info(f"Credentials JSON length: {len(credentials_json)} characters")
        logger.info("Credentials will be saved as encrypted variable 'SAP_PAB_CREDENTIALS'")

        # Check if PAB credentials variable already exists
        existing_variables = await variable_service.list_variables(user_id=current_user.id, session=session)

        if "SAP_PAB_CREDENTIALS" in existing_variables:
            # Update existing variable
            logger.info("Updating existing SAP_PAB_CREDENTIALS variable")
            variable_id = None
            all_vars = await variable_service.get_all(user_id=current_user.id, session=session)
            for var in all_vars:
                if var.name == "SAP_PAB_CREDENTIALS":
                    variable_id = var.id
                    logger.info(f"Found existing credentials variable with ID: {variable_id}")
                    break

            if variable_id:
                from langflow.services.database.models.variable.model import VariableUpdate

                await variable_service.update_variable_fields(
                    user_id=current_user.id,
                    variable_id=variable_id,
                    variable=VariableUpdate(id=variable_id, value=credentials_json),
                    session=session,
                )
                logger.info("Successfully updated existing credentials variable")
            else:
                logger.warning("SAP_PAB_CREDENTIALS found in list but variable ID not found")
        else:
            # Create new variable
            logger.info("Creating new SAP_PAB_CREDENTIALS variable")
            await variable_service.create_variable(
                user_id=current_user.id,
                name="SAP_PAB_CREDENTIALS",
                value=credentials_json,
                default_fields=[],
                type_="Credential",
                session=session,
            )
            logger.info("Successfully created new credentials variable")

        # Save agents data as well
        agents_json = json.dumps([agent.model_dump() for agent in agents])
        logger.info("=== Saving Agents to Database ===")
        logger.info(f"Agents JSON length: {len(agents_json)} characters")
        logger.info(f"Number of agents to save: {len(agents)}")
        logger.info("Agents will be saved as variable 'SAP_PAB_AGENTS'")

        if "SAP_PAB_AGENTS" in existing_variables:
            # Update existing agents variable
            logger.info("Updating existing SAP_PAB_AGENTS variable")
            variable_id = None
            all_vars = await variable_service.get_all(user_id=current_user.id, session=session)
            for var in all_vars:
                if var.name == "SAP_PAB_AGENTS":
                    variable_id = var.id
                    logger.info(f"Found existing agents variable with ID: {variable_id}")
                    break

            if variable_id:
                from langflow.services.database.models.variable.model import VariableUpdate

                await variable_service.update_variable_fields(
                    user_id=current_user.id,
                    variable_id=variable_id,
                    variable=VariableUpdate(id=variable_id, value=agents_json),
                    session=session,
                )
                logger.info("Successfully updated existing agents variable")
            else:
                logger.warning("SAP_PAB_AGENTS found in list but variable ID not found")
        else:
            # Create new agents variable
            logger.info("Creating new SAP_PAB_AGENTS variable")
            await variable_service.create_variable(
                user_id=current_user.id,
                name="SAP_PAB_AGENTS",
                value=agents_json,
                default_fields=[],
                type_="Generic",
                session=session,
            )
            logger.info("Successfully created new agents variable")

        logger.info("=== PAB Credentials Save Process Complete ===")
        logger.info(f"Final result: {len(agents)} agents saved successfully")
        logger.info("============================================")

        return SavePABCredentialsResponse(
            success=True, message=f"Successfully saved credentials and fetched {len(agents)} agents", agents=agents
        )

    except HTTPException as http_exc:
        logger.error(f"HTTP exception in save_pab_credentials: {http_exc!s}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in save_pab_credentials: {e!s}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback

        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


@router.get("/pab/credentials")
async def get_pab_credentials(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Get stored PAB credentials for editing."""
    variable_service = get_variable_service()
    
    try:
        # Get credentials from stored variable
        all_vars = await variable_service.get_all(user_id=current_user.id, session=session)
        credentials_var = None
        
        for var in all_vars:
            if var.name == "SAP_PAB_CREDENTIALS":
                credentials_var = var
                break
        
        if not credentials_var or not credentials_var.value:
            raise HTTPException(status_code=404, detail="PAB credentials not found.")
        
        # Parse and return credentials (without exposing sensitive data)
        credentials_data = json.loads(credentials_var.value)
        credentials = PABCredentials(**credentials_data)
        
        # Return credentials in the original service key format for editing
        return {
            "service_urls": {
                "agent_api_url": credentials.service_url
            },
            "uaa": {
                "clientid": credentials.client_id,
                "clientsecret": credentials.client_secret,
                "url": credentials.token_url.replace("/oauth/token", "")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving credentials: {e!s}")


@router.get("/pab/agents", response_model=list[PABAgent])
async def get_pab_agents(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Get cached PAB agents."""
    variable_service = get_variable_service()

    try:
        # Get agents from stored variable
        all_vars = await variable_service.get_all(user_id=current_user.id, session=session)
        agents_var = None

        for var in all_vars:
            if var.name == "SAP_PAB_AGENTS":
                agents_var = var
                break

        if not agents_var:
            return []

        # Parse agents data
        agents_data = json.loads(agents_var.value)
        return [PABAgent(**agent) for agent in agents_data]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving agents: {e!s}")


@router.post("/pab/refresh-agents", response_model=list[PABAgent])
async def refresh_pab_agents(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Refresh PAB agents from SAP service."""
    variable_service = get_variable_service()

    try:
        # Get stored credentials
        all_vars = await variable_service.get_all(user_id=current_user.id, session=session)
        credentials_var = None

        for var in all_vars:
            if var.name == "SAP_PAB_CREDENTIALS":
                credentials_var = var
                break

        if not credentials_var or not credentials_var.value:
            raise HTTPException(status_code=404, detail="PAB credentials not found. Please save credentials first.")

        # Parse credentials
        credentials_data = json.loads(credentials_var.value)
        credentials = PABCredentials(**credentials_data)

        # Get OAuth token and fetch agents
        access_token = await get_oauth_token(credentials)
        agents = await fetch_pab_agents(credentials, access_token)

        # Update agents variable
        agents_json = json.dumps([agent.model_dump() for agent in agents])

        agents_var = None
        for var in all_vars:
            if var.name == "SAP_PAB_AGENTS":
                agents_var = var
                break

        if agents_var:
            from langflow.services.database.models.variable.model import VariableUpdate

            await variable_service.update_variable_fields(
                user_id=current_user.id,
                variable_id=agents_var.id,
                variable=VariableUpdate(id=agents_var.id, value=agents_json),
                session=session,
            )
        else:
            await variable_service.create_variable(
                user_id=current_user.id,
                name="SAP_PAB_AGENTS",
                value=agents_json,
                default_fields=[],
                type_="Generic",
                session=session,
            )

        return agents

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing agents: {e!s}")
