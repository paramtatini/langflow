import logging
from typing import Any
import httpx
import asyncio
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from langflow.api.utils import CurrentActiveUser, DbSession
from langflow.services.database.models.sap.crud import (
    create_sap_credentials,
    get_sap_credentials_by_user_id,
    update_sap_credentials,
)
from langflow.services.database.models.sap.model import SAPCredentialsCreate, SAPCredentialsUpdate

# Set up logging for SAP API
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sap", tags=["SAP"])


class SaveCredentialsResponse(BaseModel):
    success: bool
    message: str


async def get_oauth_token(credentials_data: dict) -> str:
    """Get OAuth token using PAB credentials."""
    try:
        uaa_info = credentials_data.get("uaa", {})
        client_id = uaa_info.get("clientid")
        client_secret = uaa_info.get("clientsecret")
        uaa_url = uaa_info.get("url")
        
        if not all([client_id, client_secret, uaa_url]):
            raise ValueError("Missing required OAuth credentials (clientid, clientsecret, url)")
        
        # Construct OAuth token URL
        token_url = f"{uaa_url}/oauth/token"
        
        # Prepare OAuth request
        auth = (client_id, client_secret)
        data = {"grant_type": "client_credentials"}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(token_url, auth=auth, data=data, headers=headers)
            response.raise_for_status()
            
            token_data = response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                raise ValueError("No access token received from OAuth response")
                
            return access_token
            
    except Exception as e:
        logger.error(f"Failed to get OAuth token: {str(e)}")
        raise ValueError(f"OAuth token retrieval failed: {str(e)}")


async def fetch_pab_agents(credentials_data: dict, access_token: str) -> list[dict]:
    """Fetch PAB agents using credentials and OAuth token."""
    try:
        # Get agent API URL from credentials - handle both service key and direct formats
        agent_api_url = None
        
        # Check for service key format first
        if "service_urls" in credentials_data:
            service_urls = credentials_data["service_urls"]
            agent_api_url = service_urls.get("agent_api_url")
        else:
            # Check for direct format
            agent_api_url = credentials_data.get("agent_api_url")
        
        if not agent_api_url:
            raise ValueError("Missing agent_api_url in credentials")
        
        # Ensure URL ends with slash for proper concatenation
        if not agent_api_url.endswith('/'):
            agent_api_url += '/'
        
        # Construct agents endpoint URL
        agents_url = f"{agent_api_url}api/v1/Agents"
        
        # Prepare request headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Fetching agents from URL: {agents_url}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(agents_url, headers=headers)
            response.raise_for_status()
            
            agents_data = response.json()
            
            # Handle different response formats
            if isinstance(agents_data, dict):
                # If response is wrapped in an object, extract the agents array
                agents = agents_data.get("agents", agents_data.get("data", agents_data.get("value", [])))
            else:
                # If response is directly an array
                agents = agents_data
            
            logger.info(f"Successfully fetched {len(agents)} agents from PAB")
            return agents
            
    except Exception as e:
        logger.error(f"Failed to fetch PAB agents: {str(e)}")
        raise ValueError(f"Agent fetching failed: {str(e)}")


