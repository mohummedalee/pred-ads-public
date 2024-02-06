"""
Binarize ad coding data
"""
import csv
import pandas as pd
import utils

OUTFILE = 'ad_codes_binary.csv'

# Jul 18: adding new codes, removing Manjot's ads from survey #4
# which are erroneously annotated and currently being fixed

survey_codelist = ["Opportunity", "Healthcare", "Sensitive", "Financial", "Potentially Prohibited",
    "Potentially Harmful", "Clickbait"]  # benign = all off
# header for OUTFILE
outfile_header = ['adid', 'opportunity', 'healthcare', 'sensitive', 'financial',
'prohibited', 'harmful', 'clickbait']

if __name__ == '__main__':
    codes_file = '../../db-processing/ad_codes.tsv'    
    exclude_file = '../../db-processing/surveys/survey-4/manjot_ids.txt'
    with open(exclude_file) as fh:
        EXCLUDE_IDS = [int(i.strip()) for i in fh.readlines()]

    codes = pd.read_csv(codes_file, sep='\t')
    adid_codes = dict(zip(codes['adid'], [r.split(';') for r in codes['codes']]))

    allrows = []    
    for adid in adid_codes:
        # temporarily removing Manjot's survey-4 (february) codes
        if adid in EXCLUDE_IDS:
            continue
        ad_codes = adid_codes[adid]        
        filerow = [str(adid)]

        for c in survey_codelist:
            filerow.append(int(c in ad_codes))        
        allrows.append(filerow)
    
    with open(OUTFILE, 'w') as fh:
        writer = csv.writer(fh)
        writer.writerow(outfile_header)
        writer.writerows(allrows)
    print(f'Exported regression data to {OUTFILE}')
