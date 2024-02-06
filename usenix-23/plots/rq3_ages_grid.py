import sys, os 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
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

    # === fractions for age targeting ===
    fractions = []
    for idx, category in enumerate(categories[::-1]):
        cat_total = (~combined[category].isna()).sum()
        cat_fractions = []
        
        cat_idx = ~combined[category].isna()
        for age in range(18, 66):
            age_idx = cat_idx & (combined['age_min_explicit'] <= age-12) & (combined['age_max_explicit'] > age-12)
            # if age >= 18:
            #     age_idx = age_idx | (cat_idx & combined['age_min'].isna())
            cat_fractions.append(age_idx.sum()/cat_idx.sum())
        fractions.append(cat_fractions)
   

    # === plot ===    
    # Create 2x2 sub plots
    gs = gridspec.GridSpec(2, 8)
    f = plt.figure()
                        
    for lidx, (line, category) in enumerate(zip(fractions[::-1][1:], categories[1:])):
        ax = f.add_subplot(gs[lidx//4, (((lidx%4)*2+lidx//4)) : (((lidx%4)*2+2+lidx//4))])
        ax.plot(range(18, 66), line, label=category, color = colors[category])
        ax.plot(range(18, 66), fractions[-1], label=category, color = colors['Benign'], lw=0.5)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(ls=':')
        ax.set_axisbelow(True)
        ax.set_ylim(0.3, 1)
        if lidx % 4 != 0:
            ax.set_yticklabels([])
        else:
            ax.set_ylabel('Fraction of ads that\ninclude age $x$ in targeting')
        
        ax.set_xticks([21, 30, 40, 50, 60])
        
        
        if lidx == 5: 
            ax.set_xlabel('Age')        
            
        ax.annotate(new_categogories[category], xy=(1, 0), xycoords='axes fraction', ha='right', va='bottom')        

        f.set_size_inches(8, 4)
        f.savefig('rq3_ages_y.pdf', bbox_inches='tight')

        # axes[0].set_ylabel('Fraction of ads\ntargeting age $x$')
        # axes[0].set_xticks([21, 30, 40, 50, 60])
        f.subplots_adjust(wspace=0.1)
        f.set_size_inches(8, 4)
        f.savefig(os.path.join(DIR, 'rq3_ages_grid.pdf'), bbox_inches='tight')