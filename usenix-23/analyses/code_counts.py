import pandas as pd
import numpy as np
import pdb


tocount = ['Benign', 'Opportunity', 'Healthcare', 'Financial', 'Sensitive', 'Potentially Prohibited',
'Potentially Harmful', 'Clickbait', 'Political', 'CA Lawsuit', "Can't determine", "UNCAT"]
exclude = ["Study"]
# we have 65 UNCAT, 56 can't determine, 2405 study


if __name__ == '__main__':
    codes_file = '../../db-processing/ad_codes_transformed.tsv'
    # can also be alternatively run on ad_codes_transformed.tsv
    codes = pd.read_csv(codes_file, sep='\t')
    clean_codes = codes[~codes['codes'].str.contains('|'.join(exclude))]
        
    study_only = codes[codes['codes'].str.contains('Study')]
    study_count = study_only.shape[0]
    print('='*5, f'Study Occurences, total: {study_count}', '='*5)
    study_variations = list(study_only['codes'].value_counts().items())
    for var, cnt in study_variations:
        print(var, cnt, f'({round(cnt/study_count * 100, 2)} %)')
    
    print('\n', '='*5, 'Code Counts (sans Study)', '='*5)
    N = clean_codes.shape[0]
    for c in tocount:
        # pdb.set_trace()
        curr = clean_codes[clean_codes['codes'].str.contains(c)].shape[0]
        print(c, curr, round(curr/N * 100, 2), '%')
