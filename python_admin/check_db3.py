import asyncio, asyncpg, json, os
from dotenv import load_dotenv

load_dotenv()

async def main():
    conn = await asyncpg.connect(os.environ['DATABASE_URL'])
    rows = await conn.fetch("SELECT id, status, caption, \"mediaUrls\" FROM \"SocialPost\" ORDER BY \"createdAt\" DESC LIMIT 5")
    print(json.dumps([dict(r) for r in rows], indent=2, default=str))
    await conn.close()

asyncio.run(main())
