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
    utils.setup_nimbus_roman(plt, font_manager, DIR)

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

    # === plot ===
    boxplot_data = []
    offsets = np.array([0, .5, .5, 1, 1, 1, 1, 1])[::-1]


    for idx, category in enumerate(categories[::-1]):
        # ax.barh(idx, data.loc[~data[category].isna(), 'estimate_mau'].median(), color=colors[category])
        boxplot_data.append(combined.loc[(~combined[category].isna()) & (~combined['estimate_mau'].isna()) & (combined['estimate_mau'] > 0), 'estimate_mau'])
        
    f, ax = plt.subplots()
    ax.boxplot(boxplot_data, vert=False, medianprops={'color':'tab:red'}, positions = (np.arange(1, len(boxplot_data)+1) - offsets))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.xaxis.grid(ls=':')
    ax.set_axisbelow(True)
    ax.set_yticks(np.arange(1, len(categories)+1)-offsets)
    ax.set_yticklabels([new_categogories[c] for c in categories[::-1]])
    ax.set_xlabel('Audience size estimate')
    ax.set_xticks([0, .5e8, 1.00e8, 1.5e8, 2e8, 2.5e8])
    ax.set_xticklabels(['0', '50M', '100M', '150M', '200M', '250M'])

    f.set_size_inches(3, 2.1)
    f.savefig(os.path.join(DIR, 'rq3_audience_size.pdf'), bbox_inches='tight')    