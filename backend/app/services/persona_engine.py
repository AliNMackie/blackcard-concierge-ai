import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import TrainerPersona
from app.services.rag_service import coaching_engine
from vertexai.generative_models import GenerationConfig

logger = logging.getLogger("elite-concierge")

class PersonaEngine:
    @staticmethod
    async def get_persona_signature(trainer_id: str, db: AsyncSession) -> Optional[str]:
        """
        Retrieves the cached voice signature for a trainer.
        """
        stmt = select(TrainerPersona).where(TrainerPersona.trainer_id == trainer_id)
        result = await db.execute(stmt)
        persona = result.scalar_one_or_none()
        return persona.voice_signature if persona else None

    @staticmethod
    async def distill_voice_signature(trainer_id: str, samples: List[str], db: AsyncSession) -> str:
        """
        Takes raw style samples and uses Gemini to generate a high-fidelity 
        persona prompt (The Voice Signature).
        """
        prompt = f"""
        TASK: Distill a 'Coaching Voice Signature' from the following communication samples.
        
        SAMPLES:
        {chr(10).join(['- ' + s for s in samples])}
        
        MISSION:
        Identify the specific tone, vocabulary, sentence structure, and coaching philosophy.
        Output a 3-4 sentence 'Style Instruction' that can be used to prime an LLM to clone this voice.
        Focus on:
        - Formality level (sophisticated vs grifting vs aggressive).
        - Use of specific jargon or catchphrases.
        - Strategic emphasis (technical vs motivational).
        
        Output only the instructions.
        """

        coaching_engine._ensure_init()
        if not coaching_engine.model:
            return "Professional, technical, and direct coaching tone."

        try:
            response = coaching_engine.model.generate_content(
                prompt,
                generation_config=GenerationConfig(temperature=0.2)
            )
            signature = response.text.strip()
            
            # Upsert into DB
            stmt = select(TrainerPersona).where(TrainerPersona.trainer_id == trainer_id)
            result = await db.execute(stmt)
            persona = result.scalar_one_or_none()
            
            if not persona:
                persona = TrainerPersona(trainer_id=trainer_id, voice_signature=signature, style_samples=samples)
                db.add(persona)
            else:
                persona.voice_signature = signature
                persona.style_samples = samples
            
            await db.commit()
            return signature
            
        except Exception as e:
            logger.error(f"Persona Distillation Error: {e}")
            return "Professional coaching tone."

persona_engine = PersonaEngine()
