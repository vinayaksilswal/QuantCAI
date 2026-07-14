import asyncio
from prisma import Prisma
import base64

async def main():
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # 1MB
        data = b'0' * 1024 * 1024
        encoded = base64.b64encode(data).decode('ascii')
        
        print("Creating 1MB media...")
        media = await prisma.media.create(
            data={
                "filename": "test1.txt",
                "mimeType": "text/plain",
                "data": encoded
            }
        )
        print("Success!")
        
        # 50MB
        data = b'0' * 50 * 1024 * 1024
        encoded = base64.b64encode(data).decode('ascii')
        print("Creating 50MB media...")
        media = await prisma.media.create(
            data={
                "filename": "test50.txt",
                "mimeType": "text/plain",
                "data": encoded
            }
        )
        print("Success!")
        
    except Exception as e:
        print(f"Exception type: {type(e)}")
        print(f"Exception str: '{str(e)}'")
        import traceback
        traceback.print_exc()
    finally:
        await prisma.disconnect()

asyncio.run(main())
