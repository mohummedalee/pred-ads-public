# prepare demographic regression data
import pandas as pd
import utils
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
plt.rcParams["font.family"] = "Helvetica"

if __name__ == '__main__':
    # === load demographics ===
    dems_file = '../../db-processing/participant-demographics/ALLDEMS.csv'
    dems = pd.read_csv(dems_file, index_col='pid')

    # === load codes so far ===
    codes_file = '../../db-processing/ad_codes.tsv'
    codes = pd.read_csv(codes_file, sep='\t')

    # === load adid -> pid mapping ===
    pid_adid_files = ['../../db-processing/surveys/survey-1/survey1_coding_subsample.tsv',
                  '../../db-processing/surveys/survey-1/survey1_batch2_coding_subsample.tsv',
                 '../../db-processing/surveys/survey-2/survey2_coding_subsample.tsv',
                 '../../db-processing/surveys/survey-3/survey3_coding_subsample.tsv']
    pid_adid = pd.read_csv(pid_adid_files[0], sep='\t')
    for f in pid_adid_files[1:]:
        pid_adid = pd.concat([pid_adid, pd.read_csv(f, sep='\t')], ignore_index=True)
    pids = set(pid_adid['pid'])

    # === count code frequencies ===
    part_code_props = {}
    part_code_counts = {}
    for pid in pids:
        joiner = pid_adid[pid_adid['pid'] == pid]
        joined = joiner.merge(codes, how='inner', left_on='adid', right_on='adid')
        
        code_props = utils.count_code_props(dict(joined[['adid', 'codes']].values), norm=True)
        part_code_props[pid] = code_props
        
        code_counts = utils.count_code_props(dict(joined[['adid', 'codes']].values), norm=False)
        part_code_counts[pid] = code_counts

    # === prepare output for file ===
    code_order = ['Benign', 'Financial', 'Healthcare', 'Opportunity', 'Sensitive',
             'Potentially Harmful', 'Potentially Prohibited', 'Clickbait', 'CA Lawsuit', 'Political']
    allrows = []
    for i, pid in enumerate(pids):
        row = [pid.strip()]
        
        # 1. add code proportions
        for code in code_order:
            row.append(part_code_props[pid].get(code, 0))

        # 2. add demographics
        if pid not in dems.index:
            print(f'Demographics not found for {pid} -- skipping...')
            continue

        part_dems = dems.loc[pid]
        if len(part_dems.shape) > 1:
            # pick first when found multiple rows
            part_dems = part_dems.iloc[0]
        # all y/n        
        row.append(part_dems['older'])
        row.append(part_dems['woman'])        
        row.append(part_dems['black'])
        row.append(part_dems['hispanic'])
        row.append(part_dems['asian'])
        row.append(part_dems['high_ed'])
        row.append(part_dems['high_income'])

        allrows.append(row)

    # === write to file === 
    df = pd.DataFrame(allrows,
            columns=['id', 'p_benign', 'p_financial', 'p_healthcare', 'p_opportunity', 'p_sensitive',
             'p_harmful', 'p_prohibited', 'p_clickbait', 'p_lawsuit', 'p_political',
             'older', 'female', 'black', 'hispanic', 'asian', 'high_ed', 'high_income'])
    df.to_csv('dem_regression_data.csv', index=False)