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
                agents_data=None  # Clear agents data when updating credentials
            )
            await update_sap_credentials(session, current_user.id, credentials_update)
            return SaveCredentialsResponse(
                success=True,
                message="SAP credentials updated successfully"
            )
        else:
            # Create new credentials
            credentials_create = SAPCredentialsCreate(
                credentials_data=request_data,
                agents_data=None
            )
            await create_sap_credentials(session, current_user.id, credentials_create)
            return SaveCredentialsResponse(
                success=True,
                message="SAP credentials saved successfully"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save credentials: {str(e)}"
        )


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
            raise HTTPException(
                status_code=404,
                detail="SAP credentials not found"
            )
        
        return credentials.credentials_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve credentials: {str(e)}"
        )


@router.get("/pab/agents")
async def get_pab_agents(
    *,
    session: DbSession,
    current_user: CurrentActiveUser,
):
    """Get stored PAB agents from SQLite database."""
    try:
        credentials = await get_sap_credentials_by_user_id(session, current_user.id)
        
        if not credentials or not credentials.agents_data:
            return []
        
        return credentials.agents_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve agents: {str(e)}"
        )


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
            raise HTTPException(
                status_code=404,
                detail="SAP credentials not found. Please save credentials first."
            )
        
        # Update agents data
        credentials_update = SAPCredentialsUpdate(
            agents_data=agents_data
        )
        await update_sap_credentials(session, current_user.id, credentials_update)
        
        return {"success": True, "message": "Agents saved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save agents: {str(e)}"
        )


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
        else:
            raise HTTPException(
                status_code=404,
                detail="SAP credentials not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete credentials: {str(e)}"
        )
