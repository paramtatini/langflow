import logging
from typing import Any

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


@router.post("/pab/credentials", response_model=SaveCredentialsResponse)
async def save_pab_credentials(
    request_data: dict[str, Any],
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Save PAB credentials as JSON to SQLite database."""
    try:
        # Check if credentials already exist for this user
        existing_credentials = await get_sap_credentials_by_user_id(session, current_user.id)

        if existing_credentials:
            # Update existing credentials
            credentials_update = SAPCredentialsUpdate(
                credentials_data=request_data,
                agents_data=None,  # Clear agents data when updating credentials
            )
            await update_sap_credentials(session, current_user.id, credentials_update)
            return SaveCredentialsResponse(success=True, message="SAP credentials updated successfully")
        # Create new credentials
        credentials_create = SAPCredentialsCreate(credentials_data=request_data, agents_data=None)
        await create_sap_credentials(session, current_user.id, credentials_create)
        return SaveCredentialsResponse(success=True, message="SAP credentials saved successfully")

    except Exception as e:
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


@router.get("/pab/agents")
async def get_pab_agents(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Get stored PAB agents from SQLite database."""
    logger.info(f"PAB agents request from user: {current_user.id}")
    
    try:
        logger.debug("Retrieving SAP credentials from database")
        credentials = await get_sap_credentials_by_user_id(session, current_user.id)

        if not credentials:
            logger.warning(f"No SAP credentials found for user: {current_user.id}")
            return []
            
        if not credentials.agents_data:
            logger.info(f"No agents data found for user: {current_user.id}")
            return []

        logger.info(f"Successfully retrieved {len(credentials.agents_data)} agents for user: {current_user.id}")
        return credentials.agents_data

    except Exception as e:
        logger.error(f"Failed to retrieve PAB agents for user {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agents: {e!s}")


@router.post("/pab/agents")
async def save_pab_agents(
    agents_data: list[dict[str, Any]],
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Save PAB agents to SQLite database."""
    try:
        credentials = await get_sap_credentials_by_user_id(session, current_user.id)

        if not credentials:
            raise HTTPException(status_code=404, detail="SAP credentials not found. Please save credentials first.")

        # Update agents data
        credentials_update = SAPCredentialsUpdate(agents_data=agents_data)
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
