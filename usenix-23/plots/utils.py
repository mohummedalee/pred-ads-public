import numpy as np
import os
import pandas as pd
import matplotlib
from collections import Counter

short_names = {
    # dislike
    "I do not dislike this ad.": "dont-dislike",
    "I cannot tell what is being advertised.": "unclear",
    "It is irrelevant to me, or doesn’t contain interesting information.": "irrelevant",
    "I find the ad pushy or it causes me to feel anxious.": "pushy",
    "It contains clickbait, sensationalized, or shocking content.": "clickbait",
    "I do not trust this ad, it seems like a scam.": "scam",
    "I dislike the type of product being advertised.": "dislike-product",
    "I do not like the design of the ad.": "dislike-design",
    "I find the content uncomfortable, offensive, or repulsive.": "uncomfortable",    
    "I dislike the advertiser.": "dislike-advertiser",
    "I dislike the political nature of the ad.": "political",
    # like
    "The content is engaging, clever or amusing.": "amusing",
    "It is well designed or eye-catching.": "like-design",
    "I am interested in what is being advertised.": "interested",
    "It is clear what product the ad is selling.": "clear",
    "I trust the ad, it looks authentic or trustworthy.": "trust-ad",
    "I trust the advertiser.": "trust-advertiser",
    "It is useful, interesting, or informative.": "useful",
    "It clearly looks like an ad and can be filtered out.": "filterable",
    "I do not like this ad.": "dont-like"
}

like_list = ["amusing", "like-design", "interested", "clear", "trust-ad",
     "trust-advertiser", "useful", "filterable", "dont-like"]
dislike_list = ["dont-dislike", "unclear", "irrelevant", "pushy", "clickbait",
    "scam", "dislike-product", "dislike-design", "uncomfortable",
    "dislike-advertiser", "political"]
DONT_COUNT = ["Can't determine, return to this one", "Study", "UNCAT", 
             "Political", "CA Lawsuit"]

# actual reasons for liking or disliking
like_reasons = set(like_list) - set(["dont-like"])
dislike_reasons = set(dislike_list) - set(["dont-dislike"])

def get_err(p, N, Zval=2.576):
    ul = (p + Zval**2/(2*N)+Zval*np.sqrt((p*(1-p)/N + Zval**2/(4*N**2))))/(1+Zval**2/N)
    ll = (p + Zval**2/(2*N)-Zval*np.sqrt((p*(1-p)/N + Zval**2/(4*N**2))))/(1+Zval**2/N)
    return [[-ll+p], [ul-p]]


# NOTE: to count for groups of codes, add another parameters
def measure_exposure(pids: list, adid_codes: dict,
                     pid_adid: pd.DataFrame, freqs: pd.DataFrame, code_groups: dict = None) -> dict:
    # map from PID -> Code -> count (frequency included)
    exposure = {p: Counter() for p in pids}
    total_ads = {}    # map from PID to total number of ads
    for p in pids:
        pid_ads = pid_adid[pid_adid['pid'] == p]
        total_ads[p] = 0
        for aid in pid_ads['adid']:            
            f = int(freqs.loc[p, str(aid)])
            if int(aid) in adid_codes:
                allcodes = adid_codes[int(aid)].split(';')                
                if not code_groups:
                    for c in allcodes:
                        if c not in DONT_COUNT:
                            # code c was seen f times by participant p
                            exposure[p][c] += f                
                            total_ads[p] += f
                else:
                    # grouped code counting from `code_groups` in the else clause, don't double-count
                    done = set([])
                    for c in allcodes:
                        if c in code_groups and c not in DONT_COUNT:
                            mapped = code_groups[c]
                            if mapped not in done:
                                # code group mapped was see f times by participant p
                                exposure[p][mapped] += f
                                total_ads[p] += f
                                done.add(mapped)
            else:
                # we don't have annotations for this, don't count in analysis
                # total_ads[p] -= 1
                continue                        
            
    # NOTE: total_ads contains not just number of ads, but number of observations, factoring in frequencies
    return exposure, total_ads


def setup_nimbus_roman(plt, font_manager, DIR):    
    # FONT_FAMILY = None
    # FONT = 'NimbusRomNo9L-Reg.otf'
    # f = font_manager.get_font(os.path.join(DIR, FONT))
    # font_manager.fontManager.addfont(os.path.join(DIR, FONT))
    # FONT_FAMILY = f.family_name
    # plt.rcParams['font.family'] = FONT_FAMILY

    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['ps.fonttype'] = 42
    for font in font_manager.findSystemFonts(DIR):
        f = font_manager.get_font(font)
        font_manager.fontManager.addfont(font)
        FONT_FAMILY = f.family_name
        
    plt.rcParams['font.family'] = FONT_FAMILY    