from collections import defaultdict
from math import sqrt

plot_names = {
    'Benign': 'Neutral',
    'Healthcare': 'Healthcare',
    'Opportunity': 'Opportunity',
    'Clickbait': 'Clickbait',
    'Financial': 'Financial',
    'Potentially Harmful': 'Potentially Harmful',
    'Political': 'Political',
    'Potentially Prohibited': 'Potentially\nProhibited',
    'CA Lawsuit': 'Class Action\nLawsuit',
    'Harmful': 'Problematic',
    'Other': 'Other',
    'Sensitive': 'Sensitive'
}

colors = {
    'Benign': 'dimgray',
    'Financial': 'palegreen',
    'Healthcare': 'lightseagreen',
    'Opportunity': 'gold',
    'Harmful': 'tab:red',
    'Potentially Harmful': 'tab:red',
    'Potentially Prohibited': 'purple',
    'Clickbait': 'tab:orange',
    'Sensitive': 'pink',
    'Other': 'lightgray'
}

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

def normal_bin_conf(p, n, alpha=.95):
    tab = {0.90: 1.645, 0.95: 1.96, 0.99: 2.58}
    z = tab[alpha]
    # binomial proportion confidence interval
    return z * sqrt((p * (1-p))/n)

