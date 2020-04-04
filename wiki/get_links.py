import sys
from lxml import etree
import re

try:
    _, page = sys.argv
except ValueError:
    print('need a page')
    exit()
    
with open(page) as f:
    directory = etree.HTML(f.read())
    
links = directory.xpath('//li/a[1]/@href') + directory.xpath('//tr/td[1]/a[1]/@href')
regex = r'.*((hospital)|(infirmary)|(centre))([^s].*)?$'
hospitals = filter(lambda l: re.match(regex, l, re.IGNORECASE), links)

for link in hospitals:
    print(f'https://en.wikipedia.org/{link}')


