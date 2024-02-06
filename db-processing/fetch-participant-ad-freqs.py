import db_utils
import pdb
import pandas as pd

# exports frequency of how many times each participant_id, ad_id pair occurs in pid_adid

if __name__ == '__main__':
    CONFIG_FILE = 'config.reader.ini'
    conn, img_path, obs_path = db_utils.connect(CONFIG_FILE)
    cursor = conn.cursor()
    cursor.execute(f"SET search_path TO 'observations';")

    # survey output row format: pid, age, income, education, ethnicity
    cursor.execute("select *, count(*) from pid_adid group by pid, id order by count(*) desc;")
    res = cursor.fetchall()
    rows = []
    for pid, adid, freq in res:        
        rows.append([pid, str(adid), freq])    

    outfile = 'participant_ad_freqs.tsv'
    df_codes = pd.DataFrame(rows, columns=['pid', 'adid', 'frequency'])
    df_codes.to_csv(outfile, sep='\t', index=False)
    print(f'Exported participant demographics to {outfile}.')