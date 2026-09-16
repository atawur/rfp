from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.notification_receiver import NotificationReceiver
from app.schemas.notification_receiver import (
    NotificationReceiver as NotificationReceiverSchema,
    NotificationReceiverCreate,
    NotificationReceiverUpdate,
)
from app.repositories.notification_receiver_repo import notification_receiver_repo

router = APIRouter()


@router.get("/", response_model=List[NotificationReceiverSchema])
def read_notification_receivers(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve all notification receivers.
    """
    query = db.query(NotificationReceiver)
    if status_filter:
        query = query.filter(NotificationReceiver.status == status_filter)
    return query.order_by(NotificationReceiver.id.asc()).offset(skip).limit(limit).all()


@router.post("/", response_model=NotificationReceiverSchema, status_code=status.HTTP_201_CREATED)
def create_notification_receiver(
    *,
    db: Session = Depends(deps.get_db),
    receiver_in: NotificationReceiverCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new notification receiver contact.
    """
    existing = notification_receiver_repo.get_by_email(db, email=receiver_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A notification receiver with this email already exists.",
        )
    return notification_receiver_repo.create(db, obj_in=receiver_in)


@router.get("/{receiver_id}", response_model=NotificationReceiverSchema)
def read_notification_receiver(
    receiver_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get notification receiver by ID.
    """
    receiver = notification_receiver_repo.get(db, id=receiver_id)
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification receiver not found.",
        )
    return receiver


@router.put("/{receiver_id}", response_model=NotificationReceiverSchema)
def update_notification_receiver(
    receiver_id: int,
    receiver_in: NotificationReceiverUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a notification receiver.
    """
    receiver = notification_receiver_repo.get(db, id=receiver_id)
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification receiver not found.",
        )
    if receiver_in.email and receiver_in.email != receiver.email:
        conflict = notification_receiver_repo.get_by_email(db, email=receiver_in.email)
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A notification receiver with this email already exists.",
            )
    return notification_receiver_repo.update(db, db_obj=receiver, obj_in=receiver_in)


@router.delete("/{receiver_id}")
def delete_notification_receiver(
    receiver_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a notification receiver.
    """
    receiver = notification_receiver_repo.get(db, id=receiver_id)
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification receiver not found.",
        )
    notification_receiver_repo.remove(db, id=receiver_id)
    return {"message": "Notification receiver deleted successfully."}
