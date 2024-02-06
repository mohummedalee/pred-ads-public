"""
upload codes from Angelica (or other annotators) to the observations.coding table
"""
import sys, json
from pprint import pprint
import db_utils

if __name__ == '__main__':
    # ARGS: <ANGELICA_FILE> <ALI_FILE>
    CONFIG_FILE = 'config.reader.ini'
    conn, img_path, obs_path = db_utils.connect(CONFIG_FILE)
    cursor = conn.cursor()
    cursor.execute(f"SET search_path TO 'observations';")

    # separate files for Angelica and Ali need to be specified
    # ang_file = sys.argv[1] if len(sys.argv) > 1 else '../pilot-ads-coding/angelica-coding.jsonl'
    ang_file = None
    ali_file = 'surveys/coding-files/jan-codes/reader.jsonl'
    manjot_file = 'surveys/coding-files/jan-codes/manjot.jsonl'
    devesh_file = 'surveys/coding-files/jan-codes/devesh.jsonl'
    coding = {}

    # TODO 1: implement argparse to fix this redundancy of params (https://stackoverflow.com/questions/7427101/simple-argparse-example-wanted-1-argument-3-results)
    # TODO 2: change the following to a function
    if ang_file:
        with open(ang_file, 'r') as fh:
            for line in fh:
                obj = json.loads(line)
                coding[obj['Ad ID']] = {'angelica': obj['label']}

    if ali_file:
        with open(ali_file, 'r') as fh:
            for line in fh:
                obj = json.loads(line)
                if obj['Ad ID'] in coding:
                    coding[obj['Ad ID']]['ali'] = obj['label']
                else:
                    coding[obj['Ad ID']] = {'ali': obj['label']}

    if manjot_file:
        with open(manjot_file, 'r') as fh:
            for line in fh:
                obj = json.loads(line)
                if obj['Ad ID'] in coding:
                    coding[obj['Ad ID']]['manjot'] = obj['label']
                else:
                    coding[obj['Ad ID']] = {'manjot': obj['label']}

    if devesh_file:
        with open(devesh_file, 'r') as fh:
            for line in fh:
                obj = json.loads(line)
                if obj['Ad ID'] in coding:
                    coding[obj['Ad ID']]['devesh'] = obj['label']
                else:
                    coding[obj['Ad ID']] = {'devesh': obj['label']}

    logfile = 'upload-codes-failures.txt'
    print('Uploading codes...')
    with open(logfile, 'a') as wh:
        for aid in coding:        
            try:
                codes_ali = coding[aid]['ali'] if 'ali' in coding[aid] else None
                codes_angelica = coding[aid]['angelica'] if 'angelica' in coding[aid] else None
                codes_manjot = coding[aid]['manjot'] if 'manjot' in coding[aid] else None
                codes_devesh = coding[aid]['devesh'] if 'devesh' in coding[aid] else None

                cursor.execute("""INSERT INTO observations.coding (id, codes_angelica, codes_ali, codes_manjot, codes_devesh)
                        VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE 
                        SET codes_angelica = %s, codes_ali = %s, codes_manjot = %s, codes_devesh = %s;""",
                        (aid, codes_angelica, codes_ali, codes_manjot, codes_devesh,
                        codes_angelica, codes_ali, codes_manjot, codes_devesh))
                conn.commit()
            except Exception as e:
                print("INSERT FAILURE:", e)
                wh.write(aid + '\n')
