from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db

router = APIRouter(
    prefix="/ingestion",
    tags=["Ingestion"]
)


@router.get("/health")
def ingestion_health():
    return {
        "message": "Ingestion Service Running"
    }