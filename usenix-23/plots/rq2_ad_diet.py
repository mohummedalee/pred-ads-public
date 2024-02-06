"""
Extracted from analyses/analyses_achtung/rq2/distribution_disparities_sec52.ipynb
"""
import utils
import sys
import os
import pdb

import pandas as pd
import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import seaborn as sns

DATA_DIR = 'data/'
labels = {'Potentially Harmful': 'Deceptive', 'Financial': 'Sensitive: Financial', 'Sensitive': 'Sensitive: Other'}
colors = {'Financial': 'tab:green', 'Problematic (all together)': 'maroon', 'Problematic': 'maroon',          
        'Benign': 'dimgray', 'Potentially Harmful': 'tab:red', 
        'Clickbait': 'tab:orange', 'Potentially Prohibited': 
        'tab:purple', 'Sensitive': 'hotpink',
        'Healthcare': 'tab:blue', 'Opportunity': '#33297a'}    # copied from Piotr

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

    # === count exposure frequencies ===
    # all codes separately
    exposure, ann_ads_count = utils.measure_exposure(active_pids, adid_codes, pid_adid, pid_adid_freqs)
    # count grouped exposure
    harmful, non_harmful = 'harmful', 'non_harmful'
    groups = {
        'Potentially Harmful': harmful, 'Sensitive': harmful, 'Financial': harmful,
        'Clickbait': harmful, 'Potentially Prohibited': harmful, 'Benign': non_harmful,
        'Opportunity': 'other', 'Healthcare': 'other'
    }
    grouped_exposure, _ = utils.measure_exposure(active_pids, adid_codes, pid_adid, pid_adid_freqs, groups)
    total_vals = [ann_ads_count[p] for p in active_pids if ann_ads_count[p] > 0]
    
    # arrays of counts for plotting    
    harmful_counts = [grouped_exposure[p][harmful] for p in active_pids if ann_ads_count[p] > 0]
    neutral_counts = [exposure[p]['Benign'] for p in active_pids if ann_ads_count[p] > 0]
    healthcare_counts = [exposure[p]['Healthcare'] for p in active_pids if ann_ads_count[p] > 0]
    opportunity_counts = [exposure[p]['Opportunity'] for p in active_pids if ann_ads_count[p] > 0]

    # compute individual exposure fractions
    neutral_expos_fracs = np.array(neutral_counts) / np.array(total_vals)
    harmful_expos_fracs = np.array(harmful_counts) / np.array(total_vals)
    healthcare_expos_fracs = np.array(healthcare_counts) / np.array(total_vals)
    opportunity_expos_fracs = np.array(opportunity_counts) / np.array(total_vals)

    # preprocess into dataframe to work with seaborn
    df_data = {'problematic': harmful_expos_fracs, 'neutral': neutral_expos_fracs}
    plot_df = []
    for name, vals in df_data.items():
        for v in vals:
            plot_df.append([name, v])        
    plot_df = pd.DataFrame(plot_df, columns=['adtype', 'fraction_diet'])

    f, ax = plt.subplots()
    sns.histplot(ax=ax, data=plot_df, x="fraction_diet", kde=True, bins=25,
                hue="adtype", edgecolor='white',
                palette={'neutral': colors['Benign'], 'problematic': colors['Problematic'],
                        'other': colors['Healthcare']})

    ax.grid(ls=':')
    ax.set_axisbelow(True)
    ax.set_xlabel("Fraction of Participant's Ad Diet", fontweight='bold')
    ax.set_ylabel("Frequency", fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    legend = ax.get_legend()
    texts = legend.get_texts()
    texts[0].set_text('Problematic')
    texts[1].set_text('Neutral')
    legend.set_title('Ad Category')

    # how many people have >20% problematic in their ad diet?
    print('>20% problematic in ad diet:',
        plot_df[(plot_df['adtype'] == 'problematic') & (plot_df['fraction_diet'] >= 0.2)].shape)

    f.set_size_inches(5, 4)
    f.savefig(os.path.join(DIR, 'rq2_exposure_regen.pdf'), bbox_inches='tight')

    # ========== fine-grained plot for appendix ===============
    # finegrained DF
    df_data_fg = {
        'neutral': neutral_expos_fracs,
        'healthcare': healthcare_expos_fracs,
        'opportunity': opportunity_expos_fracs    
    }
    df_data_fg['deceptive'] = np.array([exposure[p]['Potentially Harmful'] for p in active_pids if ann_ads_count[p] > 0]) / total_vals
    df_data_fg['prohibited'] = np.array([exposure[p]['Potentially Prohibited'] for p in active_pids if ann_ads_count[p] > 0]) / total_vals
    df_data_fg['clickbait'] = np.array([exposure[p]['Clickbait'] for p in active_pids if ann_ads_count[p] > 0]) / total_vals
    df_data_fg['sensitive'] = np.array([exposure[p]['Sensitive'] for p in active_pids if ann_ads_count[p] > 0]) / total_vals
    df_data_fg['financial'] = np.array([exposure[p]['Financial'] for p in active_pids if ann_ads_count[p] > 0]) / total_vals

    plot_df_fg = []
    for name, vals in df_data_fg.items():
        for v in vals:
            plot_df_fg.append([name, v])        
    plot_df_fg = pd.DataFrame(plot_df_fg, columns=['adtype', 'fraction_diet'])
    plot_df_fg = plot_df_fg.dropna()

    f, ax = plt.subplots()
    # ==== filled bar plot =====
    order = ['neutral', 'healthcare', 'opportunity', 'sensitive', 'financial', 'clickbait', 'prohibited', 'deceptive'][::-1]
    sns.histplot(ax=ax, data=plot_df_fg, x="fraction_diet", bins=25,
                hue="adtype", fill=True, kde=False, alpha=.5, element="step",
                palette={'neutral': colors['Benign'], 'healthcare': colors['Healthcare'], 'opportunity': colors['Opportunity'],
                        'deceptive': colors['Potentially Harmful'], 'prohibited': colors['Potentially Prohibited'],
                        'clickbait': colors['Clickbait'], 'financial': colors['Financial'],
                        'sensitive': colors['Sensitive']
                        },
                # least to most skewed
                hue_order=order)    

    ax.grid(ls=':')
    ax.set_axisbelow(True)
    ax.set_xlabel("Fraction of Participant's Ad Diet", fontweight='bold')
    ax.set_ylabel("Frequency", fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.set_xlim(0, 1)

    legend = ax.get_legend()
    texts = legend.get_texts()
    for i, t in enumerate(texts):
        t.set_text(order[i].title())
    # texts[0].set_text('Problematic')
    # texts[1].set_text('Neutral')
    legend.set_title('Ad Category')

    # f.set_size_inches(7, 5)
    # 4x3 fits in appendix
    # f.set_size_inches(4, 3)
    f.set_size_inches(4.5, 3.5)
    f.savefig(os.path.join(DIR, 'rq2_exposure_disambiguated.pdf'), bbox_inches='tight')