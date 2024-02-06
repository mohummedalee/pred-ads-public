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

    # ad_id -> [list of PIDs]
    cursor.execute(f"SELECT observations.ad_id, users.pid FROM users\
        INNER JOIN observations ON observations.instid = users.instid\
        WHERE pid NOT IN {db_utils.USERS_EXCLUDE};")
    res = cursor.fetchall()
    adid_to_pid = collections.defaultdict(lambda: set())
    for ad_id, pid in res:
        adid_to_pid[ad_id].add(pid)

    outfile = 'adid_pid.tsv'
    with open(outfile, 'w') as fh:
        writer = csv.writer(fh, delimiter='\t')
        for ad_id, pids in adid_to_pid.items():
            writer.writerow([ad_id, ','.join(list(pids))])
    print(f'Ad ID -> PIDs mapping exported to {outfile}!')    