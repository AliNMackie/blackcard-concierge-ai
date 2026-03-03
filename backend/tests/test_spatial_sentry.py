"""
Tests for Phase 2 Level 3: Spatial Sentry & Haversine Logic.

Validates the mathematical correctness of the Haversine formula
and ensures the spatial sentry correctly toggles Ghost Mode
based on the 50km threshold from Strathaven, Scotland.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import User
from app.services.spatial_sentry import (
    calculate_haversine_distance,
    check_spatial_boundary,
    HOME_BASE_LAT,
    HOME_BASE_LON,
    GHOST_MODE_THRESHOLD_KM
)

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_phase3_spatial.db"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="function")
async def test_db():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def seeded_user(test_db: AsyncSession):
    user = User(id="spatial_test_user", email="spatial@blackcard.app", role="client", is_traveling=False)
    test_db.add(user)
    await test_db.commit()
    return user


# ---------------------------------------------------------------------------
# 1. Haversine Math Verification
# ---------------------------------------------------------------------------
class TestHaversineMath:
    """Validate the strict mathematical Haversine formula implementation."""

    def test_distance_to_self_is_zero(self):
        distance = calculate_haversine_distance(HOME_BASE_LAT, HOME_BASE_LON, HOME_BASE_LAT, HOME_BASE_LON)
        assert distance == 0.0

    def test_distance_strathaven_to_london(self):
        # London: ~51.5072 N, 0.1276 W
        # Expected distance: ~530 km
        distance = calculate_haversine_distance(HOME_BASE_LAT, HOME_BASE_LON, 51.5072, -0.1276)
        assert 520 < distance < 550

    def test_distance_strathaven_to_glasgow_is_within_threshold(self):
        # Glasgow: 55.8642 N, 4.2518 W
        # Expected distance: ~23 km (definitely < 50km)
        distance = calculate_haversine_distance(HOME_BASE_LAT, HOME_BASE_LON, 55.8642, -4.2518)
        assert 20 < distance < 30
        assert distance <= GHOST_MODE_THRESHOLD_KM

    def test_distance_strathaven_to_edinburgh_is_outside_threshold(self):
        # Edinburgh: 55.9533 N, 3.1883 W
        # Expected distance: ~63 km (definitely > 50km)
        distance = calculate_haversine_distance(HOME_BASE_LAT, HOME_BASE_LON, 55.9533, -3.1883)
        assert 55 < distance < 70
        assert distance > GHOST_MODE_THRESHOLD_KM

    def test_antipodal_points_do_not_throw_math_domain_error(self):
        # Test poles (exactly opposite ends of earth) to ensure internal_sqrt = 1.0 clamping works
        distance = calculate_haversine_distance(90.0, 0.0, -90.0, 0.0)
        # Should be exactly half circumference (~20015 km)
        assert 19900 < distance < 20100


# ---------------------------------------------------------------------------
# 2. Spatial Sentry State Management
# ---------------------------------------------------------------------------
class TestSpatialSentry:

    async def test_glasgow_keeps_user_home(self, test_db: AsyncSession, seeded_user):
        """User in Glasgow (~23km) should remain is_traveling=False."""
        result = await check_spatial_boundary(
            user_id="spatial_test_user",
            current_lat=55.8642,
            current_lon=-4.2518,
            db=test_db
        )

        assert result["is_traveling"] is False
        assert result["status_changed"] is False
        
        # Verify DB untouched
        await test_db.refresh(seeded_user)
        assert seeded_user.is_traveling is False

    async def test_edinburgh_toggles_ghost_mode_on(self, test_db: AsyncSession, seeded_user):
        """User in Edinburgh (~63km) should cross the 50km threshold and trigger Ghost Mode."""
        result = await check_spatial_boundary(
            user_id="spatial_test_user",
            current_lat=55.9533,
            current_lon=-3.1883,
            db=test_db
        )

        assert result["is_traveling"] is True
        assert result["status_changed"] is True
        assert "Ghost Mode Activated" in result["message"]

        # Verify DB updated
        await test_db.refresh(seeded_user)
        assert seeded_user.is_traveling is True
        assert seeded_user.equipment_constraint == "Unknown Hotel Gym"

    async def test_subsequent_checks_outside_radius_do_not_retrigger_status(self, test_db: AsyncSession, seeded_user):
        """If already traveling, moving between foreign cities shouldn't count as a status toggle event."""
        seeded_user.is_traveling = True
        seeded_user.equipment_constraint = "Unknown Hotel Gym"
        await test_db.commit()

        # London coordinates
        result = await check_spatial_boundary(
            user_id="spatial_test_user",
            current_lat=51.5072,
            current_lon=-0.1276,
            db=test_db
        )

        assert result["is_traveling"] is True
        assert result["status_changed"] is False # Status didn't change, they were already traveling

    async def test_returning_home_toggles_ghost_mode_off(self, test_db: AsyncSession, seeded_user):
        """Returning to within 50km disables Ghost Mode and resets equipment constraints."""
        seeded_user.is_traveling = True
        seeded_user.equipment_constraint = "Unknown Hotel Gym"
        await test_db.commit()

        # Strathaven coordinates
        result = await check_spatial_boundary(
            user_id="spatial_test_user",
            current_lat=HOME_BASE_LAT,
            current_lon=HOME_BASE_LON,
            db=test_db
        )

        assert result["is_traveling"] is False
        assert result["status_changed"] is True
        assert "Welcome back" in result["message"]

        # Verify DB updated
        await test_db.refresh(seeded_user)
        assert seeded_user.is_traveling is False
        assert seeded_user.equipment_constraint == "Full Gym"
