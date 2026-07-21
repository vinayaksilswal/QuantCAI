import asyncio, asyncpg, json
import sys
sys.path.append('python_admin')
from config import settings

async def main():
    conn = await asyncpg.connect(settings.database_url)
    rows = await conn.fetch('SELECT id, status, caption, "mediaUrls" FROM "SocialPost" ORDER BY "createdAt" DESC LIMIT 5')
    print(json.dumps([dict(r) for r in rows], indent=2, default=str))
    await conn.close()

asyncio.run(main())
