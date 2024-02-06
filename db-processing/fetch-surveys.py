import db_utils
import sys
import json
import base64
import pandas as pd

# exports pandas-friendly survey responses

if __name__ == '__main__':
    CONFIG_FILE = 'config.reader.ini'
    conn, img_path, obs_path = db_utils.connect(CONFIG_FILE)
    cursor = conn.cursor()
    cursor.execute(f"SET search_path TO 'observations';")

    # survey output row format: pid, adid, q1_resp, q2_resp, q3_resp
    cursor.execute("SELECT pid, survey_resp, survey_model FROM surveys WHERE survey_resp IS NOT null AND pid NOT IN %s;",
        (db_utils.USERS_EXCLUDE,))
    res = cursor.fetchall()     # survey_resp is auto-parsed into a dict 
    
    # ad_codes = {}
    # for _, _, model_enc in res:
    #     model = json.loads(base64.b64decode(model_enc['b64encoded']).decode('utf-8'))
        # model_d['pages'][2]['elements'][0]['local_coding'] has the annotator codes
        # model_d['pages'][1]['elements'][0]['name'] has the ad id
        # TODO: prepare a code map from ad_id to ad id and put in the output file

    rows = []
    for pid, response, _ in res:                
        adids = set([x.split('-')[1] for x in response.keys()])
        for aid in adids:
            # answers in pre-determined order: relevance, like, dislike
            answers = [int(response['relevance-' + aid])]
            for ques in ['like', 'dislike']:
                answers.append(';'.join(response[ques + '-' + aid]))

            rows.append([pid, aid] + answers)

    outfile_survey = 'survey_responses.tsv'
    df_surveys = pd.DataFrame(rows, columns=['pid', 'adid', 'relevance', 'like', 'dislike'])
    df_surveys.to_csv(outfile_survey, sep='\t', index=False)