import sys
from pathlib import Path
import re
import pickle
from lxml import etree
import requests
import time
import json

def extract_id(element):
    try:
        (id, ) = re.match('.*\?id=(\d+)', element.attrib['href']).groups()
        return int(id)
    except AttributeError:
        return None

def get_trusts():
    with open('NHSTrustListing.aspx') as f:
        directory = etree.HTML(f.read())

    trusts = {}
    for trust in directory.xpath('//*[@class="trust-list"]/li/a'):
        id = extract_id(trust)
        if id:
            trusts[id] = {
                'id': id,
                'name': trust.text,
            }
    return trusts

def download(ids, entity, page):
    '''
    download `page` for all ids
    '''
    folder = Path(entity) / page
    if not folder.exists():
        folder.mkdir(parents=True)
    for id in ids:
        path = folder / str(id)
        if not path.exists():
            print(f'downloading {entity}/{page} {id}...', end=' ')
            url = f'https://www.nhs.uk/Services/{entity}/{page}/DefaultView.aspx?id={id}'
            try:
                response = requests.get(url)
            except requests.exceptions.ConnectionError:
                print(f"fail")
                continue
            
            with open(path, 'w') as f:
                f.write(response.text)
            print('done')



def get_facilities(trusts_ids, facility_type):
    '''
    get facilities for all trusts in `trust_ids`
    facility_type = 'hospital' | 'clinic'
    '''
    output = {}
    for trust_id in trust_ids:
        with open(Path('trusts') / 'hospitalsandclinics' / str(trust_id)) as f: 
            d = etree.HTML(f.read())
        hlists = d.xpath(f'//*[@class="box-list clear {facility_type}-list"]')
        for hlist in hlists:
            for he in hlist.xpath('div/div/div'):
                h = he.xpath('h3/a')
                if len(h) > 0:
                    name = h[0].xpath('string()')
                    id = extract_id(h[0])
                    output[id] = {
                        'id': id,
                        'name': name,
                        'trust_id': trust_id,
                    }
    return output

def update_hospital(hospital):
    '''
    look in the overview, services and facilities page
    and write values into `hospital`
    '''
    ### overview
    with open(Path('./hospitals/overview') / str(hospital['id'])) as f:
        overview = etree.HTML(f.read())

    def add_key(key, xpath):
        try:
            hospital[key] = overview.xpath(xpath)[0]
        except IndexError:
            pass
        
    add_key('name', '//*[@id="org-title"]/text()')
    add_key('phone', '//*[@property="telephone"]/text()')
    add_key('website', '//a[@property="url"]/@href')
    add_key('pic', '//div[@class="profile-pic"]/img/@src')
    text = ' '.join(overview.xpath('//div[@class="panel-content"]/div/p/text()'))
    
    addressParts = overview.xpath('//span[@typeof="PostalAddress"]/span/@property')
    addressValues = overview.xpath('//span[@typeof="PostalAddress"]/span/text()')
    addressPartMap = {
        'streetAddress': 'street',
        'addressLocality': 'locality',
        'postalCode': 'postcode',
        'addressRegion': 'region',
    }
    hospital['address'] = { addressPartMap[p]: v for p, v in zip(addressParts, addressValues) }

    hospital['qos'] = {}
    for feedback in overview.xpath('//div[@class="service-feedback clear"]'):
        title = feedback.xpath('div[1]/h4/text()')[0]
        score = feedback.xpath('div[2]/p/span/text()')
        if len(score) == 0:
            try:
                score = feedback.xpath('div[2]/p/text()')[0]
            except IndexError:
                continue
        hospital['qos'][title] = ' '.join(score)

    ### services
    with open(Path('./hospitals/services') / str(hospital['id'])) as f:
        services = etree.HTML(f.read())
        
    hospital['departments'] = services.xpath('//*[@class="departments-services"]/table/tbody/tr/td/a/text()')

    ### facilities
    try:
        with open(Path('./hospitals/facilities') / str(hospital['id'])) as f:
            facilities = etree.HTML(f.read())

        hospital['facilities'] = facilities.xpath('//li[@class="yes"]/text()')
        
    except FileNotFoundError:
        pass

hospital_cache = 'hospitals.pickle'

if Path(hospital_cache).exists():
    print('loading from cache')
    with open(hospital_cache, 'rb') as f:
        hospitals = pickle.load(f)
else:
    trusts = get_trusts()
    trust_ids = list(trusts.keys())
    download(trust_ids, entity='trusts', page='hospitalsandclinics')
    hospitals = get_facilities(trust_ids, 'hospital')
    #clinics = get_facilities(trust_ids, 'clinic')
    print(len(hospitals), len(clinics))
    download(hospitals.keys(), entity='hospitals', page='overview')
    download(hospitals.keys(), entity='hospitals', page='services')
    download(hospitals.keys(), entity='hospitals', page='facilities')
    with open('hospitals.pickle', 'wb') as f:
        pickle.dump(hospitals, f)


for hospital in hospitals.values():
    update_hospital(hospital)

with open('hospitals.json', 'w') as f:
    json.dump(hospitals, f, indent=True)
