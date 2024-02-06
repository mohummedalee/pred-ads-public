"""
similar to vis_participant_ads.py
"""
import os, sys
import json
import datetime as dt
from copy import deepcopy

from html_parser import DBHTMLParser
import db_utils
import pdb

SCREENSHOT_PATH = '/mnt/data/scam-ads/screenshots/'

if __name__ == '__main__':             
    CONFIG_FILE = 'config.reader.ini'
    conn, img_path, obs_path = db_utils.connect(CONFIG_FILE)
    cursor = conn.cursor()
    cursor.execute(f"SET search_path TO 'observations';")    
    print('connected!')        

    participant_ads = []
    
    cursor.execute(f"SELECT ad_id, observed_at, advertiser, thumbnail, images, message, html FROM observations\
        INNER JOIN users ON observations.instid = users.instid\
        INNER JOIN ads ON observations.ad_id = ads.id\
        WHERE users.pid NOT IN {db_utils.USERS_EXCLUDE};")
    participant_q_result = cursor.fetchall()
    # make index by ad_id to remove duplicates
    all_adids = {row[0]: row for row in participant_q_result}    
            
    outliers = 'outliers.txt'
    wh = open(outliers, 'w')
    for ad_id in all_adids:

        row = all_adids[ad_id]            
        # parse html to extract link, link description, caption etc.
        try:
            advertiser_name = row[2].strip()
            ad_html = row[-1].strip()                
            parser = DBHTMLParser(ad_html)
            parser.linkedURL()
            parser.linkDescriptionCaption()
            parser.callToAction()
            parser.adCaption(advertiser_name)
        except Exception:
            continue

        # abbreviated message field in case it's used as caption        
        abb_message = row[-2].split('\n')[0]

        # only visualizing single image ads
        if parser.is_image_ad and len(row[-3]):
            participant_ads.append({
                'advertiser': advertiser_name,
                'caption': parser.caption,
                'linked_url': parser.url,
                'public_url': parser.text_elements[parser.link_ind].text(),
                'link_desc': parser.link_desc,
                'link_caption': parser.link_caption,
                'cta': parser.cta,                
                'logo': os.path.join(img_path, row[-4]),
                'image': os.path.join(img_path, row[-3][0]),
                'note': "ID: " + str(ad_id)
            })
        elif len(row[-3]) >= 1:
            # hackily visualize where parser can't pick up finegrained components
            participant_ads.append({
                'advertiser': advertiser_name,
                # two cases where parser fails: ads that are not URL specific, and multi-image ads -- show for annotator
                'caption': abb_message,
                'linked_url': parser.url,
                'public_url': '',
                'link_desc': '',
                'link_caption': '',
                'cta': '',
                'logo': os.path.join(img_path, row[-4]),
                'image': os.path.join(img_path, row[-3][0]),
                'note': "ID: " + str(ad_id)
            })
        else:
            # some ads can be in a different format, dump to stdout
            # print('\nNot an image ad. Text elements:')
            # print([x.text() for x in parser.text_elements])
            wh.write(str(ad_id) + ' -- images:' + str(row[-3]) + '\n\n')

    # write out as both HTML and json for setting up ads
    today = str(dt.date.today())
    offline, online = db_utils.build_html_output(participant_ads, today+'.html', rowsize=3)
    
    for ad in participant_ads:
        offline, online = db_utils.build_html_output([ad], f"{SCREENSHOT_PATH}{ad['note'].replace('ID: ','')}.html", rowsize=1)

    #with open(today+'.json', 'w') as wh:
    #    json.dump(participant_ads, wh, indent=2)
    
    print(f'\n=== visualized {offline}/{len(all_adids)} ads in {today}.html! ===')
    print(f'\n=== {online}/{len(all_adids)} images weren\'t found downloaded. ===')
    print(f'\n=== exported outliers to {outliers} ===')

    conn.close()
