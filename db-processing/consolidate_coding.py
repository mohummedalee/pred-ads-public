"""
given the multiple annotators, we have, consolidate everyone's annotations from the DB into a single column
final word on each ad should be in `codes_analysis` column in the coding table
order of code preference/consolidation: Angelica -> Ali -> Devesh -> Manjot
"""
import db_utils


if __name__ == '__main__':
    avoid_file = 'harmful-cleanup/harmful_ids.csv'
    avoid = [aid.strip() for aid in open(avoid_file).readlines()]

    CONFIG_FILE = 'config.reader.ini'
    conn, img_path, obs_path = db_utils.connect(CONFIG_FILE)
    cursor = conn.cursor()
    cursor.execute(f"SET search_path TO 'observations';")

    cursor.execute("SELECT id, codes_angelica, codes_ali, codes_devesh, codes_manjot FROM coding;")
    res = cursor.fetchall()
    consolidated = {}
    for id, codes_angelica, codes_ali, codes_devesh, codes_manjot in res:
        if str(id) in avoid:
            # don't consolidate, these are manually cleaned up potentially harmful codes
            continue
        if codes_angelica:
            consolidated[id] = codes_angelica
        elif codes_ali:
            consolidated[id] = codes_ali
        elif codes_devesh:
            consolidated[id] = codes_devesh
        elif codes_manjot:
            consolidated[id] = codes_manjot

    logfile = 'consolidation-failures.txt'
    print(len(consolidated))
    print('Consolidating codes in codes_analysis column...')
    with open(logfile, 'a') as wh:
        for aid in consolidated:
            try:                
                cursor.execute("""INSERT INTO observations.coding (id, codes_analysis)
                        VALUES (%s, %s) ON CONFLICT (id) DO UPDATE
                        SET codes_analysis = %s;""",
                        (aid, consolidated[aid], consolidated[aid]))
                conn.commit()
            except Exception as e:
                print("INSERT FAILURE:", e)
                wh.write(aid + '\n')

    