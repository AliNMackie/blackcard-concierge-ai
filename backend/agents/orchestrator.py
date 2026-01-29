import vertexai
from vertexai.generative_models import GenerativeModel, Tool, FunctionDeclaration, Part
from sqlalchemy import select
from app import database
from app.models import EventLog, Exercise
from app.config import settings, logger
import asyncio
import json

# Ensure db pool is init if this module is imported standalone (handled by lifespan in main app usually)

# --- Tool Definitions ---

sql_tool_spec = FunctionDeclaration(
    name="query_exercise_db",
    description="Query the exercise database for movements based on criteria. Returns names and details of available equipment/exercises.",
    parameters={
        "type": "object",
        "properties": {
            "muscle_group": {"type": "string", "description": "Target muscle group (e.g. Legs, Chest, Back, Full Body)"},
            "category": {"type": "string", "description": "Category filter (Hyrox, Strength, Cardio)"},
            "is_hyrox": {"type": "boolean", "description": "If true, filter only Hyrox stations"}
        },
        "required": ["category"]
    },
)

training_tools = Tool(
    function_declarations=[sql_tool_spec],
)

# --- Agent Logic ---

async def execute_sql_tool(muscle_group: str = None, category: str = None, is_hyrox: bool = False):
    """
    Actual Python implementation of the SQL tool.
    """
    logger.info(f"Agent executing SQL Tool: Group={muscle_group}, Cat={category}, Hyrox={is_hyrox}")
    
    stmt = select(Exercise.name, Exercise.category, Exercise.equipment)
    if category:
        stmt = stmt.where(Exercise.category == category)
    if muscle_group:
         stmt = stmt.where(Exercise.muscle_group == muscle_group)
    if is_hyrox:
        stmt = stmt.where(Exercise.is_hyrox_station == True)
        
    try:
        async with database.async_engine.connect() as conn:
            result = await conn.execute(stmt)
            rows = result.all()
            
            data = []
            for row in rows: 
                 data.append(f"- {row.name} (Cat: {row.category}, Equip: {row.equipment})")
                 
            if not data:
                return "No exercises found matching criteria."
            
            # Limit to prevent context overflow
            return "\n".join(data[:15])
            
    except Exception as e:
        logger.error(f"Tool Execution Error: {e}")
        return f"Database Query Failed: {str(e)}"

def get_system_prompt(coach_style="hyrox_competitor"):
    # Map internal keys to the elaborate instructions from the new prompt
    persona_instructions = {
        "hyrox_competitor": """
        **Persona: HYROX / Hybrid Athlete**
        - Emphasise mixed-modality conditioning, race-specific movements (sleds, wall balls, runs), pacing, and transitions.
        - Include periodic race simulations and clear guidance on target paces and RPE.
        """,
        "muscle_architect": """
        **Persona: Muscle Gain / Physique**
        - Emphasise progressive overload, stable exercise selection, appropriate weekly volume per muscle group, and clear progression rules (load, reps, or sets).
        """,
        "empowered_mum": """
        **Persona: Mum into fitness / Post-natal or busy parent**
        - Prioritise safety, core and pelvic floor awareness where relevant, time-efficient sessions, and recovery-friendly planning.
        """,
        "bio_optimizer": """
        **Persona: Longevity / High Performer**
        - Balance resistance training, Zone 2 cardio, mobility, and stress management; integrate deloads and recovery blocks.
        """
    }

    selected_persona_instruction = persona_instructions.get(coach_style, persona_instructions["hyrox_competitor"])

    return f"""
    You are an AI workout planning engine for a high-end fitness app used by personal trainers (PTs) and their clients.
    Your job is to generate structured workout sessions using an existing exercise database and to respect any PT interventions from the “God Mode” dashboard.

    **Data model & constraints**
    - You must only use exercises that exist in the database (via `query_exercise_db` tool) when prescribing sets/reps/tempo.
    - If a requested exercise is not in the DB, choose the closest available alternative and clearly label it as a substitution in the notes.

    **Personas & Goal-Driven Behaviour**
    {selected_persona_instruction}

    **Rules:**
    - Align the plan with goal, training age, schedule, equipment, and constraints.
    - Make trade-offs explicit in notes when constraints conflict.

    **PT Overrides (“God Mode”) Logic**
    The user prompt may contain natural-language overrides (e.g., "Change today to strict Zone 2 cardio").
    - **Never ignore a PT override.** If it conflicts with periodisation, obey the override.
    - If ambiguous, interpret conservatively for safety.
    - If equipment is missing for an override, choose the closest bodyweight/low-impact option.

    **Safety & UX**
    - Provide scaling options for demanding exercises.
    - Avoid prescribing maximal testing (1RM) unless requested.
    - Keep language clear, concise, and free of medical claims.

    **Output Format**
    Return the workout in this strictly valid JSON structure (no markdown formatting around it, just raw JSON if possible, or inside a json block):

    {{
      "metadata": {{
        "persona": "{coach_style}",
        "session_type": "string",
        "estimated_duration_min": "integer"
      }},
      "blocks": [
        {{
          "type": "warm_up|main|finisher|cool_down",
          "exercises": [
            {{
              "exercise_name": "string (must match DB)",
              "sets": "integer",
              "reps_or_time": "string",
              "intensity": "string (RPE, %1RM, etc)",
              "rest_seconds": "integer",
              "notes": "string (cues, substitutions)"
            }}
          ]
        }}
      ]
    }}
    """

