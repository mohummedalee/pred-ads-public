"""
export the full json for each ad's targeting to tsv for analyses, better than constant DB querying
"""
import db_utils


if __name__ == '__main__':
    CONFIG_FILE = 'config.reader.ini'
    conn, img_path, obs_path = db_utils.connect(CONFIG_FILE)
    cursor = conn.cursor()
    cursor.execute(f"SET search_path TO 'observations';")

    cursor.execute(f"SELECT targetings.ad_id, full_json FROM targetings\
        INNER JOIN observations on targetings.ad_id::bigint=observations.ad_id\
        WHERE observations.instid NOT IN {db_utils.INSTID_EXCLUDE};")
    res = cursor.fetchall()

    targetings = dict(res)
    outfile = 'ad-targetings.tsv'
    with open(outfile, 'w') as fh:
        for ad_id, json_str in targetings.items():
            fh.write(str(ad_id) + '\t' + json_str + '\n')

    print(f'Ad ID -> targetings exported to {outfile}!')
    conn.close()
