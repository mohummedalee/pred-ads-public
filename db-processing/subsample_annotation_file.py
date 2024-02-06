import json
import pandas as pd


# === CONFIG ===
full_annotation_file = 'surveys/survey-7/annotation_export_survey7.jsonl'
subsample_ids = 'surveys/survey-7/survey7_coding_subsample.tsv'
outfile = 'surveys/survey-7/annotation_export_survey7_subsampled.jsonl'
# =====

if __name__ == '__main__':
    to_keep = list(pd.read_csv(subsample_ids, sep='\t', dtype='str')['adid'])
    processed = set([])

    with open(outfile, 'w') as wh:
        with open(full_annotation_file, 'r') as fh:
            for line in fh:
                row = json.loads(line)
                adid = row["Ad ID"]
                if adid in to_keep and adid not in processed:
                    wh.write(json.dumps(row) + '\n')
                    processed.add(adid)

    print(f'Exported subsampled annotation export to {outfile}!')