@router.post("/pab/credentials", response_model=SaveCredentialsResponse)
async def save_pab_credentials(
    request_data: dict[str, Any],
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Save PAB credentials and automatically fetch all Ariba agents."""
    try:
        logger.info(f"Saving PAB credentials for user: {current_user.id}")
        
        # First, save the credentials
        existing_credentials = await get_sap_credentials_by_user_id(session, current_user.id)
        
        if existing_credentials:
            # Update existing credentials
            credentials_update = SAPCredentialsUpdate(
                credentials_data=request_data,
                agents_data=None,  # Clear agents data when updating credentials
            )
            await update_sap_credentials(session, current_user.id, credentials_update)
            logger.info(f"Updated PAB credentials for user: {current_user.id}")
        else:
            # Create new credentials
            credentials_create = SAPCredentialsCreate(credentials_data=request_data, agents_data=None)
            await create_sap_credentials(session, current_user.id, credentials_create)
            logger.info(f"Created new PAB credentials for user: {current_user.id}")
        
        # Now automatically fetch and store all Ariba agents
        try:
            logger.info(f"Starting automatic agent fetch for user: {current_user.id}")
            
            # Get OAuth token
            access_token = await get_oauth_token(request_data)
            logger.info(f"Successfully obtained OAuth token for user: {current_user.id}")
            
            # Fetch agents from PAB
            agents = await fetch_pab_agents(request_data, access_token)
            logger.info(f"Successfully fetched {len(agents)} agents for user: {current_user.id}")
            
            # Store agents in database
            if agents:
                # Wrap agents list in a dictionary structure to match the database model
                agents_dict = {"agents": agents}
                credentials_update = SAPCredentialsUpdate(agents_data=agents_dict)
                await update_sap_credentials(session, current_user.id, credentials_update)
                logger.info(f"Successfully stored {len(agents)} agents for user: {current_user.id}")
                
                return SaveCredentialsResponse(
                    success=True, 
                    message=f"PAB credentials saved and {len(agents)} Ariba agents fetched successfully"
                )
            else:
                logger.warning(f"No agents found for user: {current_user.id}")
                return SaveCredentialsResponse(
                    success=True, 
                    message="PAB credentials saved successfully, but no agents were found"
                )
                
        except Exception as agent_error:
            # If agent fetching fails, still return success for credential saving
            logger.error(f"Failed to fetch agents for user {current_user.id}: {str(agent_error)}")
            return SaveCredentialsResponse(
                success=True, 
                message=f"PAB credentials saved successfully, but agent fetching failed: {str(agent_error)}"
            )

    except Exception as e:
        logger.error(f"Failed to save PAB credentials for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save credentials: {e!s}")


@router.get("/pab/credentials")
async def get_pab_credentials(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Get stored PAB credentials from SQLite database."""
    try:
        credentials = await get_sap_credentials_by_user_id(session, current_user.id)

        if not credentials:
            raise HTTPException(status_code=404, detail="SAP credentials not found")

        return credentials.credentials_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve credentials: {e!s}")


@router.get("/ariba_agents")
async def get_ariba_agents(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Get stored Ariba agents from SQLite database."""
    logger.info(f"Ariba agents request from user: {current_user.id}")
    
    try:
        logger.debug("Retrieving SAP credentials from database")
        credentials = await get_sap_credentials_by_user_id(session, current_user.id)

        if not credentials:
            logger.warning(f"No SAP credentials found for user: {current_user.id}")
            return []
            
        if not credentials.agents_data:
            logger.info(f"No agents data found for user: {current_user.id}")
            return []

        # Handle both old format (direct list) and new format (wrapped in dict)
        if isinstance(credentials.agents_data, dict) and "agents" in credentials.agents_data:
            agents = credentials.agents_data["agents"]
        elif isinstance(credentials.agents_data, list):
            # Legacy format - direct list
            agents = credentials.agents_data
        else:
            logger.warning(f"Unexpected agents_data format for user: {current_user.id}")
            return []

        logger.info(f"Successfully retrieved {len(agents)} agents for user: {current_user.id}")
        return agents

    except Exception as e:
        logger.error(f"Failed to retrieve Ariba agents for user {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agents: {e!s}")


@router.post("/ariba_agents")
async def save_ariba_agents(
    agents_data: list[dict[str, Any]],
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Save Ariba agents to SQLite database."""
    try:
        credentials = await get_sap_credentials_by_user_id(session, current_user.id)

        if not credentials:
            raise HTTPException(status_code=404, detail="SAP credentials not found. Please save credentials first.")

        # Wrap agents list in a dictionary structure to match the database model
        agents_dict = {"agents": agents_data}
        credentials_update = SAPCredentialsUpdate(agents_data=agents_dict)
        await update_sap_credentials(session, current_user.id, credentials_update)

        return {"success": True, "message": "Agents saved successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save agents: {e!s}")


@router.delete("/pab/credentials")
async def delete_pab_credentials(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Delete PAB credentials from SQLite database."""
    try:
        from langflow.services.database.models.sap.crud import delete_sap_credentials

        success = await delete_sap_credentials(session, current_user.id)

        if success:
            return {"success": True, "message": "PAB credentials deleted successfully"}
        raise HTTPException(status_code=404, detail="SAP credentials not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete credentials: {e!s}")