async def get_workout_plan(client_id: str):
    """
    The 'Real Brain' entry point: Hybrid RAG.
    1. Fetches User Context (Sleep Score).
    2. Prompts Gemini.
    3. Gemini calls SQL Tool to find exercises.
    4. Gemini generates Plan.
    """
    try:
        # Init Vertex inside function to avoid startup errors if auth missing locally
        vertexai.init(project=settings.PROJECT_ID, location=settings.GCP_REGION)
        # Use Configured Model
        model = GenerativeModel(settings.GEMINI_MODEL_ID, tools=[training_tools])
    except Exception as e:
        return f"AI Initialization Failed: {e}"

    # 1. Fetch Context (Recent Logs & Travel Status)
    sleep_score = 75 # Default
    is_traveling = False
    
    async with database.async_engine.connect() as conn:
         # Find latest wearable event
         stmt = select(EventLog.payload).where(
             EventLog.user_id == client_id, 
             EventLog.event_type == "wearable"
         ).order_by(EventLog.created_at.desc()).limit(1)
         
         result = await conn.execute(stmt)
         log = result.scalar_one_or_none()
         
         if log:
             # Handle different payload structures (Terra vs Seed)
             p = log
             if "sleep_score" in p:
                 sleep_score = p["sleep_score"]
             elif "data" in p and "scores" in p["data"]:
                 sleep_score = p["data"]["scores"].get("recovery", 50)
         
         # Check Travel and Persona Status
         from app.models import User
         user_stmt = select(User).where(User.id == client_id)
         user_result = await conn.execute(user_stmt)
         user = user_result.scalar_one_or_none()
         
         is_traveling = user.is_traveling if user else False
         coach_style = user.coach_style if user and user.coach_style else "hyrox_competitor"
    
    logger.info(f"Orchestrator: Client {client_id} has Sleep Score {sleep_score}, Traveling={is_traveling}, Persona={coach_style}")

    # 2. Construct Prompt
    system_prompt = get_system_prompt(coach_style=coach_style)
    
    travel_injection = ""
    if is_traveling:
        travel_injection = """
        **CRITICAL CONTEXT:** Client is currently TRAVELING. RESTRICT equipment usage to: Bodyweight, Resistance Bands, and Hotel Dumbbells only. Focus on Mobility and metabolic conditioning. Do NOT prescribe heavy barbells or sleds.
        """

    prompt = f"""
    {system_prompt}
    {travel_injection}
    
    Client ID: {client_id}
    Recovery Score: {sleep_score}/100.
    
    Mission: Build a workout session.
    
    LOGIC:
    - If score < 50: Recommend Active Recovery (Mobility, easy Cardio). Query 'Core' or 'Mobility' or 'Cardio'.
    - If score >= 50: Recommend High Intensity Hyrox/Strength. Query 'Hyrox' or 'Strength'.
    
    INSTRUCTIONS:
    1. Check the database using `query_exercise_db` to find available exercises matching the logic.
    2. Output a structured plaintext session plan.
    """
    
    # 3. Chat Interaction with Tool Use
    chat = model.start_chat()
    
    # 1st Turn: Send Prompt
    response = await chat.send_message_async(prompt)
    
    # Loop for Function Calling (Simple 1-turn loop for MVP)
    # response.candidates[0].content.parts might contain a function call
    
    try:
        part = response.candidates[0].content.parts[0]
        
        if part.function_call:
            fc = part.function_call
            fn_name = fc.name
            args = dict(fc.args)
            
            # Execute Python Tool
            if fn_name == "query_exercise_db":
                tool_output = await execute_sql_tool(
                    muscle_group=args.get("muscle_group"),
                    category=args.get("category"),
                    is_hyrox=args.get("is_hyrox", False)
                )
                
                # Send Tool Output back to Model
                response_final = await chat.send_message_async(
                    Part.from_function_response(
                        name=fn_name,
                        response={"content": tool_output}
                    )
                )
                return response_final.text
                
        return response.text
        
    except Exception as e:
        logger.error(f"Orchestrator Loop Error: {e}")
        return f"Error generating plan: {e}"
