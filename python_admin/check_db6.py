import asyncio, asyncpg, json, os
from dotenv import load_dotenv

load_dotenv()

async def main():
    conn = await asyncpg.connect(os.environ['DATABASE_URL'])
    rows = await conn.fetch("SELECT id, status, caption, \"mediaUrls\" FROM \"SocialPost\" ORDER BY \"createdAt\" DESC LIMIT 20")
    for r in rows:
        if 'QuantCAI' in (r['caption'] or ''):
            print(json.dumps(dict(r), indent=2, default=str))
    await conn.close()

asyncio.run(main())
