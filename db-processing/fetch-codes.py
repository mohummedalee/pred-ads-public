import db_utils
import pdb
import pandas as pd

# exports codes against ad ids

if __name__ == '__main__':
    CONFIG_FILE = 'config.reader.ini'
    conn, img_path, obs_path = db_utils.connect(CONFIG_FILE)
    cursor = conn.cursor()
    cursor.execute(f"SET search_path TO 'observations';")

    # survey output row format: pid, adid, q1_resp, q2_resp, q3_resp
    cursor.execute("SELECT id, codes_analysis FROM coding;")
    res = cursor.fetchall()
    rows = []
    for id, codes in res:
        rows.append([
            id,
            ';'.join(sorted(list(codes))) if codes else None
        ])

    outfile_codes = 'ad_codes.tsv'
    df_codes = pd.DataFrame(rows, columns=['adid', 'codes'])
    df_codes.to_csv(outfile_codes, sep='\t', index=False)
    print(f'Exported codes to {outfile_codes}')