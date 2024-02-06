import pandas as pd
import json
import numpy as np
from collections import defaultdict, Counter


ca_advertisers = {}
# 'ca_owner_name': 'Klarna'


def get_targeting(ut, aid):
    # also updates global list of CA advertisers
    global ca_advertisers

    # there is always an el['__typename'] == 'WAISTUIAgeGenderType'
    all_targetings = {'id': aid}
    for el in ut['data']['waist_targeting_data']:
        if el['__typename'] == 'WAISTUIInterestsType':
            all_targetings['interests'] = set([i['name'] for i in el['interests']])
        elif el['__typename'] == 'WAISTUICustomAudienceType':
            ca_advertisers[aid] = el['dfca_data']['ca_owner_name']
            all_targetings['custom'] = True
        elif el['__typename'] == 'WAISTUILocationType':
            gran = json.loads(el['serialized_data'])['location_granularity']
            loc = el['location_name']
            all_targetings['location'] = {'loc': loc, 'gran': gran}
        elif el['__typename'] == 'WAISTUIAgeGenderType':
            all_targetings['age-gender'] = {
                'age_min': el['age_min'],
                'age_max': el['age_max'],
                'gender': el['gender']
            }        
        
    return all_targetings


if __name__ == '__main__':
    # load targetings
    ad_targetings = {}
    targeting_file = '../../db-processing/ad-targetings.tsv'
    with open(targeting_file, 'r') as fh:
        for line in fh:
            ad_id, targeting = line.split('\t')
            targeting = json.loads(targeting.strip())            
            ad_targetings[ad_id] = targeting
            
    # prepare regression file for targeting vs. relevance regression
    allrows = []
    for adid in ad_targetings:
        tar = get_targeting(ad_targetings[adid], adid)
        interests = 0
        if 'interests' in tar:
            interests = len(tar['interests'])
        custom = int('custom' in tar)        
        row = [str(adid), interests, custom]
        allrows.append(row)

    outfile = 'adid_targeting.csv'
    df = pd.DataFrame(allrows, columns=['adid', 'n_interests', 'custom'])    
    df.to_csv(outfile, index=False)
    print(f'Exported targeting data to {outfile}!')