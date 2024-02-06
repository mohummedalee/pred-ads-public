import os
import pdb
from copy import deepcopy
import configparser
import pandas as pd
import psycopg2

from html_parser import DBHTMLParser

USERS_EXCLUDE = ('piotr_piot', 'Piotr_user', '921', 'alitest')
INSTID_EXCLUDE = ('neu:616d9b9d-b102-4103-b939-a8884f961d89',
    'neu:7746f9ac-fd28-4d62-b28a-08f8cc60fa00',
    'neu:ee89fd5a-dc91-4a8b-bcd9-b855ea84c2ba')

cta_list = ['Apply Now', 'Book Now', 'Buy Tickets', 'Call Now', 'Contact Us',
    'Donate Now', 'Get Directions', 'Download', 'Get Offer', 'Get Quote', 'Get Showtimes', 'Install Now',
    'Learn More', 'Like Page', 'Listen Now', 'Open Link', 'Order Now', 'Play Game', 'Request Time', 'Save', 'See Menu',
    'Send Message', 'Send WhatsApp Message','Shop Now','Sign Up','Subscribe','Use App','View Event','Watch More']

def connect(config_file):    
    if not os.path.isfile(config_file):
        print(f"Config file is missing: {config_file}")
        return

    Config = configparser.ConfigParser()
    Config.read(config_file)
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

    return conn, image_data_path, observation_data_path

def build_html_output(ads_list, outfile, rowsize=2, template_file="ad_template.html"):
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

    # NOTE: disabling hiding for now, to enable put hider in body and submitpass in head
    out = f'<!DOCTYPE html><html><head><meta charset="utf-8"><link rel="stylesheet" href="style.css"/></head><body><div id="container" class="container">'
    template = open(template_file).read()
    
    offline, online = 0, 0
    for i in range(0, len(ads_list), rowsize):
        out += '<div class="adrow">'
        for j in range(rowsize):
            # add two ads to each row
            if i+j < len(ads_list):
                ad = ads_list[i+j]
                # FIXME: images during achtung outage were not downloaded, don't visualize these
                content = deepcopy(template)
                # fill out all placeholders
                for el, value in ad.items():
                    if el in ['logo', 'image'] and 'http' in value:
                        content = content.replace('%%%s%%'%el, '/mnt/data/scam-ads/screenshots/images/placeholder_%s.png'%el)
                    else:
                        content = content.replace('%%%s%%'%el, value)
                if 'http' not in ad['image']:
                    offline += 1
                else:
                    online += 1
                
                if 'cta' in ad.keys() and ad['cta'].strip() != '':
                    content = content.replace('%btn_visibility%','block')
                else:
                    content = content.replace('%btn_visibility%','none')
                out += content
        out += '</div>'

    out += '</div></body></html>'
    f = open(outfile, 'w')
    f.write(out)
    f.close()

    return offline, online


# load prolific demographics file and returns a dict
def load_dem_file(filename):    
    # Q22 = how would you cover a $400 random expense?
    # Q20 = kinds of debt
    # Q19 = how much are you saving?
    # Q18 = how often do you worry about debt?
    # Q12 = what industry did your parents work in?
    # Q11/Q11_14_TEXT = what industry do you work in
    user_demographics = {}
    df = pd.read_csv(filename)
    df.drop(labels=[0, 1], inplace=True)
    for i in range(df.shape[0]):
        pid = df['PROLIFIC_PID'].iloc[i]
        user_demographics[pid] = {
            '400_expense': df['Q22'].iloc[i],
            'debt': df['Q20'].iloc[i],
            'saving': df['Q19'].iloc[i],
            'how_often': df['Q18'].iloc[i],
            'industry': df['Q11'].iloc[i],
            'industry_text': df['Q11_14_TEXT'].iloc[i]
        }        
        
    return user_demographics

# making a general purpose version of `prepare_annotation_file.py` that takes ad IDs
def prepare_annotation_file(cursor, adids):
    cursor.execute(f"SELECT DISTINCT id, message, advertiser, html, page_id, images FROM ads WHERE id IN %s;",
        (tuple(adids),))
    res = cursor.fetchall()
    export = []
    for row in res:
        # pull out exact linked URL from HTML
        parser = DBHTMLParser(row[3])
        parser.linkedURL()

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

        export.append(pt)

    return export