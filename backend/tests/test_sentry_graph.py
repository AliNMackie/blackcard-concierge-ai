"""
Tests for Phase 1 Level 3: Biometric Sentry Graph + Temporal Retriever.

Test strategy:
- Uses SQLite for fast, portable, Postgres-independent tests.
- Temporal decay math is tested in Python (since SQLite lacks exp()).
- Sentry graph is tested end-to-end via the `run_sentry_for_user` API,
  with mocked Gemini (no Vertex AI credentials required).
"""
import math
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock, MagicMock

from app.database import Base
from app.models import User, DailyBiometrics, DailyInsight, SessionAnalysis, WorkoutSession

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_phase3_sentry.db"


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
    """Creates a baseline user for sentry tests."""
    user = User(id="sentry_test_user", email="sentry@blackcard.app", role="client")
    test_db.add(user)
    await test_db.commit()
    return user


# ---------------------------------------------------------------------------
# 1. Temporal Decay Math (pure Python, no DB required)
# ---------------------------------------------------------------------------
class TestTemporalDecayMath:
    """Validate the decay formula: Score = cosine_sim * exp(-λ * days_ago)"""

    LAMBDA = 0.05

    def _compute_weighted(self, cos_sim: float, days_ago: float) -> float:
        return cos_sim * math.exp(-self.LAMBDA * days_ago)

    def test_recent_session_scores_higher(self):
        """A session from 2 days ago should score higher than 30 days ago
        even if both have the same cosine similarity."""
        sim = 0.85
        recent_score = self._compute_weighted(sim, days_ago=2)
        old_score = self._compute_weighted(sim, days_ago=30)
        assert recent_score > old_score

    def test_decay_rate_half_life_approximately_14_days(self):
        """With λ=0.05, weight at 14 days ≈ 50% of day-0 weight."""
        at_zero = self._compute_weighted(1.0, days_ago=0)
        at_14 = self._compute_weighted(1.0, days_ago=14)
        ratio = at_14 / at_zero
        # Should be close to exp(-0.05 * 14) ≈ 0.497
        assert 0.45 < ratio < 0.55

    def test_perfect_similarity_today_dominates_old_high_sim(self):
        """Perfect match today still beats a slightly higher match from 60 days ago."""
        today_score = self._compute_weighted(1.0, days_ago=0)
        old_score = self._compute_weighted(0.99, days_ago=60)
        assert today_score > old_score

    def test_zero_similarity_produces_zero_score(self):
        score = self._compute_weighted(0.0, days_ago=5)
        assert score == 0.0


# ---------------------------------------------------------------------------
# 2. Temporal Retriever — Pydantic model + fallback path
# ---------------------------------------------------------------------------
class TestTemporalRetriever:

    async def test_returns_empty_on_no_sessions(self, test_db: AsyncSession, seeded_user):
        """If no session_analysis rows exist, result is empty."""
        from app.services.temporal_retriever import retrieve_temporally_weighted, TemporalRetrievalResult

        # Mock the embedding call
        with patch("app.services.temporal_retriever.retriever") as mock_retriever:
            mock_retriever.get_embedding = AsyncMock(return_value=[0.1] * 768)
            result = await retrieve_temporally_weighted(
                user_id="sentry_test_user",
                current_context="Recovery: RED, Sleep Score: 38/100",
                db=test_db,
            )

        assert isinstance(result, TemporalRetrievalResult)
        assert result.matches == []
        assert result.total_candidates == 0

    async def test_recent_session_returned_with_correct_shape(self, test_db: AsyncSession, seeded_user):
        """Seeds one session and verifies TemporalMatch shape."""
        from app.services.temporal_retriever import retrieve_temporally_weighted, TemporalMatch

        # Seed a WorkoutSession + SessionAnalysis
        session = WorkoutSession(
            user_id="sentry_test_user",
            date=datetime.now(timezone.utc) - timedelta(days=3),
            focus_area="Strength",
            rpe=7,
        )
        test_db.add(session)
        await test_db.flush()

        # Store a dummy embedding (all 0.5s, 768-dim)
        embedding = [0.5] * 768
        analysis = SessionAnalysis(
            session_id=session.id,
            user_id="sentry_test_user",
            content="Strength session with good HRV. Hit 5x5 squats at 120kg.",
            embedding=embedding,
        )
        test_db.add(analysis)
        await test_db.commit()

        with patch("app.services.temporal_retriever.retriever") as mock_retriever:
            # Return the same vector → cosine similarity = 1.0
            mock_retriever.get_embedding = AsyncMock(return_value=embedding)
            result = await retrieve_temporally_weighted(
                user_id="sentry_test_user",
                current_context="recovery fatigue low hrv",
                db=test_db,
            )

        assert len(result.matches) == 1
        match = result.matches[0]
        assert isinstance(match, TemporalMatch)
        assert match.raw_similarity > 0.99
        assert match.days_ago >= 2.9  # ~3 days
        # Weighted score should be lower than raw (decay applied)
        assert match.weighted_score < match.raw_similarity
        assert "Strength session" in match.content


