"""The purpose of this is to read the output from lookup_doi.py and
resolve whether one of the search results is a close enough match
to accurately reflect the DOI. In order to do this, we insist on an 
exact match for the title and authors, and then check that the DOI
prefix and year are plausible. As an example, if you are looking up
for CCS:BarJacMit08, then the CCS prefix identifies it as an ACM DOI,
so a DOI should start with 10.1145/. Unfortunately the year is only
weakly inferred from the suffix of the bibtex key, since the ccs08
crossreference does not contain a year field. In this case we would fall
back to pages, which should also be supplied in the search result.

"""
"""This takes the output from lookup.py and tries to match
a paper against the best match from search."""
import argparse
import html
import json
import Levenshtein
from pylatexenc.latex2text import LatexNodes2Text
from pathlib import Path
import re
import string
import sys
# We use the conference identifier to match to a DOI prefix.
prefixes = {
    'ACISP': ['10.1007'],
    'AFRICACRYPT': ['10.1007'],
    'ASIACCS': ['10.1145'],
    'CANS': ['10.1007'],
    'C': ['10.1007'], 
    'EC': ['10.1007'],
    'ESORICS': ['10.1007'],
    'FC': ['10.1007'],
    'FCW': ['10.1007'],
    'FOCS': ['10.1109'],
    'ICALP': ['10.4230'],
    'ICICS': ['10.1007'],
    'ICISC': ['10.1007'],
    'ICITS': ['10.1007'],
    'IEICE': ['10.1587'],
    'IMA': ['10.1007'],
    'INDOCRYPT': ['10.1007'],
    'ISC': ['10.1007'],
#    'ITCS': '',
    'IWSEC': ['10.1007'],
    'JC': ['10.1007'],
    'LATIN': ['10.1007'],
    'LC': ['10.1007'],
    'NDSS': ['10.14722'],
    'PODC': ['10.1145'],
    'PoPETS': ['10.56553','10.1515'],
    'PROVSEC': ['10.1007'],
    'SODA': ['10.1137'],
    'SP': ['10.1109'],
    'STOC': ['10.1145'],
    'TCHES': ['10.46586'],
    'TRUSTBUS': ['10.1007'],
#    'USENIX': '',
    'VIETCRYPT': ['10.1007'],
    'WISA': ['10.1007']
}

argparser = argparse.ArgumentParser(description='Create .doi files from .json file')
argparser.add_argument('--json_file',
                       required=True,
                       default='all.json',
                       help = 'output from lookup.py')
argparser.add_argument('--out_file',
                       required=True,
                       help = 'output file')
args = argparser.parse_args()

out_file = Path(args.out_file)
if out_file.is_file():
    print('out_file must not exist')
    sys.exit(2)

decoder = LatexNodes2Text()
lookups = json.loads(open(args.json_file, 'r').read())
short_pat = re.compile(r'\(?Extended Abstract\)?|\(?Short Paper\)?|\(?Invited talk\)?|\{?Poster\}?:|\(?Poster\)?|Poster:|\(?Invited lecture\)?|\(?keynote lecture\)?|\(?keynote talk\)?|\(?keynote\)?|\(?Short paper\)?|\(?fast abstract\)?|\(?preliminary version\)?',
                       re.IGNORECASE)
no_space_pat = re.compile(r'\s')
def clean_title(t):
    return no_space_pat.sub('', short_pat.sub('', decoder.latex_to_text(t)).lower())

_removepunct = str.maketrans('', '', string.punctuation)

def check_prefix(k, result):
    if ':' in k:
        conf = k.split(':')[0]
        prefixlist = prefixes.get(conf)
        if prefixlist and result['prefix'] not in prefixlist:
            print('mismatch on prefix {}:{}'.format(k, result['prefix']))
            return False
    return True # (no prefix, so this is a no-op)

def almost_equal(t1, t2):
    t1 = t1.translate(_removepunct)
    t2 = t2.translate(_removepunct)
    dist = Levenshtein.distance(t1, t2)
    percent_dist =  dist / float(len(t1))
    if percent_dist < .08:
        if dist == 0:
            print('exact match on title', t1)
            return True
        else:
            print('close match on title', dist)
            print(t1)
            print(t2)
            return True
    print('mismatch:{}:{}\n {}\n {}\n {}\n {}'.format(dist, percent_dist, t1, t2, t1.encode('utf-8').hex(),t2.encode('utf-8').hex()))
    return False

with open(args.out_file, 'w') as f:
    for v in lookups:
        bibtex = v['bibtex']
        k = bibtex['bibkey']
        if 'doi' in bibtex:
            continue
        print('================ {}'.format(k))
        title = clean_title(bibtex['title'])
        authors = bibtex['author']
        if 'year' not in bibtex:
            print('no year in ', k)
            sys.exit(2)
        vyear = bibtex['year'].strip()
        matched = False
        for result in v['search']:
            if len(authors) != len(result['author']):
                print('wrong number of authors {}:{}'.format(len(authors), len(result['author'])))
            else:
                year = None
                if 'published-print' in result:
                    year = result['published-print']['date-parts'][0][0]
                elif 'published-online' in result:
                    year = result['published-online']['date-parts'][0][0]
                elif 'published' in result:
                    year = result['published']['date-parts'][0][0]
                if year and (vyear != str(year)):
                    print('year mismatch {}:{}:{}'.format(k, vyear, year, result['title'][0]))
                else:
                    res_title = clean_title(html.unescape(result['title'][0]))
                    if almost_equal(title, res_title):
                        if check_prefix(k, result):
                            matched = True
                            f.write('{},{}\n'.format(k, result['DOI']))
                            break
                    else:
                        if 'subtitle' in result and result['subtitle']:
                            res_title = clean_title(html.unescape(result['title'][0] + result['subtitle'][0]))
                            if almost_equal(title, res_title):
                                if check_prefix(k, result):
                                    matched = True
                                    f.write('{},{}\n'.format(k, result['DOI']))
                                    break
        if not matched:
            print('//////////////NO MATCH for {}:{}'.format(k, v['bibtex']['title']))

    
    
