"""
Put both like and dislike reasons into one file, how it likely should have been from the start
"""
import csv
import pdb
import pandas as pd
import utils
import pdb

OUTFILE_FULL = 'survey_data_full.csv'

# NOTE: NEVER iterate over sets ever again, it doesn't guarantee order
dislike_reasons = ["unclear", "irrelevant", "pushy", "clickbait",
    "scam", "dislike-product", "dislike-design", "uncomfortable",
    "dislike-advertiser", "political"]
like_reasons = ["amusing", "like-design", "interested", "clear", "trust-ad",
    "trust-advertiser", "useful", "filterable"]

if __name__ == '__main__':
    survey_file = '../../db-processing/survey_responses.tsv'
    codes_file = '../../db-processing/ad_codes_transformed.tsv'
    survey_codelist = ["Opportunity", "Healthcare", "Sensitive", "Financial", "Potentially Prohibited",
        "Potentially Harmful", "Clickbait", "Benign"]        

    survey = pd.read_csv(survey_file, sep='\t')
    codes = pd.read_csv(codes_file, sep='\t')
    # change to use ad_codes_transformed, only one code per ad
    adid_codes = dict(zip(codes['adid'], codes['codes']))

    # merge survey and codes for easy lookup
    survey_codes = survey.merge(codes, 'inner', 'adid')    
    # 984 rows that don't match are "Study" in codes, which were removed from ad_codes_transformed.tsv

    allrows = []
    for i in range(survey_codes.shape[0]):
        row = survey_codes.iloc[i]
        adid = row['adid']; pid = row['pid']
        ad_codes = adid_codes[adid]
        
        part_dislike_reasons = set([utils.short_names[r] for r in row['dislike'].split(';')])
        part_like_reasons = set([utils.short_names[r] for r in row['like'].split(';')])
        relevance = int(row['relevance'])

        # add all dislike reasons first (part_dislike_reasons)
        general_dislike = int("dont-like" in part_like_reasons)
        filerow_full = [general_dislike]
        filerow_full.extend([int(r in part_dislike_reasons) for r in dislike_reasons])        

        # add all like reasons (part_like_reasons)
        general_like = int("dont-dislike" in part_dislike_reasons)
        filerow_full.append(general_like)
        filerow_full.extend([int(r in part_like_reasons) for r in like_reasons])

        # identify codes for each ad
        for c in survey_codelist:
            filerow_full.append(int(c == ad_codes))

        filerow_full.append(relevance)
        filerow_full.append(pid)
        allrows.append(filerow_full)
            
    header = [
        # === dislike reasons ===
        "dislike_general", "dislike_unclear", "dislike_irrelevant", "dislike_pushy", "dislike_clickbait", "dislike_scam",
        "dislike_product", "dislike_design", "dislike_uncomfortable", "dislike_advertiser", "dislike_political",
        # === like reasons ===
        "like_general", "like_amusing", "like_design", "like_interested", "like_clear", 
        "like_trust_ad", "like_trust_advertiser", "like_useful", "like_filterable", 
        # === ad codes ===        
        'opportunity', 'healthcare', 'sensitive', 'financial', 'prohibited', 'deceptive', 'clickbait', 'neutral',
        # finally, relevance and PID
        'relevance', 'pid'
    ]
    with open(OUTFILE_FULL, 'w') as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(allrows)
    print(f'Exported regression data to {OUTFILE_FULL} (n={len(allrows)})')