# ---------------------------------------------------------------------------
# 3. Sentry Graph — End-to-End with Mocked Gemini
# ---------------------------------------------------------------------------
class TestSentryGraph:

    async def test_green_status_short_circuits(self, test_db: AsyncSession, seeded_user):
        """GREEN biometrics → no intervention, no DailyInsight created."""
        from app.sentry_graph import run_sentry_for_user

        test_db.add(DailyBiometrics(
            user_id="sentry_test_user",
            sleep_score=88,
            recovery_status="GREEN",
            date=datetime.now(timezone.utc),
        ))
        await test_db.commit()

        result = await run_sentry_for_user("sentry_test_user", test_db)

        assert result.recovery_status == "GREEN"
        assert result.intervention_triggered is False
        assert result.session_mutation is None
        assert result.notification_payload is None

    async def test_red_status_triggers_full_pipeline(self, test_db: AsyncSession, seeded_user):
        """RED biometrics → full pipeline runs, DailyInsight is persisted."""
        from app.sentry_graph import run_sentry_for_user
        from sqlalchemy import select

        test_db.add(DailyBiometrics(
            user_id="sentry_test_user",
            sleep_score=32,
            recovery_status="RED",
            date=datetime.now(timezone.utc),
        ))
        await test_db.commit()

        # Mock temporal retriever to return empty (no history needed for this test)
        # Build a lightweight mock result object (avoids nested AsyncMock issues)
        mock_retrieval = MagicMock()
        mock_retrieval.matches = []

        with patch("app.services.temporal_retriever.retrieve_temporally_weighted", new=AsyncMock(return_value=mock_retrieval)), \
             patch("rag.retriever.retriever") as mock_rag, \
             patch("app.sentry_graph.gemini_client") as mock_gemini:

            mock_rag.retrieve_protocol = MagicMock(return_value="RED Protocol: Zone 1 only.")
            mock_gemini.model = None
            mock_gemini._ensure_init = MagicMock()

            result = await run_sentry_for_user("sentry_test_user", test_db)

        assert result.intervention_triggered is True
        assert result.recovery_status == "RED"
        assert result.session_mutation is not None
        assert result.session_mutation.session_type_override == "recovery_protocol"
        assert result.session_mutation.intensity_cap_percent == 0
        assert result.session_mutation.volume_reduction_percent == 100
        assert result.notification_payload is not None
        assert "Recovery Protocol" in result.notification_payload["body"]
        assert "daily_insight_persisted" in result.actions_taken

        # Verify DailyInsight was persisted
        stmt = select(DailyInsight).where(DailyInsight.user_id == "sentry_test_user")
        db_result = await test_db.execute(stmt)
        insight = db_result.scalar_one_or_none()
        assert insight is not None
        assert insight.suggested_plan_override["session_type_override"] == "recovery_protocol"

    async def test_amber_status_triggers_deload_not_full_recovery(self, test_db: AsyncSession, seeded_user):
        """AMBER biometrics → deload mutation (50% volume, 60% intensity) not full recovery."""
        from app.sentry_graph import run_sentry_for_user

        test_db.add(DailyBiometrics(
            user_id="sentry_test_user",
            sleep_score=58,
            recovery_status="AMBER",
            date=datetime.now(timezone.utc),
        ))
        await test_db.commit()

        mock_retrieval = MagicMock()
        mock_retrieval.matches = []

        with patch("app.services.temporal_retriever.retrieve_temporally_weighted", new=AsyncMock(return_value=mock_retrieval)), \
             patch("rag.retriever.retriever") as mock_rag, \
             patch("app.sentry_graph.gemini_client") as mock_gemini:

            mock_rag.retrieve_protocol = MagicMock(return_value="AMBER Protocol: 50% volume.")
            mock_gemini.model = None
            mock_gemini._ensure_init = MagicMock()

            result = await run_sentry_for_user("sentry_test_user", test_db)

        assert result.intervention_triggered is True
        assert result.session_mutation is not None
        # AMBER allows some training
        assert result.session_mutation.intensity_cap_percent == 60
        assert result.session_mutation.volume_reduction_percent == 50
        assert result.session_mutation.session_type_override == "technical_deload"

    async def test_no_biometrics_gracefully_handled(self, test_db: AsyncSession, seeded_user):
        """If no biometrics row exists, sentry should not crash."""
        from app.sentry_graph import run_sentry_for_user

        # No biometrics seeded intentionally
        result = await run_sentry_for_user("sentry_test_user", test_db)

        assert result.recovery_status == "GREEN"
        assert result.intervention_triggered is False

    async def test_notification_payload_contains_whatsapp_format(self, test_db: AsyncSession, seeded_user):
        """WhatsApp payload must have correct channel, body, and timestamp keys."""
        from app.sentry_graph import run_sentry_for_user

        test_db.add(DailyBiometrics(
            user_id="sentry_test_user",
            sleep_score=30,
            recovery_status="RED",
            date=datetime.now(timezone.utc),
        ))
        await test_db.commit()

        mock_retrieval = MagicMock()
        mock_retrieval.matches = []

        with patch("app.services.temporal_retriever.retrieve_temporally_weighted", new=AsyncMock(return_value=mock_retrieval)), \
             patch("rag.retriever.retriever") as mock_rag, \
             patch("app.sentry_graph.gemini_client") as mock_gemini:

            mock_rag.retrieve_protocol = MagicMock(return_value="RED Protocol.")
            mock_gemini.model = None
            mock_gemini._ensure_init = MagicMock()

            result = await run_sentry_for_user("sentry_test_user", test_db)

        payload = result.notification_payload
        assert payload is not None
        assert payload["channel"] == "whatsapp"
        assert "body" in payload
        assert "timestamp" in payload
        # Body must contain the formatted markdown for WhatsApp
        assert "*" in payload["body"]     # Bold formatting
        assert "blackcard.app" in payload["body"]  # Deep link
