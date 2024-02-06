"""
prepares annotation data for upload to doccano, each row is of the form:
{"text": "ads.message", "advertiser": "ads.advertiser", "ID": "ads.id"}
"""
import json

import db_utils
import pandas as pd
from html_parser import DBHTMLParser

# ====== CONFIGURATION ======
# consolidation_file = 'angelica-jul2.jsonl'
ann_config_f = 'ann_conf.json'
with open(ann_config_f, 'r') as fh:
    ann_config = json.loads(fh.read())
    
consolidation_file = None
# time querying: https://popsql.com/learn-sql/postgresql/how-to-query-date-and-time-in-postgresql
start_date = ann_config['start_date']
end_date = ann_config['end_date']
user_whitelist = ann_config['user_whitelist']
user_blacklist = None
if 'user_blacklist' in ann_config:
    user_blacklist = ann_config['user_blacklist']
pid_adid_file = ann_config['pid_adid_file']     # pid_adid_file is for outputs, no need to create beforehand
outfile = ann_config['outfile']
# ============

if __name__ == '__main__':
    # if consolidation needs to be done from a previous round of labeling
    prev_labels = {}
    if consolidation_file:
        with open(consolidation_file, 'r') as fh:
            for line in fh:
                pt = json.loads(line)
                ad_id = str(pt['Ad ID'])
                prev_labels[ad_id]= pt['label'] 


    CONFIG_FILE = 'config.reader.ini'
    conn, img_path, obs_path = db_utils.connect(CONFIG_FILE)
    cursor = conn.cursor()
    cursor.execute(f"SET search_path TO 'observations';")    
    
    if user_whitelist:        
        USERS_INCLUDE = tuple([p.strip() for p in open(user_whitelist).readlines()])
        cursor.execute(f"SELECT DISTINCT ads.id, ads.message, ads.advertiser, ads.html, ads.page_id, users.pid, ads.images FROM ads\
            INNER JOIN observations ON observations.ad_id = ads.id\
            INNER JOIN users on observations.instid=users.instid\
            WHERE users.pid IN {USERS_INCLUDE} AND observed_at between '{start_date}' and '{end_date}';")
    elif user_blacklist:
        USERS_EXCLUDE = tuple([p.strip() for p in open(user_blacklist).readlines()])
        cursor.execute(f"SELECT DISTINCT ads.id, ads.message, ads.advertiser, ads.html, ads.page_id, users.pid, ads.images FROM ads\
            INNER JOIN observations ON observations.ad_id = ads.id\
            INNER JOIN users on observations.instid=users.instid\
            WHERE users.pid NOT IN {USERS_EXCLUDE} AND observed_at between '{start_date}' and '{end_date}';")
    else:
        cursor.execute(f"SELECT DISTINCT ads.id, ads.message, ads.advertiser, ads.html, ads.page_id, users.pid, ads.images FROM ads\
            INNER JOIN observations ON observations.ad_id = ads.id\
            INNER JOIN users on observations.instid=users.instid\
            WHERE users.pid NOT IN {db_utils.USERS_EXCLUDE} AND observed_at between '{start_date}' and '{end_date}';")    
    res = cursor.fetchall()
    user_ads = []
    export = []
    for row in res:
        # pull out exact linked URL from HTML
        parser = DBHTMLParser(row[3])
        parser.linkedURL()

        pid = row[5]
        ad_id = str(row[0])
        note = 'None'
        if len(row[-1]) == 1 and parser.is_image_ad:
            note = 'Standard'
        elif len(row[-1]) == 0:
            note = 'Video Ad'
        elif len(row[-1]) > 1:
            note = 'Multi-Image'
        elif 'http' in ''.join(row[-1]):
            note = 'Missing Image'        
        
        pt = {
            "text": f"ID: {ad_id} == ALL TEXT ==\n\n" + row[1],
            "advertiser": row[2],
            "Page ID": str(row[4]),
            "URL": parser.url,
            "Ad ID": ad_id,
            "Note": note
        }
        if len(prev_labels) and ad_id in prev_labels:
            pt['label'] = prev_labels[ad_id]

        user_ads.append([pid, ad_id])
        export.append(pt)
    
    with open(outfile, 'w') as wh:
        for pt in export:
            wh.write(json.dumps(pt) + '\n')
    print(f'annotation data exported to {outfile}!')
        
    user_ads = pd.DataFrame(user_ads, columns=['pid', 'adid'])
    user_ads.to_csv(pid_adid_file, sep='\t', index=False)
    print(f'PID to ad ID mapping exported to {pid_adid_file}!')

    conn.close()