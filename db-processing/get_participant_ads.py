"""
setting up basic infrastructure to fetch a participant's ads given participant ID
"""
import os, sys
import psycopg2
import configparser
import argparse
import json
from copy import deepcopy
from html_parser import DBHTMLParser


def build_html_output(ads_list, outfile, template_file="ad_template.html"):
    hider = '<div id="hider" class="hider">\
        <input id="password" placeholder="enter page password">\
        <button id="passbutton" onclick="submitPass()">Unlock</button>\
    </div>'
    submitpass = '<script>function submitPass() {\
			var pass = document.getElementById("password").value;\
			if (pass == "letmeread") {\
				var x = document.getElementById("container");\
				var y = document.getElementById("hider");\
				if (x.style.display === "none") {\
					x.style.display = "block";\
					y.style.display = "none";\
				} else {\
					x.style.display = "none";\
				}}}</script>'		
    out = f'<html><head><link rel="stylesheet" href="style.css"/>{submitpass}</head><body>{hider}<div id="container" class="container" style="display:none;">'
    template = open(template_file).read()

    for i in range(0, len(ads_list), 2):
        out += '<div class="adrow">'
        for j in range(2):
            # add two ads to each row
            if i+j < len(ads_list):
                ad = ads_list[i+j]
                content = deepcopy(template)
                # fill out all placeholders
                for el, value in ad.items():
                    content = content.replace('%%%s%%'%el, value)
                    
                out += content
        out += '</div>'

    out += '</div></body></html>'
    f = open(outfile, 'w')
    f.write(out)
    f.close()


if __name__ == '__main__':     
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-p", "--pid", help="participant ID (PID)")
    args = argparser.parse_args()
    PID = args.pid
    if not PID:
        sys.exit('No participant ID given. Plese pass arg as -p.')

    participant_ads = []
    
    CONFIG_FILE = "config.local.ini"
    if not os.path.isfile(CONFIG_FILE):
        print(f"Config file is missing: {CONFIG_FILE}")
        sys.exit()

    Config = configparser.ConfigParser()
    Config.read(CONFIG_FILE)
    # db config settings
    db_user = Config.get("database", "user")
    db_port = Config.get("database", "port")    
    db_database = Config.get("database", "db")
    db_schema = Config.get("database", "schema")
    db_password = Config.get("database", "password")
    # filesystem config settings
    image_data_path = Config.get("filesystem", "images")
    observation_data_path = Config.get("filesystem", "observations")    
    # connect to db and set search_path
    if len(db_password):
        conn = psycopg2.connect(f"dbname='{db_database}' user='{db_user}' port='{db_port}' password='{db_password}'")
    else:
        # this would happen for local connections
        conn = psycopg2.connect(f"dbname='{db_database}' user='{db_user}' port='{db_port}'")
    cursor = conn.cursor()    
    cursor.execute(f"SET search_path TO '{db_schema}';")
    print('connected!')

    # fetch shown ad info for each user
    cursor.execute(f"SELECT ad_id, observed_at, advertiser, thumbnail, images, message, html FROM observations\
        INNER JOIN users ON observations.instid = users.instid\
        INNER JOIN ads ON observations.ad_id = ads.id\
        WHERE users.pid = '{PID}';")
    participant_q_result = cursor.fetchall()
    # make index by ad_id
    participant_adids = {row[0]: row for row in participant_q_result}

    # pull out frequency of each ad for the user
    cursor.execute(f"SELECT ad_id, COUNT(*) as freq FROM observations\
        INNER JOIN users on observations.instid=users.instid\
        INNER JOIN ads on observations.ad_id=ads.id\
        WHERE users.pid='{PID}' GROUP BY ad_id ORDER BY freq DESC;")
    ad_freqs_res = cursor.fetchall()
    ad_freqs = dict(ad_freqs_res)
        
    total_ads = len(participant_adids)
    parsed_ads = 0

    print(f'\n--- Participant ID: {PID} ---')    
    # processed = set([])
    for freq_row in ad_freqs_res:
        ad_id = freq_row[0]
        freq = freq_row[1]
        # complete row with advertiser, message etc.
        row = participant_adids[ad_id]
        # if ad_id in processed:
        #     # don't show duplicate observations
        #     continue
        # else:
        #     processed.add(ad_id)
        try:
            advertiser_name = row[2].strip()
            ad_html = row[-1].strip()
            # parse html to extract link, link description, caption etc.
            parser = DBHTMLParser(ad_html)
            parser.linkedURL()
            parser.linkDescriptionCaption()
            parser.callToAction()
            parser.adCaption(advertiser_name)
        except Exception:
            continue

        # only visualizing single image ads
        if parser.is_image_ad and len(row[-3]):
            parsed_ads += 1
            participant_ads.append({
                'advertiser': advertiser_name,
                'caption': parser.caption,
                'linked_url': parser.url,
                'public_url': parser.text_elements[parser.link_ind].text(),
                'link_desc': parser.link_desc,
                'link_caption': parser.link_caption,
                'cta': parser.cta,                
                'logo': os.path.join(image_data_path, row[-4]),
                'image': os.path.join(image_data_path, row[-3][0]),
                'freq': str(freq)
            })            
        else:
            # some ads can be in a different format
            # TODO: investigate later how these can be parsed
            print('\nNot an image ad. Text elements:')
            print([x.text() for x in parser.text_elements])
            print(row[-3])

    # write out as both HTML and json for setting up ads
    build_html_output(participant_ads, PID+'.html')
    with open(PID+'.json', 'w') as wh:
        json.dump(participant_ads, wh, indent=2)

    conn.close()