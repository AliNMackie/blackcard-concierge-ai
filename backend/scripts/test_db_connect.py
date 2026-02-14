import asyncio
import asyncpg

async def test_connect():
    dsn = "postgresql://postgres:mysecretpassword@127.0.0.1:5432/postgres"
    print(f"Connecting to {dsn}...")
    try:
        conn = await asyncpg.connect(dsn)
        version = await conn.fetchval("SELECT version()")
        print(f"Connected! Version: {version}")
        await conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    if asyncio.get_event_loop_policy().__class__.__name__ == 'WindowsProactorEventLoopPolicy':
        # Fix for Windows loop issue with some async libraries, though asyncpg usually fine
        pass
    import os
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(test_connect())
