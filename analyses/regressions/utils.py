from collections import defaultdict

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

# actual reasons for liking or disliking
like_reasons = set(like_list) - set(["dont-like"])
dislike_reasons = set(dislike_list) - set(["dont-dislike"])

def count_code_props(codes, norm=True):
    # takes dict from adid -> codes and returns dict of code proportions
    counts = defaultdict(lambda: 0)
    for aid in codes:
        # in case of multiple codes, count each one -- essentially computing fraction of codes and not ads here
        for code in codes[aid].split(';'):
            if "Can't determine" not in code and code != 'Study':
                counts[code] += 1                
    if norm:
        return {c: counts[c]/sum(counts.values()) for c in counts}
    else:
        return counts