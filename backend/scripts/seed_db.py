import asyncio
import sys
import os
import uuid
from sqlalchemy import select

# Add the parent directory (backend) to sys.path to allow imports from 'app'
# Assuming scripts/seed_db.py is executed from backend root or scripts dir
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import database
from app.database import init_connection_pool, Base
from app.models import User, Exercise, WorkoutTemplate, EventLog
from sqlalchemy.ext.asyncio import async_sessionmaker

async def seed():
    print("Initializing DB Connection...")
    await init_connection_pool()
    
    if not database.async_engine:
        print("Failed to initialize database connection. Check config.")
        return

    # Create tables if they don't exist (Useful for local dev / quickstart)
    print("Ensuring local schema...")
    async with database.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(database.async_engine, expire_on_commit=False)
    
    async with async_session() as session:
        print("Seeding Users...")
        clients = [
            User(id="auth0|alice", profile_data={"name": "Athlete Alice", "type": "Hyrox Pro", "goals": ["Sub 60 Hyrox"]}),
            User(id="auth0|bob", profile_data={"name": "Executive Bob", "type": "Traveler", "goals": ["Maintenance", "Health"]}),
            User(id="auth0|ian", profile_data={"name": "Injured Ian", "type": "Rehab", "goals": ["Knee Rehab"]}),
            # Demo User for Travel Mode Toggle
            User(id="1", profile_data={"name": "Demo Client", "type": "VIP", "goals": ["Look Good Naked"]}),
        ]
        
        for client in clients:
            result = await session.execute(select(User).where(User.id == client.id))
            if not result.scalar_one_or_none():
                session.add(client)
        
        print("Seeding Exercises...")
        exercises_data = [
            # --- Hyrox / Functional ---
            {"name": "Sled Push", "category": "Hyrox", "muscle_group": "Full Body", "is_hyrox_station": True, "equipment": ["Sled"]},
            {"name": "Sled Pull", "category": "Hyrox", "muscle_group": "Full Body", "is_hyrox_station": True, "equipment": ["Sled", "Rope"]},
            {"name": "SkiErg", "category": "Hyrox", "muscle_group": "Full Body", "is_hyrox_station": True, "concept2_id": 1, "equipment": ["SkiErg"]},
            {"name": "Rowing", "category": "Hyrox", "muscle_group": "Full Body", "is_hyrox_station": True, "concept2_id": 2, "equipment": ["Rower"]},
            {"name": "Wall Balls", "category": "Hyrox", "muscle_group": "Legs/Shoulders", "is_hyrox_station": True, "equipment": ["Medicine Ball", "Target"]},
            {"name": "Burpee Broad Jump", "category": "Hyrox", "muscle_group": "Full Body", "is_hyrox_station": True, "equipment": []},
            {"name": "Farmers Carry", "category": "Hyrox", "muscle_group": "Grip/Core", "is_hyrox_station": True, "equipment": ["Kettlebells"]},
            {"name": "Sandbag Lunges", "category": "Hyrox", "muscle_group": "Legs", "is_hyrox_station": True, "equipment": ["Sandbag"]},
            {"name": "Running", "category": "Cardio", "muscle_group": "Legs", "is_hyrox_station": True, "equipment": []},

            # --- Strength (Core) ---
            {"name": "Barbell Back Squat", "category": "Strength", "muscle_group": "Legs", "equipment": ["Barbell", "Rack"]},
            {"name": "Deadlift", "category": "Strength", "muscle_group": "Posterior Chain", "equipment": ["Barbell"]},
            {"name": "Bench Press", "category": "Strength", "muscle_group": "Chest", "equipment": ["Barbell", "Bench"]},
            {"name": "Overhead Press", "category": "Strength", "muscle_group": "Shoulders", "equipment": ["Barbell"]},
            {"name": "Pull Up", "category": "Strength", "muscle_group": "Back", "equipment": ["Pull Up Bar"]},
            {"name": "Dumbbell Row", "category": "Strength", "muscle_group": "Back", "unilateral": True, "equipment": ["Dumbbell", "Bench"]},
            {"name": "Bulgarian Split Squat", "category": "Strength", "muscle_group": "Legs", "unilateral": True, "equipment": ["Dumbbell", "Bench"]},
            {"name": "Romanian Deadlift", "category": "Strength", "muscle_group": "Posterior Chain", "equipment": ["Barbell"]},
            
            # --- Accessory / Hypertrophy ---
            {"name": "Incline Dumbbell Press", "category": "Hypertrophy", "muscle_group": "Chest", "equipment": ["Dumbbells", "Incline Bench"]},
            {"name": "Lateral Raise", "category": "Hypertrophy", "muscle_group": "Shoulders", "equipment": ["Dumbbells"]},
            {"name": "Face Pull", "category": "Hypertrophy", "muscle_group": "Rear Delts", "equipment": ["Cable"]},
            {"name": "Tricep Pushdown", "category": "Hypertrophy", "muscle_group": "Arms", "equipment": ["Cable"]},
            {"name": "Bicep Curl", "category": "Hypertrophy", "muscle_group": "Arms", "equipment": ["Dumbbells"]},
            {"name": "Leg Extension", "category": "Hypertrophy", "muscle_group": "Legs", "equipment": ["Machine"]},
            {"name": "Leg Curl", "category": "Hypertrophy", "muscle_group": "Legs", "equipment": ["Machine"]},
            {"name": "Calf Raise", "category": "Hypertrophy", "muscle_group": "Legs", "equipment": ["Machine"]},
            
            # --- Core / Mobility ---
            {"name": "Plank", "category": "Core", "muscle_group": "Core", "equipment": []},
            {"name": "Hanging Leg Raise", "category": "Core", "muscle_group": "Core", "equipment": ["Pull Up Bar"]},
            {"name": "Russian Twist", "category": "Core", "muscle_group": "Core", "equipment": ["Medicine Ball"]},
            {"name": "90/90 Hip Switch", "category": "Mobility", "muscle_group": "Hips", "equipment": []},
            {"name": "Cat Cow", "category": "Mobility", "muscle_group": "Spine", "equipment": []},
        ]

        for ex_data in exercises_data:
            result = await session.execute(select(Exercise).where(Exercise.name == ex_data["name"]))
            if not result.scalar_one_or_none():
                exercise = Exercise(**ex_data)
                session.add(exercise)
        
        print("Seeding Red Flag Event...")
        # Check if Bob has recent events to avoid spamming on re-runs
        # For this script, we'll just add it to ensure the "Red Flag" exists for the demo
        red_flag = EventLog(
            user_id="auth0|bob",
            event_type="wearable",
            payload={"sleep_score": 45, "hrv": 20, "rhr": 65},
            agent_decision="RED",
            agent_message="Critical recovery warning. Sleep score 45 indicates severe under-recovery. Recommended: Active Recovery only."
        )
        session.add(red_flag)
        
        print("Seeding Additional Events for Dashboard...")
        # Alice (Optimal)
        alice_event = EventLog(
            user_id="auth0|alice",
            event_type="wearable",
            payload={"sleep_score": 85, "hrv": 65, "rhr": 52},
            agent_decision="GREEN",
            agent_message="Recovery is optimal. High intensity Hyrox session recommended."
        )
        session.add(alice_event)
        
        # Ian (Vision/Rehab)
        ian_event = EventLog(
            user_id="auth0|ian",
            event_type="vision",
            payload={"detected_equipment": ["Kettlebell", "Mat"], "session_type": "mobility"},
            agent_decision="WORKOUT_GENERATED",
            agent_message="Detected equipment for knee rehab. mobility protocol active."
        )
        session.add(ian_event)

        await session.commit()
        print("Seed Complete! Database is populated.")

if __name__ == "__main__":
    asyncio.run(seed())
