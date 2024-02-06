"""
export message column from ads table, and the PIDs alongside as well
"""
import collections
import csv
import pandas as pd
from pprint import pprint

import db_utils


if __name__ == '__main__':
    CONFIG_FILE = 'config.reader.ini'
    conn, img_path, obs_path = db_utils.connect(CONFIG_FILE)
    cursor = conn.cursor()
    cursor.execute(f"SET search_path TO 'observations';")

    # ad_id -> message
    cursor.execute(f"SELECT DISTINCT ads.id, ads.message FROM ads\
        INNER JOIN observations ON observations.ad_id = ads.id\
        INNER JOIN users on observations.instid=users.instid\
        WHERE users.pid NOT IN {db_utils.USERS_EXCLUDE};")
    res = cursor.fetchall()
    df = pd.DataFrame(res)
    df.columns = ['ad_id', 'message']
    outfile = 'adid_message.tsv'
    df.to_csv(outfile, sep='\t', index=False)
    print(f'Ad ID -> message mapping exported to {outfile}!')
    conn.close()