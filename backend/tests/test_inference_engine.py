"""
Tests for Level 5: Ambient Physical Intelligence.

Validates:
  - Vector insertion for ContextualMemory models (InferenceState, BiomechanicalSignature).
  - Situational Similarity Retrieval using pgvector cosine distance `<=>`.
  - Golden Form retrieval based on string + vector constraints.
"""
import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.contextual_memory import InferenceState, BiomechanicalSignature
from app.services.inference_engine import find_similar_situations, SimilarityQuery, embed_text

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def db_session(db_engine):
    """Provides a fresh async session from the conftest.py engine."""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()

class TestContextualMemoryVectors:
    
    async def test_vector_insertion(self, db_session: AsyncSession):
        """Test 1: Ensure state_vector and embedding save correctly to PostgreSQL."""
        user_id = "test_vector_insert_user"
        
        # Insert InferenceState
        mock_vec = [0.1] * 768
        state = InferenceState(
            id=str(uuid.uuid4()),
            user_id=user_id,
            state_vector=mock_vec,
            context_summary="Test insertion state",
        )
        db_session.add(state)
        
        # Insert BiomechanicalSignature
        movement_vec = [0.2] * 768
        signature = BiomechanicalSignature(
            id=str(uuid.uuid4()),
            user_id=user_id,
            movement_type="barbell_squat",
            is_golden=True,
            embedding=movement_vec,
        )
        db_session.add(signature)
        
        await db_session.commit()
        
        # Retrieve and verify
        retrieved_state = await db_session.get(InferenceState, state.id)
        assert retrieved_state is not None
        assert len(retrieved_state.state_vector) == 768
        # Due to float precision, we check close equality for the first element
        assert abs(retrieved_state.state_vector[0] - 0.1) < 0.0001
        
        retrieved_sig = await db_session.get(BiomechanicalSignature, signature.id)
        assert retrieved_sig is not None
        assert retrieved_sig.movement_type == "barbell_squat"

class TestSituationalSimilarityEngine:
    
    async def test_situational_similarity_retrieval(self, db_session: AsyncSession):
        """
        Test 2: Mock 5 InferenceState rows. Query V_current that matches one row exactly.
        Assert cosine distance operator returns it as top match.
        """
        user_id = f"test_sim_user_{uuid.uuid4().hex[:6]}"
        
        # We'll use embed_text here so we can generate identical deterministic vectors
        exact_match_context = "Slept 4 hours after a late transatlantic flight, resting HR 65."
        orthogonal_contexts = [
            "Fully rested, 8 hours of sleep, ready for a PR.",
            "Normal training day, moderate stress.",
            "Recovering from a slight cold, HRV is baseline.",
            "Carb-loaded after a cheat meal, feeling energetic."
        ]
        
        # Seed exact match
        exact_vec = await embed_text(exact_match_context)
        db_session.add(InferenceState(
            id="exact_match_id",
            user_id=user_id,
            state_vector=exact_vec,
            context_summary=exact_match_context,
            resulting_outcome="Skipped heavy squats, did mobility."
        ))
        
        # Seed pseudo-orthogonal ones
        for i, ctx in enumerate(orthogonal_contexts):
            vec = await embed_text(ctx)
            db_session.add(InferenceState(
                id=f"other_{i}",
                user_id=user_id,
                state_vector=vec,
                context_summary=ctx,
                resulting_outcome="Regular workout."
            ))
            
        await db_session.commit()
        
        # Execute query
        query = SimilarityQuery(
            user_id=user_id,
            current_context=exact_match_context, # Querying with identical text -> identical vector
            limit=3
        )
        
        results = await find_similar_situations(query, db_session)
        
        # Assertions
        assert len(results) > 0
        top_match = results[0]
        
        # Should be the exact match we seeded
        assert top_match.id == "exact_match_id"
        # Similarity should be ~1.0 since it's an identical vector
        assert top_match.similarity_score > 0.99 
        # Verify the custom attribute returned mapping worked
        assert top_match.resulting_outcome == "Skipped heavy squats, did mobility."


class TestBiomechanicalSignatureRetrieval:

    async def test_golden_form_retrieval(self, db_session: AsyncSession):
        """
        Test 3: Ensure we can query movement_type + vector and retrieve the Golden Form correctly.
        """
        user_id = f"test_golden_{uuid.uuid4().hex[:6]}"
        
        # Add a golden squat
        golden_squat = BiomechanicalSignature(
            id=str(uuid.uuid4()),
            user_id=user_id,
            movement_type="barbell_squat",
            is_golden=True,
            embedding=[0.3] * 768,
            kinematic_notes="Perfect depth, rigid torso."
        )
        db_session.add(golden_squat)
        
        # Add a non-golden squat (e.g. daily drift log)
        daily_squat = BiomechanicalSignature(
            id=str(uuid.uuid4()),
            user_id=user_id,
            movement_type="barbell_squat",
            is_golden=False,
            embedding=[0.31] * 768,
            kinematic_notes="Shifted slightly to the right."
        )
        db_session.add(daily_squat)
        
        # Add a golden deadlift
        golden_deadlift = BiomechanicalSignature(
            id=str(uuid.uuid4()),
            user_id=user_id,
            movement_type="deadlift",
            is_golden=True,
            embedding=[0.4] * 768,
        )
        db_session.add(golden_deadlift)
        
        await db_session.commit()
        
        # Simulate endpoint logic: retrieve only golden squal
        stmt = (
            select(BiomechanicalSignature)
            .where(BiomechanicalSignature.user_id == user_id)
            .where(BiomechanicalSignature.movement_type == "barbell_squat")
            .where(BiomechanicalSignature.is_golden == True)
        )
        result = await db_session.execute(stmt)
        record = result.scalar_one_or_none()
        
        assert record is not None
        assert record.id == golden_squat.id
        assert record.kinematic_notes == "Perfect depth, rigid torso."
