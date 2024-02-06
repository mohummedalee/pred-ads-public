import utils
import sys
import os
import pdb

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
from collections import defaultdict, Counter


if __name__ == '__main__':
    DIR = sys.argv[1]   # dir to save plot must be passed, ideally plots/
    
    # change font
    utils.setup_nimbus_roman(plt, font_manager, DIR)

    survey_file = 'data/survey_responses.tsv'
    survey = pd.read_csv(survey_file, sep='\t')

    codes_file = 'data/ad_codes_transformed.tsv'
    codes = pd.read_csv(codes_file, sep='\t')
    adid_codes = dict(zip(codes['adid'], [r.split(';') for r in codes['codes']]))
    survey_codes = survey.merge(codes, 'inner', 'adid')

    # === compute participant perception summaries ===
    perceptions = defaultdict(list)  # perceptions by code
    survey_code_counts = Counter()   # number of times each code appeared in survey
    perceptions_disliked = defaultdict(list)    # only recording ads here that have dont-like chosen for like reasons
    survey_disliked_counts = Counter()    

    for i in range(survey_codes.shape[0]):
        row = survey_codes.iloc[i]
        if 'Study' in row['codes']:
            # Ignore ads that were studies -- this is extremely important for our paper
            continue
        for curr_code in row['codes'].split(';'):
            survey_code_counts[curr_code] += 1
            # add both reasons for like and dislike into some arrray
            perceptions[curr_code].extend([utils.short_names[r] for r in row['like'].split(';')])
            perceptions[curr_code].extend([utils.short_names[r] for r in row['dislike'].split(';')])
            
            if "I do not like this ad." in row['like']:
                # this is a disliked ad, record perceptions separately
                perceptions_disliked[curr_code].extend([utils.short_names[r] for r in row['like'].split(';')])
                perceptions_disliked[curr_code].extend([utils.short_names[r] for r in row['dislike'].split(';')])
                survey_disliked_counts[curr_code] += 1

    plot_order = ['Potentially Prohibited', 'Potentially Harmful', 'Clickbait', 'Financial', 'Sensitive',
             'Opportunity', 'Healthcare', 'Benign']
    x_names = ['Pot. Prohibited', 'Deceptive', 'Clickbait', 'Sensitive: Financial', 'Sensitive: Other',
                'Opportunity', 'Healthcare', 'Neutral']                
    colors = {'irrelevant': 'dimgray', 'dislike-product': 'tab:purple', 'dislike-design': 'brown', 'dislike-design': 'steelblue',
            'scam': 'tab:red', 'unclear': 'goldenrod', 'clickbait': 'tab:orange', 'other': 'brown'}
    labeled = {c: False for c in colors}
    labels = {
        'irrelevant': 'Irrelevant', 'dislike-product': 'Product',
        'dislike-design': 'Design',
        'unclear': 'Unclear', 'clickbait': 'Clickbait',
        'scam': 'Scam', 'other': 'Other'
    }

    f, axs = plt.subplots(1, 1, figsize=(4, 3))
    # f.subplots_adjust(hspace=.2)

    # saving both general and reason-specific dislike counts for chi-2 testing
    chisq_export = {}
    for i, c in enumerate(plot_order):
        # ===== Plot general dislike =====
        freqs = Counter(perceptions[c])
        dont_like = freqs['dont-like']
        frac = dont_like / survey_code_counts[c]
        err = utils.get_err(frac, survey_code_counts[c], Zval=1.960)    
        chisq_export[c] = (dont_like, frac, survey_code_counts[c])    
        axs.errorbar([frac],[i],  xerr=err, color='k', ls=':', markersize=4, marker='o')                
        
    print('====== For Proportion Testing ======')
    print('overall dislike:', chisq_export)    

    axs.grid(ls=':')
    #ax.set_xlabel('Ad Type', fontweight='bold')
    # axs.set_yticks(np.arange(len(x_names)), x_names);
    axs.set_yticks(np.arange(len(x_names)));
    axs.set_yticklabels(x_names)
    axs.spines['top'].set_visible(False)
    axs.spines['right'].set_visible(False)
        
    axs.set_xlabel('Fraction Disliked in Surveys')
    # axs.set_title('Overall Dislike by Ad Type')    

    # axs[1].legend(bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
    #                     ncol=3, mode="expand", borderaxespad=0., frameon=False)

    # f.subplots_adjust(hspace=.6)
    # f.set_size_inches(8, 3)
    f.set_size_inches(3, 2.1)
    plt.savefig(os.path.join(DIR, 'plot_dislike.pdf'), bbox_inches='tight')
