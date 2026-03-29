from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app import models, schemas, services

router = APIRouter(prefix="/bulk", tags=["Bulk Transactions"])


@router.post("/validate", response_model=schemas.BulkValidationResponse)
def validate_bulk(
    payload:      schemas.BulkValidateRequest,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    result = services.validate_bulk(db, current_user, payload.rows)
    return result


@router.post("/submit", response_model=schemas.BulkSubmitResponse, status_code=201)
def submit_bulk(
    payload:      schemas.BulkSubmitRequest,
    db:           Session      = Depends(get_db),
    current_user: models.User  = Depends(get_current_user),
):
    result = services.submit_bulk(db, current_user, payload.rows)
    return result
