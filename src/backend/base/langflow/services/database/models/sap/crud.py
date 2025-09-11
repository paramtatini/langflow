from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from langflow.schema.serialize import UUIDstr

from .model import SAPCredentials, SAPCredentialsCreate, SAPCredentialsUpdate


async def create_sap_credentials(
    session: AsyncSession, user_id: UUIDstr, credentials_create: SAPCredentialsCreate
) -> SAPCredentials:
    """Create new SAP credentials record."""
    db_credentials = SAPCredentials(
        user_id=user_id,
        credentials_data=credentials_create.credentials_data,
        agents_data=credentials_create.agents_data,
    )
    session.add(db_credentials)
    await session.commit()
    await session.refresh(db_credentials)
    return db_credentials


async def get_sap_credentials_by_user_id(session: AsyncSession, user_id: UUIDstr) -> SAPCredentials | None:
    """Get SAP credentials for a user."""
    statement = select(SAPCredentials).where(SAPCredentials.user_id == user_id)
    result = await session.exec(statement)
    return result.first()


async def update_sap_credentials(
    session: AsyncSession, user_id: UUIDstr, credentials_update: SAPCredentialsUpdate
) -> SAPCredentials | None:
    """Update existing SAP credentials or create new ones."""
    db_credentials = await get_sap_credentials_by_user_id(session, user_id)

    if db_credentials:
        # Update existing record
        if credentials_update.credentials_data is not None:
            db_credentials.credentials_data = credentials_update.credentials_data
        if credentials_update.agents_data is not None:
            db_credentials.agents_data = credentials_update.agents_data
        db_credentials.updated_at = datetime.now(timezone.utc)

        session.add(db_credentials)
        await session.commit()
        await session.refresh(db_credentials)
        return db_credentials
    # Create new record if none exists
    create_data = SAPCredentialsCreate(
        credentials_data=credentials_update.credentials_data or {}, agents_data=credentials_update.agents_data
    )
    return await create_sap_credentials(session, user_id, create_data)


async def delete_sap_credentials(session: AsyncSession, user_id: UUIDstr) -> bool:
    """Delete SAP credentials for a user."""
    db_credentials = await get_sap_credentials_by_user_id(session, user_id)
    if db_credentials:
        await session.delete(db_credentials)
        await session.commit()
        return True
    return False
