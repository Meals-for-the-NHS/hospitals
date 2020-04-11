from pathlib import Path
from lxml import etree
from collections import defaultdict
import re
import csv
import pickle

def coords(s):
    finds = re.findall(' (-?\d+\.\d+); (-?\d+.\d+)', s)
    if len(finds) > 0:
        return finds[0]

def beds(s):
    finds = re.findall('(\d+)', s)
    if len(finds) > 0:
        return finds[0]
    
    
td_map = {
    'Coordinates': coords,
    'Beds': beds,
}

hospitals = []
th_counts= defaultdict(int)

for hospital_path in sorted(Path('./pages').iterdir()):
    with open(hospital_path) as f:            
        h = etree.HTML(f.read())

    try:
        name = h.xpath('//*[@id="mw-content-text"]/div/table[1]/tbody/tr[1]/th/text()')[0]
        trust = h.xpath('//*[@id="mw-content-text"]/div/table[1]/tbody/tr[2]/td')[0].xpath('string()')

        hospital = {
            'Name': name,
            'Trust': trust,
        }

        table_rows = h.xpath('//*[@id="mw-content-text"]/div/table/tbody/tr')
        for row in table_rows:
            th = row.xpath('th')
            if len(th) > 0:
                th = th[0].xpath('string()')
                try:
                    td = row.xpath('td')[0].xpath('string()')
                    if th in td_map:
                        td = td_map[th](td)
                    hospital[th] = td
                    th_counts[th] += 1
                except IndexError:
                    pass

        if not 'Closed' in hospital:
            hospitals.append(hospital)
                
    except IndexError:
        pass

# remove infrequent keys that will be wrong or useless
ths_to_remove = ['Closed']
for th, count in th_counts.items():
    if count < 3:
        ths_to_remove.append(th)
        
ths_to_keep = set(th_counts.keys()) - set(ths_to_remove)

with open('wiki_hospitals.csv', 'w') as f:
    columns = ['Name', 'Trust'] + sorted(list(ths_to_keep))
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    
    for hospital in hospitals:
        for th in ths_to_remove:
            if th in hospital:
                del hospital[th]

        writer.writerow(hospital)


with open('wiki_hospitals.pickle', 'wb') as f:
    pickle.dump(hospitals, f)
