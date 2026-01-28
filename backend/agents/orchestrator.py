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
    
    stmt = select(Exercise)
    if category:
        stmt = stmt.where(Exercise.category == category)
    if muscle_group:
         stmt = stmt.where(Exercise.muscle_group == muscle_group)
    if is_hyrox:
        stmt = stmt.where(Exercise.is_hyrox_station == True)
        
    try:
        async with database.async_engine.connect() as conn:
            result = await conn.execute(stmt)
            # result row: (ExerciseObj,)
            rows = result.all()
            
            data = []
            for row in rows: 
                 ex = row[0]
                 data.append(f"- {ex.name} (Cat: {ex.category}, Equip: {ex.equipment})")
                 
            if not data:
                return "No exercises found matching criteria."
            
            # Limit to prevent context overflow
            return "\n".join(data[:15])
            
    except Exception as e:
        logger.error(f"Tool Execution Error: {e}")
        return f"Database Query Failed: {str(e)}"

def get_system_prompt(coach_style="hyrox_competitor"):
    # 1. The Global UK Filter (Applied to EVERY persona)
    uk_localization_rules = """
    **LINGUISTIC REQUIREMENT: STRICT UK ENGLISH**
    - **Spelling:** Use 's' instead of 'z' (Optimise, Realise). Use 'our' (Colour, Labour). Use 're' (Centre, Metre).
    - **Vocabulary:** - Say 'Mum', NEVER 'Mom' or 'Mommy'.
        - Say 'Trainers', NOT 'Sneakers'.
        - Say 'Holiday', NOT 'Vacation'.
        - Say 'Programme', NOT 'Program' (when referring to the plan).
    - **Format:** Use Metric (kg/km) unless specifically asked for lbs.
    """

    base_prompt = f"""
    You are the Client's dedicated High-Performance Coach.
    {uk_localization_rules}
    
    **Your Principles:**
    1. **Data First:** Check `client_biometrics` before prescribing intensity.
    2. **Safety:** If recovery is <40%, downgrade intensity.
    3. **Tool Use:** Use `query_exercise_db` to find exercises.
    """
    
    # The Styles (Now stripping specific names to be "White Label")
    styles = {
        "hyrox_competitor": """
        **Tone**: "The Technical Athlete". Motivational, data-driven, focused on pacing.
        **Key Phrases**: 'Compromised Running', 'Splits', 'Threshold'.
        **Style**: Direct and professional. Focus on the leaderboard.
        """,
        
        "empowered_mum": """
        **Tone**: "The Supportive Postnatal Specialist". Empathetic but firm on consistency.
        **Key Phrases**: 'Pelvic health', 'Energy management', 'Routine'.
        **Style**: Warm and encouraging. Acknowledges that 'time is tight'.
        """,
        
        "muscle_architect": """
        **Tone**: "The Hypertrophy Expert". Serious about aesthetics and mechanics.
        **Key Phrases**: 'Time Under Tension', 'Volume', 'Contraction'.
        **Style**: Disciplined. Treats the gym floor like a lab.
        """,
        
        "bio_optimizer": """
        **Tone**: "The Science-Based Practitioner". Clinical and precise.
        **Key Phrases**: 'Circadian rhythm', 'Cortisol', 'Adaptation'.
        **Style**: Educated and calm. Explains the 'Why' behind the 'What'.
        """
    }
    
    return base_prompt + "\n\n" + styles.get(coach_style, styles["hyrox_competitor"])

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
        model = GenerativeModel(settings.GEMINI_MODEL_ID) 
    except Exception as e:
        return f"AI Initialization Failed: {e}"

    # 1. Fetch Context (Recent Logs)
    sleep_score = 75 # Default
    
    async with database.async_engine.connect() as conn:
         # Find latest wearable event
         stmt = select(EventLog).where(
             EventLog.user_id == client_id, 
             EventLog.event_type == "wearable"
         ).order_by(EventLog.created_at.desc()).limit(1)
         
         result = await conn.execute(stmt)
         row = result.first()
         
         if row:
             log = row[0]
             # Handle different payload structures (Terra vs Seed)
             p = log.payload
             if "sleep_score" in p:
                 sleep_score = p["sleep_score"]
             elif "data" in p and "scores" in p["data"]:
                 sleep_score = p["data"]["scores"].get("recovery", 50)
    
    logger.info(f"Orchestrator: Client {client_id} has Sleep Score {sleep_score}")

    # 2. Construct Prompt
    # 2. Construct Prompt
    system_prompt = get_system_prompt(coach_style="hyrox_competitor") # Default to hyrox for now
    prompt = f\"\"\"
    {system_prompt}
    
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
    chat = model.start_chat(tools=[training_tools])
    
    # 1st Turn: Send Prompt
    response = await chat.send_message(prompt)
    
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
                response_final = await chat.send_message(
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
