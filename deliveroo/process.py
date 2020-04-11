import sys
from lxml import etree
import re
from pathlib import Path
import time
import requests
import pickle
import urllib
import csv
from categories import categories

_, page = sys.argv

wanted_cache = 'wanted.pickle'
if not Path(wanted_cache).exists():
    with open(page) as f:
        directory = etree.HTML(f.read())

    cities = directory.xpath('/html/body/div[2]/div[2]/ul/ul/li/a')

    wanted = {}
    for city in cities:
        if re.findall(r'([yn] centre)|(central)', city.text, re.IGNORECASE):
            path = city.attrib["href"]
            slug = Path(path).name
            wanted[city.text] = {
                'url': f'https://deliveroo.co.uk{path}',
                'path': f'{slug}.html',
            }

    with open(wanted_cache, 'wb') as f:
        pickle.dump(wanted, f)

else:
    with open(wanted_cache, 'rb') as f:
        wanted = pickle.load(f)


deliveroo_cache = Path('./deliveroo_cache')
if not deliveroo_cache.exists():
    deliveroo_cache.mkdir()
        
def download(cache, place, params):
    path = cache / place['path']
    user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'
    if not path.exists():
        print(f'downloading {place["url"]}...', end=' ')
        try:
            response = requests.get(place['url'],  params=params, headers={ 'User-Agent': user_agent })
            if response.status_code == 200:
                with open(path, 'w') as f:
                    f.write(response.text)
                print('done')
            else:
                print(f'failed with status {response.status_code}')
            return True
        except requests.exceptions.ConnectionError:
            print(f"fail")
    


for city, place in wanted.items():
    downloaded = download(deliveroo_cache, place, params={
        'hygiene': ['hygiene rating five', 'hygiene rating four'],
        'category': categories
    })
    
    if downloaded:
        time.sleep(0.5)

providers = []
    
for city, place in wanted.items():
    with open(deliveroo_cache / place['path']) as f:
        page = etree.HTML(f.read())
        
    sections = page.xpath('//*[@id="__next"]/div/div/div[2]/div/div[2]/div/ul/li')
    for section in sections:
        section_root = section.xpath('div/div/a/span/span[2]/div[2]/ul')
        if section_root:
            (section_root, ) = section_root
            name = section_root.xpath('li/span/p/text()')
            if name:
                name = name[0].strip()
                cats = section_root.xpath('li[2]/span[@style="color:#828585"]/span/text()')
                cats = [c for c in cats if len(c) > 1]
                try:
                    rating = section_root.xpath('li[2]/span[3]/span/text()')[0]
                    rating = float(rating.split()[0])
                except (ValueError, IndexError):
                    rating = None

                providers.append({
                    'name': name,
                    'city': city,
                    'rating': rating,
                    'categories': ', '.join(cats),
                })
            

yell_cache = Path('./yell_cache')
if not yell_cache.exists():
    yell_cache.mkdir()
        

usable_providers = []

for provider in providers:
    if re.match(r'^(BP M)|(Co-op).*', provider['name']):
        continue

    location = provider['city'].split()[0]
    query = f'{provider["name"]}, {location}'
    params = urllib.parse.urlencode({ 'q': query })
    google = f'https://www.google.com/search?{params}'
    # print(google)

    search_result = Path(f'~/Downloads/providers/{query} - Google Search.html').expanduser()

    if search_result.exists():
    
        with open(search_result) as f:
            page = etree.HTML(f.read())

        phone = page.xpath('//*[@class="zgWrF"]/text()')

        uprovider = provider.copy()
        uprovider['google'] = google
        if phone:
            uprovider['phone'] = phone[0]
        facebook = [l for l in page.xpath('//a/@href') if re.findall(f'facebook', l)]
        if facebook:
            uprovider['facebook'] = facebook[0]
            
        if phone or facebook:    
            usable_providers.append(uprovider)


with open('deliveroo_providers.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=['name', 'city', 'rating', 'phone', 'facebook', 'google', 'categories'])
    writer.writeheader()
    
    for provider in usable_providers:
        writer.writerow(provider)

    print(f'wrote {len(usable_providers)} providers')

