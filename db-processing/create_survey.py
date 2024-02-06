import db_utils as dbu
from collections import defaultdict
import datetime
import json
import pdb
import random
import base64


def setup():
    conn, img_path, obs_path = dbu.connect('config.reader.ini')
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("SET search_path TO 'observations';")
    return cursor, img_path, obs_path


# returns PID -> [adid, adid, ...] mapping between start and end dates
def get_ads_per_user(cursor, start_date = '1990-01-01', end_date = '2022-12-31'):
    # a few users apparently re-installed the plugin, leading to multiple instids for their submissions -- need complicated join
    cursor.execute('''SELECT pid, users.instid, ads.id, ads.images FROM ads
        INNER JOIN observations ON observations.ad_id=ads.id
        RIGHT JOIN users ON users.instid=observations.instid
        WHERE observed_at BETWEEN %s AND %s;''', (start_date, end_date))
    result = defaultdict(set)
    allads = cursor.fetchall()
    # start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    # end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    for ad in allads:
        if len(ad[3]) and 'http' not in ''.join(ad[3]):
            # only ads with images should be put in survey
            result[ad[0]].add(ad[2])
    return dict(result)


def get_coding(cursor):
    # TODO: move this to use `codes_analysis`
    cursor.execute("SELECT id, codes_angelica, codes_ali, codes_devesh, codes_manjot from coding;")
    coding = cursor.fetchall()
    result = {}
    for id, codes_angelica, codes_ali, codes_devesh, codes_manjot in coding:
        # Prefer Angelica's codes, but if not available, pick up Ali's codes, and so on...
        if codes_angelica:
            result[id] = codes_angelica
        elif codes_ali:
            result[id] = codes_ali
        elif codes_devesh:
            result[id] = codes_devesh
        elif codes_manjot:
            result[id] = codes_manjot
    return result


def get_pids(cursor):
    cursor.execute("SELECT * FROM users;")
    return {val[0]: val[2] for val in cursor.fetchall()}    


#def sample_ads(user_ads, coding, ad_selection = {'Financial': 5, 'Suspicious': 5, 'Benign': 5}):
#    random.seed(1)
#    used = set()
#    random.shuffle(sorted(list(user_ads)))
#    counter = defaultdict(list)
#    result = []
#    for ad in user_ads:
#        for category in ad_selection:
#            if ad in coding and category in coding[ad] and len(counter[category]) <= ad_selection[category] and ad not in used:
#                counter[category].append(ad)
#                result.append(ad)
#                used.add(ad)
#    return result


def sample_ads(user_ads, coding, ad_selection = [], total=25):
    random.seed(1)
    used = set()
    random.shuffle(sorted(list(user_ads)))

    # create a lookup from category to the set of ads that match it
    cat_to_adid = defaultdict(set)
    for ad in user_ads:
        if ad in coding:
            for category in coding[ad]:                
                cat_to_adid[category].add(ad)
                # treat p. prohibited and p. harmful as similar for the purpose of the survey -- mention harmful in config
                if category == "Potentially Prohibited":
                    cat_to_adid["Potentially Harmful"].add(ad)

    # add one ad from each category until we get the right number of ads
    possible_cats = [True] * len(ad_selection)
    while len(used) < total and any(possible_cats):
        for i, category in enumerate(ad_selection):
            if len(cat_to_adid[category]) > 0:
                sample = cat_to_adid[category].pop()
                while (sample in used) and (len(cat_to_adid[category]) > 0):
                    # draw different ad not already in survey
                    sample = cat_to_adid[category].pop()
                used.add(sample)

                # do we have enough?
                if len(used) >= total:
                    break
            else:
                possible_cats[i] = False
    
    return used

import copy

def generate_survey_json(user_ads, survey_header, survey_question, coding):
    survey = copy.deepcopy(survey_header)
    # shuffle order of answer options (except the final "I like/don't like this ad" option)
    for i in [2, 3]:
        all_choices = copy.deepcopy(survey_question['elements'][i]["choices"])
        shuf_choices = copy.deepcopy(all_choices[:-1])
        random.shuffle(shuf_choices)
        survey_question['elements'][i]["choices"] = shuf_choices + [all_choices[-1]]

    for ad in user_ads:
        ques = json.loads(json.dumps(survey_question).replace('ADID',str(ad)))
        # look up codes from coding and add to image element of form
        ques['elements'][0]['local_coding'].append(coding[ad])
        survey['pages'].append(ques)
    return survey

import string
import random
def get_token(length=64):
    return ''.join(random.SystemRandom().choice(string.ascii_letters) for _ in range(length))

def insert_survey(survey, pid, cursor, survey_no=1):
    encoded = {'b64encoded': str(base64.b64encode(json.dumps(survey).encode('utf-8')), 'utf-8')}
    cursor.execute(f'''
        INSERT INTO 
            surveys(pid, survey_model, curr_token, survey_no)
        VALUES('{pid}', '{json.dumps(encoded)}', '{get_token()}', {survey_no})
    ''')

def main(config = None):
    if config is None:
        config = json.loads(open('config_0.json').read())
        
    cursor, img_path, obs_path = setup()
    ads_per_user = get_ads_per_user(cursor, start_date = config['start_date'], end_date = config['end_date'])
    coding = get_coding(cursor)
    # pids = get_pids(cursor)
    if config['pid_whitelist']:
        fh = open(config['pid_whitelist'], 'r')
        pid_whitelist = tuple([p.strip() for p in fh.readlines()])    
        surveys = {}
        for user in pid_whitelist:
            if user in ads_per_user:
                surveys[user] = sample_ads(ads_per_user[user], coding, ad_selection=config['ad_selection'], total=config['sample_size'])
            else:
                print(f'No ads for {user} between {config["start_date"]} and {config["end_date"]}!')
    else:
        surveys = {user: sample_ads(ads_per_user[user], coding, ad_selection=config['ad_selection'], total=config['sample_size'])\
            for user in ads_per_user}
        
    print('Survey lengths:', {u: len(surveys[u]) for u in surveys})
    print('# surveys:', len(surveys))
    for user in surveys:
        print(f'Processing {user} -- survey length: {len(surveys[user])}')
        survey_json = generate_survey_json(surveys[user], config['survey_header'], config['survey_question'], coding)
        insert_survey(survey_json, user, cursor, config['survey_no'])
    return surveys

import sys
if __name__ == "__main__":
    if len(sys.argv) > 1:
        config = json.loads(open(sys.argv[1]).read())
    else:
        config = None
    
    main(config)  

