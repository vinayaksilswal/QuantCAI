import asyncio, os, sys
sys.path.append(os.path.abspath('.'))
from services.ai_service import generate_promotional_email

class MockProduct:
    id = '123'
    productName = 'Mock Product'
    sellPrice = 45.0
    originalPrice = 50.0
    categoryName = 'Health'
    tagline = 'Tag'
    description = 'Desc'
    highlights = ['h1', 'h2']
    productImage = 'https://via.placeholder.com/600'

async def main():
    res = await generate_promotional_email(MockProduct())
    print("SUCCESS, FIRST 200 CHARS OF HTML:")
    print(res['bodyHtml'][:200])

asyncio.run(main())
