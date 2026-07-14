import asyncio
from prisma import Prisma
import os
from config import settings
from services.scheduler import _marketing_loop

async def main():
    prisma = Prisma()
    os.environ["DATABASE_URL"] = settings.database_url
    await prisma.connect()
    
    print("Running AI automation 5 times...")
    for i in range(5):
        print(f"Run {i+1}...")
        try:
            await _marketing_loop(prisma)
            print(f"Run {i+1} complete.")
        except Exception as e:
            print(f"Run {i+1} failed: {e}")
        
    await prisma.disconnect()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
