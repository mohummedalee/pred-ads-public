"""
Extracted from analyses/analyses_achtung/rq2/distribution_disparities_sec52.ipynb
"""

import utils
import sys
import os
import pdb

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
from collections import defaultdict, Counter

DATA_DIR = 'data/'

# It was found that 250/36257 ads in pid_adid were not coded in adid_codes
if __name__ == '__main__':
    DIR = sys.argv[1]
    utils.setup_nimbus_roman(plt, font_manager, DIR)

    # === Active participants ===
    active_pids = open(os.path.join(DATA_DIR, 'pid_active_contribs_cleaned.txt'), 'r').readlines()
    active_pids = [p.strip() for p in active_pids]

    codes = pd.read_csv(os.path.join(DATA_DIR, 'ad_codes_transformed.tsv'), sep='\t')
    print('codes shape:', codes.shape)
    adid_codes = dict(zip(codes['adid'], codes['codes']))

    # === participant to ad matching ===
    pid_adid_files = [os.path.join(DATA_DIR, f'surveys/survey-{n}/survey{n}_coding_subsample.tsv') \
                      for n in range(1, 8)]
    pid_adid_files.append(os.path.join(DATA_DIR, 'surveys/survey-1/survey1_batch2_coding_subsample.tsv'))
    pid_adid = pd.read_csv(pid_adid_files[0], sep='\t')
    for f in pid_adid_files[1:]:
        pid_adid = pd.concat([pid_adid, pd.read_csv(f, sep='\t')], ignore_index=True)

    # only keep PID ADID mapping for active participants
    pid_adid = pid_adid[pid_adid['pid'].isin(active_pids)]
    print('pid_adid shape:', pid_adid.shape)  

    # participant x ad frequency of seeing
    pid_adid_freqs_noind = pd.read_csv(os.path.join(DATA_DIR, 'participant_ad_freqs.tsv'), sep='\t')
    pid_adid_freqs = pid_adid_freqs_noind.set_index(['pid', 'adid'])

    # === Process data and plot ===
    # count exposure and total ads
    exposure, ann_ads_count = utils.measure_exposure(active_pids, adid_codes, pid_adid, pid_adid_freqs)

    # count grouped exposure
    harmful, non_harmful = 'harmful', 'non_harmful'
    groups = {
        'Potentially Harmful': harmful, 'Sensitive': harmful, 'Financial': harmful,
        'Clickbait': harmful, 'Potentially Prohibited': harmful, 'Benign': non_harmful,
        'Opportunity': 'other', 'Healthcare': 'other'
    }
    grouped_exposure, _ = utils.measure_exposure(active_pids, adid_codes, pid_adid, pid_adid_freqs, groups)

    f, ax = plt.subplots()
    labels = {'Potentially Harmful': 'Deceptive', 'Financial': 'Sensitive: Financial', 'Sensitive': 'Sensitive: Other'}
    colors = {'Financial': 'tab:green', 'Problematic (all together)': 'maroon', 'Problematic': 'maroon',          
            'Benign': 'dimgray', 'Potentially Harmful': 'tab:red', 
            'Clickbait': 'tab:orange', 'Potentially Prohibited': 
            'tab:purple', 'Sensitive': 'hotpink',
            'Healthcare': 'tab:blue', 'Opportunity': '#33297a'}    # copied from Piotr

    harmful_counts = [grouped_exposure[p][harmful] for p in active_pids]
    harmful_pdf = np.array(harmful_counts) / sum(harmful_counts)
    harmful_cdf = [0]
    harmful_cdf.extend(np.cumsum(sorted(harmful_pdf, reverse=True)))

    neutral_counts = [grouped_exposure[p][non_harmful] for p in active_pids]
    neutral_pdf = np.array(neutral_counts) / sum(neutral_counts)
    neutral_cdf = [0]
    neutral_cdf.extend(np.cumsum(sorted(neutral_pdf, reverse=True)))

    # healthcare + opportunity = other 
    other_counts = [grouped_exposure[p]['other'] for p in active_pids]
    other_pdf = np.array(other_counts) / sum(other_counts)
    other_cdf = [0]
    other_cdf.extend(np.cumsum(sorted(other_pdf, reverse=True)))

    ax.plot(np.arange(len(active_pids)), np.arange(0, 1, 1/len(active_pids)), 'k:', label='Uniform Distribution')
    # ax.plot(harmful_cdf, color=colors['Problematic (all together)'], label='Problematic', lw=1.5)
    ax.plot(neutral_cdf, color=colors['Benign'], label='Neutral', lw=1.5)
    print('Neutral: x-axis @ 80%:', np.where(np.array(neutral_cdf) >= 0.8)[0][0])
    # ax.plot(other_cdf, color='goldenrod', label='Somewhat Problematic', lw=1.5)

    # solid lines for healthcare and opportunity
    for c in ['Healthcare', 'Opportunity']:
        counts = [exposure[p][c] for p in active_pids]
        pdf = np.array(counts) / sum(counts)
        cdf = [0]    # 0 participants = 0 ads
        cdf.extend(np.cumsum(sorted(pdf, reverse=True)))
        print(f'{c}: x-axis @ 80%:', np.where(np.array(cdf) >= 0.8)[0][0])
        
        ax.plot(cdf, label=labels[c] if c in labels else c, color=colors[c], lw=1.5, alpha=.8)

    # dashed lines for problematic ad types
    for c in ['Sensitive', 'Financial', 'Clickbait', 'Potentially Prohibited', 'Potentially Harmful']:
        counts = [exposure[p][c] for p in active_pids]
        pdf = np.array(counts) / sum(counts)
        cdf = [0]    # 0 participants = 0 ads
        cdf.extend(np.cumsum(sorted(pdf, reverse=True)))
        print(f'{c}: x-axis @ 80%:', np.where(np.array(cdf) >= 0.8)[0][0])

        ax.plot(cdf, label=labels[c] if c in labels else c, ls='--', color=colors[c], lw=1.5)        
        
    ax.grid(ls=':')
    ax.legend(loc='lower right', fontsize=9, frameon=False)
    ax.set_xlabel(f'Participants (n={len(active_pids)-1})', fontweight='bold')
    ax.set_ylabel('Fraction of Total Ads for Category (CDF)', fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # ax.xaxis.set_tick_params(labelsize=16)
    # ax.yaxis.set_tick_params(labelsize=16)

    f.set_size_inches(5, 4)
    # f.set_size_inches(3, 2.1)
    f.set_dpi(150)

    f.savefig(os.path.join(DIR,'cdf.pdf'), bbox_inches='tight')