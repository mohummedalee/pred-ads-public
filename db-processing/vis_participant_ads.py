"""
setting up basic infrastructure to fetch a participant's ads given participant ID
"""
import os, sys
import psycopg2
import configparser
import argparse
import json
from copy import deepcopy

import db_utils
from html_parser import DBHTMLParser


def build_html_output(ads_list, outfile, PID, template_file="ad_template.html", dem_file='prolific-demographics.csv'):    
    hider = '<div id="hider" class="hider">\
        <input id="password" placeholder="enter page password">\
        <button id="passbutton" onclick="submitPass()">Unlock</button>\
    </div>'

    # add user demographics
    dems = db_utils.load_dem_file(dem_file)[PID]
    dems_div = '<div class="demographics">\
			        <h3 style="text-decoration: underline; font-weight: normal;">User Demographics</h3> <ul>'
    dems_div += '<li><span style="font-weight: bold;">What industry do you work in? </span>' + dems['industry'] + f' ({dems["industry_text"]})' + '</li>'
    dems_div += '<li><span style="font-weight: bold;">How would you cover an unexpected $400 expense? </span>' + dems['400_expense'] + '</li>'
    dems_div += '<li><span style="font-weight: bold;">What kinds of debt are you currently carrying? </span>' + dems['debt'] + '</li>'
    dems_div += '<li><span style="font-weight: bold;">In terms of savings, how would you describe your current financial situation? </span>' + dems['saving'] + '</li>'
    dems_div += '<li><span style="font-weight: bold;">How often do you worry about debt? </span>' + dems['how_often'] + '</li>'
    dems_div += '</ul></div>'

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
    # out = f'<html><head><link rel="stylesheet" href="style.css"/>{submitpass}</head><body>{hider}<div id="container" class="container" style="display:none;">'
    # hider disabled version
    out = f'<html><head><link rel="stylesheet" href="style.css"/></head><body><div id="container" class="container">{dems_div}'
    template = open(template_file).read()

    rowsize = 3
    for i in range(0, len(ads_list), rowsize):
        out += '<div class="adrow">'
        for j in range(rowsize):
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
    
    CONFIG_FILE = "config.reader.ini"    
    outdir = 'pilot-ad-viz-htmls'
    
    conn, image_data_path, observation_data_path = db_utils.connect(CONFIG_FILE)
    cursor = conn.cursor()    
    cursor.execute("SET search_path TO 'observations';")

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
  
    print(f'unique retrieved from DB: {len(ad_freqs_res)}')
    for freq_row in ad_freqs_res:
        ad_id = freq_row[0]
        freq = freq_row[1]
        # complete row with advertiser, message etc.
        row = participant_adids[ad_id]        
        try:
            advertiser_name = row[2].strip()
            ad_html = row[-1].strip()
            # parse html to extract link, link description, caption etc.
            parser = DBHTMLParser(ad_html)
            parser.linkedURL()
            parser.linkDescriptionCaption()
            parser.callToAction()
            parser.adCaption(advertiser_name)
        except Exception as e:
            # parser can't take it
            participant_ads.append({
                'advertiser': advertiser_name,
                'caption': "UNPROCESSED TEXT: " + row[-2] if len(row[-3]) == 1 else "MULTI-IMAGE: " + row[-2],
                'linked_url': '',
                'public_url': '',
                'link_desc': '',
                'link_caption': '',
                'cta': '',         
                'logo': os.path.join(image_data_path, row[-4] if 'http' not in row[-4] else 'missing.jpg'),
                'image': os.path.join(image_data_path, row[-3][0] if len(row[-3]) and 'http' not in ''.join(row[-3])\
                     else 'missing.jpg'),
                'note': 'freq: ' + str(freq)
            })
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
                'logo': os.path.join(image_data_path, row[-4] if 'http' not in row[-4] else 'missing.jpg'),
                'image': os.path.join(image_data_path, row[-3][0] if 'http' not in ''.join(row[-3]) else 'missing.jpg'),
                'note': 'freq: ' + str(freq)
            })
        else:
            # put in the HTML in whatever form you can
            participant_ads.append({
                'advertiser': advertiser_name,
                'caption': "UNPROCESSED TEXT: " + row[-2] if len(row[-3]) == 1 else "MULTI-IMAGE: " + row[-2],
                'linked_url': parser.url,
                'public_url': '',
                'link_desc': '',
                'link_caption': '',
                'cta': '',         
                'logo': os.path.join(image_data_path, row[-4] if 'http' not in row[-4] else 'missing.jpg'),
                'image': os.path.join(image_data_path, row[-3][0] if len(row[-3]) and 'http' not in ''.join(row[-3])\
                     else 'missing.jpg'),
                'note': 'freq: ' + str(freq)
            })

    print(f'after processing: {len(participant_ads)}')
    # write out as both HTML and json for setting up ads    
    build_html_output(participant_ads, os.path.join(outdir, PID+'.html'), PID)
    with open(os.path.join(outdir, PID+'.json'), 'w') as wh:
        json.dump(participant_ads, wh, indent=2)
    
    outpath = str(os.path.join(outdir, PID+'.html'))
    print(f'exported visualization to {outpath}!')

    conn.close()