import sys, os 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
from collections import defaultdict, Counter
import utils


DATA_DIR = 'data/'
new_categogories = {
    'Benign': 'Neutral',
    'Opportunity': 'Opportunity',
    'Healthcare': 'Healthcare',
    'Potentially Prohibited': 'Pot. Prohibited',
    'Potentially Harmful': 'Deceptive',
    'Financial': 'Sensitive: Financial',
    'Sensitive': 'Sensitive: Other',
    'Clickbait': 'Clickbait'
}
colors = {
    'Financial': 'tab:green', 'Problematic (all together)': 'maroon', 'Problematic': 'maroon',          
    'Benign': 'dimgray', 'Potentially Harmful': 'tab:red', 
    'Clickbait': 'tab:orange', 'Potentially Prohibited': 
    'tab:purple', 'Sensitive': 'hotpink',
    'Healthcare': 'tab:blue', 'Opportunity': '#33297a'
}


if __name__ == '__main__':
    DIR = sys.argv[1]
    # utils.setup_nimbus_roman(plt, font_manager, DIR)

    # load ad codes
    codes_file = 'ad_codes_transformed.tsv'
    codes = pd.read_csv(os.path.join(DATA_DIR, codes_file), sep='\t')
    adid_codes = dict(zip(codes['adid'], [r.split(';') for r in codes['codes']]))
    categories = ['Benign', 'Healthcare', 'Opportunity', 'Sensitive', 'Financial',
                  'Clickbait', 'Potentially Harmful',  'Potentially Prohibited']

    # load preprocessed targeting data
    targeting_params = pd.read_csv(os.path.join(DATA_DIR, 'targeting_params.csv'), low_memory=False)
    # get rid of the Nigerian and Indian ads
    targeting_params = targeting_params.loc[targeting_params['location'] != "{'serialized': {'location_granularity': 'country', 'location_geo_type': 'home', 'location_code': 'NG'}, 'location_name': 'Nigeria', 'location_type': 'HOME'}"]
    targeting_params = targeting_params.loc[targeting_params['location'] != "{'serialized': {'location_granularity': 'country', 'location_geo_type': 'home', 'location_code': 'IN'}, 'location_name': 'India', 'location_type': 'HOME'}"]
    maus = {row['adid']: row['estimate_mau'] for idx, row in targeting_params.iterrows()}
    
    custom_audiences = pd.read_csv(os.path.join(DATA_DIR, 'custom_types.csv'))    
    custom_audiences.set_index('Unnamed: 0', inplace=True)
    custom_audiences['CUSTOM_AUDIENCES_OTHER'] = custom_audiences['CUSTOM_AUDIENCES_MOBILE_APP'] == 1
    del custom_audiences['CUSTOM_AUDIENCES_MOBILE_APP']
    for k in ['CUSTOM_AUDIENCES_ENGAGEMENT_PAGE', 'CUSTOM_AUDIENCES_ENGAGEMENT_IG',
        'CUSTOM_AUDIENCES_ENGAGEMENT_VIDEO', 'CUSTOM_AUDIENCES_OFFLINE',
        'CUSTOM_AUDIENCES_ENGAGEMENT_LEAD_GEN',
        'CUSTOM_AUDIENCES_ENGAGEMENT_EVENT']:
        custom_audiences['CUSTOM_AUDIENCES_OTHER'] = custom_audiences['CUSTOM_AUDIENCES_OTHER'] | (custom_audiences[k] == 1)
        del custom_audiences[k]

    data = []
    for adid, adcodes in adid_codes.items():
        row = {code: 1 for code in adcodes}
        row['adid'] = adid
        try:
            row['estimate_mau'] = maus[adid]
        except:
            row['estimate_mau'] = float('nan')
        data.append(row)
    data = pd.DataFrame(data)

    # === combine all ===
    combined = targeting_params.set_index('adid').join(data.set_index('adid'), how='inner', lsuffix='l')
    combined['age_min_explicit'] = combined['age_min'].map(lambda x: 6 if pd.isna(x) else x)
    combined['age_max_explicit'] = combined['age_max'].map(lambda x: 54 if pd.isna(x) else x)
    joined = custom_audiences.join(combined, how='inner')
   

    # === plot ===
    f, axes = plt.subplots(1, 4, sharey=True, sharex=False)

    ca_labels = {'CUSTOM_AUDIENCES_LOOKALIKE': '(d) Lookalike', 
                'CUSTOM_AUDIENCES_DATAFILE': '(a) PII',
                'CUSTOM_AUDIENCES_WEBSITE': '(b) Website visits',
                'CUSTOM_AUDIENCES_OTHER': '(c) Other'}

    offsets = np.array([0, .5, .5, 1, 1, 1, 1, 1])[::-1]
    for axidx, k in enumerate(['CUSTOM_AUDIENCES_DATAFILE', 	
                            'CUSTOM_AUDIENCES_WEBSITE', 
                            'CUSTOM_AUDIENCES_OTHER',
                            'CUSTOM_AUDIENCES_LOOKALIKE']):
        ax = axes[axidx]
        for cidx, category in enumerate(categories[::-1]):
            y = cidx - offsets[cidx]
            ax.barh(y, joined.loc[joined[category]==1, k].sum()/(combined[category] == 1).sum(),
                    color=colors[category], alpha=.85)

        # ax.set_xticks([0, .2, .4, .6,])
        # ax.set_xticklabels(['0', '.2', '.4', '.6',])
        # ax.set_xlim(0, .7)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(ls=':')
        ax.set_axisbelow(True)
        ax.set_xlabel('Fraction of ads')
        ax.set_title(ca_labels[k])
        ax.set_xlim(0, 0.3)

    axes[0].set_yticks(np.arange(0, len(categories))-offsets)
    axes[0].set_yticklabels([new_categogories[c] for c in categories[::-1]])
        
    f.set_size_inches(8, 2.1)
    f.savefig('rq3_ca_prevalence_all.pdf', bbox_inches='tight')