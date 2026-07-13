from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db

from app.services.batting_feature_service import (
    BattingFeatureService
)
from app.services.bowling_feature_service import (
    BowlingFeatureService
)
from app.services.match_phase_service import (
    MatchPhaseService
)
from app.services.advanced_batting_service import (
    AdvancedBattingService
)

from app.services.momentum_service import (
    MomentumService
)
from app.services.player_ranking_service import (
    PlayerRankingService
)
from app.services.team_analytics_service import (
    TeamAnalyticsService
)
from app.services.venue_analytics_service import (
    VenueAnalyticsService
)
from app.services.matchup_analytics_service import (
    MatchupAnalyticsService
)
from app.services.player_intelligence_service import (
    PlayerIntelligenceService
)

router = APIRouter(
    prefix="/features",
    tags=["Feature Engineering"]
)


@router.get("/health")
def feature_health():

    return {
        "message": "Feature Engineering Running"
    }


@router.post("/batting")
def generate_batting_features(
    db: Session = Depends(get_db)
):

    result = (
        BattingFeatureService
        .generate_batting_features(
            db=db
        )
    )

    return result

@router.post("/bowling")
def generate_bowling_features(
    db: Session = Depends(get_db)
):

    result = (
        BowlingFeatureService
        .generate_bowling_features(
            db=db
        )
    )

    return result

@router.post("/match-phases")
def generate_match_phase_features(
    db: Session = Depends(get_db)
):

    result = (
        MatchPhaseService
        .generate_phase_features(
            db=db
        )
    )

    return result

@router.post("/advanced-batting")
def generate_advanced_batting_features(
    db: Session = Depends(get_db)
):

    result = (
        AdvancedBattingService
        .generate_advanced_features(
            db=db
        )
    )

    return result

@router.post("/momentum")
def generate_momentum_features(
    db: Session = Depends(get_db)
):

    result = (
        MomentumService
        .generate_momentum_features(
            db=db
        )
    )

    return result

@router.post("/player-rankings")
def generate_player_rankings(
    db: Session = Depends(get_db)
):

    result = (
        PlayerRankingService
        .generate_player_rankings(
            db=db
        )
    )

    return result

@router.post("/team-analytics")
def generate_team_analytics(
    db: Session = Depends(get_db)
):

    result = (
        TeamAnalyticsService
        .generate_team_analytics(
            db=db
        )
    )

    return result

@router.post("/venue-analytics")
def generate_venue_analytics(
    db: Session = Depends(get_db)
):

    result = (
        VenueAnalyticsService
        .generate_venue_analytics(
            db=db
        )
    )

    return result

@router.post("/matchup-analytics")
def generate_matchup_analytics(
    db: Session = Depends(get_db)
):

    result = (
        MatchupAnalyticsService
        .generate_matchup_analytics(
            db=db
        )
    )

    return result

@router.post("/player-intelligence")
def generate_player_intelligence(
    db: Session = Depends(get_db)
):

    result = (
        PlayerIntelligenceService
        .generate_player_intelligence(
            db=db
        )
    )

    return result