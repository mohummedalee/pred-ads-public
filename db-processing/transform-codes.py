"""
convert codes in ad_code.tsv into mutually exclusive category accordint to precedence:
    prohibited > deceptive > clickbait > financial = sensitive > opportunity > healthcare > neutral
"""
import os, sys
import pandas as pd
import csv
import pdb

DATA_DIR = '../db-processing'
EXCLUDE = ['Study', "UNCAT", "Can't determine, return to this one", "Political", "CA Lawsuit"]
PRECEDENCE = {c: i for i, c in 
    enumerate(['Potentially Prohibited', 'Potentially Harmful',
    'Clickbait', 'Financial', 'Sensitive', 'Opportunity', 'Healthcare', 'Benign',
    # auxiliary codes, only for internal organization
    'Drug'])
}


def transform_codes(code_arr):
    global PRECEDENCE

    if len(set(EXCLUDE) & set(code_arr)) >= 1:
        # has one of the codes that should be excluded
        return None
    
    codes_sorted = sorted(code_arr, key=lambda c: PRECEDENCE[c])
    return codes_sorted    


if __name__ == '__main__':    
    df = pd.read_csv(os.path.join(DATA_DIR, 'ad_codes.tsv'), sep='\t', index_col=False)
    export = []     # [adid, codes] that have been transformed

    for row in df.itertuples(index=False):
        adid, codestr = row.adid, row.codes
        code_trans = transform_codes(codestr.split(';'))
        # print(adid, codestr, code_trans)        
        if code_trans:
            newcode = code_trans[0]     # one code per ad
            export.append([adid, newcode])            
        
    OUTFILE = 'ad_codes_transformed.tsv'    
    df_export = pd.DataFrame(export, columns=['adid', 'codes'])
    df_export.to_csv(OUTFILE, index=False, sep='\t')
    print(f'Exported tranformed, mutually exclusive ad codes to {OUTFILE}! (n={len(export)})')