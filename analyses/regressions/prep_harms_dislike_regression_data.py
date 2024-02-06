"""
Prepare regression file for modeling dislike (yes/no)
dislike ~ opportunity + healthcare + financial + prohibited + harmful + clickbait + (1|pid)
"""
import csv
import pdb
import pandas as pd
import utils

OUTFILE = 'ad_dislike_data_harms.csv'

# Jul 18: adding new codes, removing Manjot's ads from survey #4
# which are erroneously annotated and currently being fixed
# exclude_files = ['../../db-processing/surveys/survey-2/survey2_ids.txt']
exclude_files = []
EXCLUDE_IDS = []
for fname in exclude_files:
    with open(fname) as fh:
        EXCLUDE_IDS.extend([int(i.strip()) for i in fh.readlines()])

# dislike reasons that are directly describe harmful ads
scam_dislike_reasons = set(["unclear", "pushy", "clickbait", "scam", "uncomfortable"])
# reasons for disliking that have little to do with harms
other_dislike_reasons = set(["irrelevant", "dislike-product", "dislike-design", "political", "dislike-advertiser"])

HEADER = ['relevance', 'scam_dislike', 'other_dislike', "general_like", "general_dislike",
    "sensitive", "prohibited", "harmful", "clickbait", "benign", "code_other", "pid"]
    
if __name__ == '__main__':
    survey_file = '../../db-processing/survey_responses.tsv'
    codes_file = '../../db-processing/ad_codes.tsv'
    survey_codelist = ["Sensitive", "Potentially Prohibited", "Potentially Harmful", "Clickbait"]

    survey = pd.read_csv(survey_file, sep='\t')
    codes = pd.read_csv(codes_file, sep='\t')    
    adid_codes = dict(zip(codes['adid'], [r.split(';') for r in codes['codes']]))

    # merge survey and codes for easy lookup
    survey_codes = survey.merge(codes, 'inner', 'adid')

    allrows = []
    for i in range(survey_codes.shape[0]):
        row = survey_codes.iloc[i]
        relevance = int(row['relevance'])
        adid = row['adid']; pid = row['pid']
        if adid in EXCLUDE_IDS:
            continue
        ad_codes = adid_codes[adid]
        part_dislike_reasons = set([utils.short_names[r] for r in row['dislike'].split(';')])
        part_like_reasons = set([utils.short_names[r] for r in row['like'].split(';')])

        filerow = [relevance]
        # scam dislike = yes/no
        filerow.append(int(len(part_dislike_reasons & scam_dislike_reasons) > 0))
        # other dislike reasons = yes/no
        filerow.append(int(len(part_dislike_reasons & other_dislike_reasons) > 0))

        # TODO: add boolean for general like/dislike
        general_dislike = "dont-like" in part_like_reasons
        general_like = "dont-dislike" in part_dislike_reasons
        filerow.extend([int(general_like), int(general_dislike)])
        
        # `other` = non benign and not any of the types in `survey_codelist`
        if 'Benign' in ad_codes:
            other = False
            benign = True
        else:
            other = True
            benign = False

        for c in survey_codelist:
            if c in ad_codes:
                # ad is not anything other than prohibited, harmful, clickbait, sensitive
                other = False
            filerow.append(int(c in ad_codes))        
        filerow.append(int(benign))
        filerow.append(int(other))
        filerow.append(pid)

        allrows.append(filerow)
    
    with open(OUTFILE, 'w') as fh:
        writer = csv.writer(fh)
        writer.writerow(HEADER)
        writer.writerows(allrows)
    print(f'Exported regression data to {OUTFILE}')
