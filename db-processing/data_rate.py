import db_utils
import csv
import datetime
from pprint import pprint

if __name__ == '__main__':
    CONFIG_FILE = 'config.reader.ini'
    conn, img_path, obs_path = db_utils.connect(CONFIG_FILE)    
    cursor = conn.cursor()
    cursor.execute(f"SET search_path TO 'observations';")    

    # find all user prolific IDs mapped to plugin install IDs
    cursor.execute(f"SELECT instid, pid FROM users WHERE pid NOT IN {db_utils.USERS_EXCLUDE};")
    res = cursor.fetchall()
    instid_map = dict(res)

    cursor.execute(f"SELECT observations.instid, observations.observed_at, observations.ad_id FROM observations\
        INNER JOIN users ON users.instid = observations.instid\
        WHERE users.pid NOT IN {db_utils.USERS_EXCLUDE};")
    res = cursor.fetchall()

    # note that this is from pid -> list, not from the install ID
    user_observations = {u: [] for u in instid_map.values()}
    user_ads = {u: {} for u in instid_map.values()}
    for row in res:
        instid, ts, ad_id = row[0], row[1], row[2]
        pid = instid_map[instid]
        user_observations[pid].append(str(ts))
        # only earliest timestamp per ad
        if ad_id not in user_ads[pid]:
            user_ads[pid][ad_id] = ts
        elif ts < user_ads[pid][ad_id]:
            user_ads[pid][ad_id] = ts

    # time sort
    for pid in user_observations:
        user_observations[pid].sort()        
    
    obs_outfile = 'observation_timestamps.txt'
    with open(obs_outfile, 'w') as wh:
        for pid in user_observations:
            wh.write(pid + '\t' + ','.join(user_observations[pid]) + '\n')
    print(f'exported observation timestamps to {obs_outfile}!')

    # also export unique ad IDs and timestamps corresponding to user
    # (to see rate of seeing unique ads)
    user_ads_outfile = 'user_ads_timestamps.tsv'
    with open(user_ads_outfile, 'w') as wh:
        writer = csv.writer(wh, delimiter='\t')
        for pid in user_ads:
            id_ts_tups = sorted([(ad_id, user_ads[pid][ad_id]) for ad_id in user_ads[pid]], key=lambda tup: tup[1])
            row = [pid]
            row.extend([str(ad_id) + ',' + str(ts) for ad_id, ts in id_ts_tups])
            writer.writerow(row)
    print(f'exported ad ID timestamps, disaggregated by user to {user_ads_outfile}!')

    # also export the earliest timestamp for each ad ID
    unique_ads = {} # ad -> first timestamp
    for row in res:        
        ts, ad_id = row[1], row[2]
        if ad_id not in unique_ads or ts < unique_ads[ad_id]:
            unique_ads[ad_id] = ts        

    unique_ads_items = sorted(unique_ads.items(), key=lambda tup: tup[1])
    ads_outfile = 'ads_timestamps.tsv'
    with open(ads_outfile, 'w') as wh:
        writer = csv.writer(wh, delimiter='\t')
        for ad_id, ts in unique_ads_items:
            writer.writerow([ad_id, str(ts)])
    print(f'exported ad timestamps to {ads_outfile}!')

    conn.close()