import urllib.request

data = b'test data'
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="test.mp4"\r\n'
    f'Content-Type: video/mp4\r\n\r\n'
).encode('utf-8') + data + f'\r\n--{boundary}--\r\n'.encode('utf-8')

req = urllib.request.Request('http://127.0.0.1:8000/api/v1/upload-media', data=body)
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
try:
    response = urllib.request.urlopen(req)
    print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(e.read().decode('utf-8'))
