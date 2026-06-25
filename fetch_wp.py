import urllib.request
import re

html = urllib.request.urlopen('https://quantcai.in').read().decode('utf-8')
links = re.findall(r'href=[\'\"](https://warriorplus\.com[^\'\"]+)[\'\"]', html)
images = re.findall(r'src=[\'\"](https://warriorplus\.com[^\'\"]+)[\'\"]', html)
print("Links:", links)
print("Images:", images)
