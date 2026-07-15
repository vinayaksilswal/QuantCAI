import sys
import os
try:
    from prisma.fields import Base64
    obj = Base64(b"test")
    print("Type:", type(obj))
    print("Methods:", dir(obj))
    print("str:", str(obj))
    
    if hasattr(obj, 'decode'):
        print("decode():", obj.decode())
        
except Exception as e:
    print(e)
