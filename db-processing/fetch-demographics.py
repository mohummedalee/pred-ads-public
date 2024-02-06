import db_utils
import pdb
import pandas as pd

# exports codes against ad ids

if __name__ == '__main__':
    CONFIG_FILE = 'config.reader.ini'
    conn, img_path, obs_path = db_utils.connect(CONFIG_FILE)
    cursor = conn.cursor()
    cursor.execute(f"SET search_path TO 'observations';")

    # survey output row format: pid, age, income, education, ethnicity
    cursor.execute("SELECT pid, dems FROM dems;")
    res = cursor.fetchall()
    rows = []
    for pid, dems in res:        
        rows.append([pid, dems['age'], dems['income'], dems['education'], dems['ethnicity']])

    outfile_dems = 'participant_dems.tsv'
    df_codes = pd.DataFrame(rows, columns=['pid', 'age', 'income', 'education', 'ethnicity'])
    df_codes.to_csv(outfile_dems, sep='\t', index=False)
    print(f'Exported participant demographics to {outfile_dems}.')