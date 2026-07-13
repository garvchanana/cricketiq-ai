from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db

from app.ingestion.api_fetchers.bulk_historical_ingestion import (
    BulkHistoricalIngestion
)

router = APIRouter(
    prefix="/historical",
    tags=["Historical Ingestion"]
)


@router.get("/health")
def historical_health():

    return {
        "message": "Historical Ingestion Running"
    }


@router.post("/ipl")
def ingest_ipl(
    db: Session = Depends(get_db)
):

    result = (
        BulkHistoricalIngestion.ingest_ipl_dataset(
            db=db
        )
    )

    return result