"""
Prepare 1st regression file for modeling dislike (yes/no)
dislike ~ opportunity + healthcare + financial + prohibited + harmful + clickbait + (1|pid)

Prepare 2nd regression file for understanding kind of dislike associated with code

"""
import csv
import pdb
import pandas as pd
import utils
import pdb

OUTFILE = 'ad_dislike_data.csv'
OUTFILE_FULL = 'ad_dislike_data_full.csv'   # TODO: includes all reasons for dislike
scam_dislike_reasons = set(["unclear", "pushy", "clickbait", "scam", "uncomfortable"])
scam_dislike_exp_reasons = utils.dislike_reasons - set(["political", "dislike-design", "irrelevant"])

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

    allrows = []
    allrows_full = []
    for i in range(survey_codes.shape[0]):
        row = survey_codes.iloc[i]
        adid = row['adid']; pid = row['pid']
        ad_codes = adid_codes[adid]
        
        part_dislike_reasons = set([utils.short_names[r] for r in row['dislike'].split(';')])
        part_like_reasons = set([utils.short_names[r] for r in row['like'].split(';')])

        # add all reasons here (for the full file)
        # dont_dislike = int("dont-dislike" in part_dislike_reasons)
        general_dislike = int("dont-like" in part_like_reasons)
        filerow_full = [general_dislike]
        filerow_full.extend([int(r in part_dislike_reasons) for r in utils.dislike_reasons])

        # capture different kinds of dislike (for the summary file)
        general_dislike = int("dont-like" in part_like_reasons)        
        scam_dislike = int(len(part_dislike_reasons & scam_dislike_reasons) > 0)
        scam_dislike_exp = int(len(part_dislike_reasons & scam_dislike_exp_reasons) > 0)
        any_dislike_reason = int(len(part_dislike_reasons & utils.dislike_reasons) > 0)
        filerow = [general_dislike, scam_dislike, scam_dislike_exp, any_dislike_reason]

        # identify codes for each ad
        for c in survey_codelist:
            filerow.append(int(c in ad_codes))
            filerow_full.append(int(c in ad_codes))

        filerow.append(pid); filerow_full.append(pid)
        allrows.append(filerow); allrows_full.append(filerow_full)
            
    header = ['general_dislike', 'scam_dislike', 'scam_dislike_exp', 'any_dislike_reason',
        'opportunity', 'healthcare', 'sensitive', 'financial', 'prohibited', 'harmful', 'clickbait', 'political',
        'pid']
    with open(OUTFILE, 'w') as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(allrows)
    print(f'Exported regression data to {OUTFILE}')

    header_full = ["dislike_general", "dislike_unclear", "dislike_irrelevant", "dislike_pushy", "dislike_clickbait",
        "dislike_scam", "dislike_product", "dislike_design", "dislike_uncomfortable",
        "dislike_advertiser", "dislike_political",
        # ad codes
        'opportunity', 'healthcare', 'sensitive', 'financial', 'prohibited',
        'deceptive', 'clickbait', 'neutral', 'pid']
    with open(OUTFILE_FULL, 'w') as fh:
        writer = csv.writer(fh)
        writer.writerow(header_full)
        writer.writerows(allrows_full)
    print(f"Exported full dislike reasons to {OUTFILE_FULL}")