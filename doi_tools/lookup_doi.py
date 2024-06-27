"""The purpose of this is to read a dump from find_missing.py
containing bibliographic information about cryptobib entries with
DOIs, and execute a search on the crossref API looking for the
paper. The searches are somewhat slow and expensive, and the matching
is necessarily fuzzy, so we simply save the search results for offline
processing.

"""

import argparse
import datetime
from pathlib import Path
import json
from crossref.restful import Works, Etiquette
from pylatexenc.latex2text import LatexNodes2Text
import sys

def exact_match(orig, res):
    if not res['title']:
        return False

argparser = argparse.ArgumentParser(description='Create .doi files from .json file')
argparser.add_argument('--bads_file',
                       default = 'example.bads',
                       help = 'output from find_missing.py')
argparser.add_argument('--start',
                       type=int,
                       default=0,
                       help = 'which record to start from')
argparser.add_argument('--num_records',
                       type=int,
                       default=10000,
                       help = 'how many records to process')
argparser.add_argument('--num_results',
                       type=int,
                       default=3,
                       help='Number of search results to request')
args = argparser.parse_args()

out_path = Path(args.bads_file + '.{}.{}.json'.format(args.start, args.num_records))
if out_path.is_file():
    print('{} must not exist'.format(str(out_path)))
    sys.exit(2)

bads = json.loads(open(args.bads_file, 'r').read())

decoder = LatexNodes2Text()
etiquette = Etiquette('cryptobib',
                      'updates',
                      'https://github.com/cryptobib',
                      'cryptobib@digicrime.com')
works = Works(etiquette=etiquette)
works.request_params['rows'] = args.num_results
lookups = {}
badcount = 0
with out_path.open('w', encoding='utf-8') as out_file:
    out_file.write('[')
    for i in range(args.start, args.start+args.num_records):
        if i % 10 == 0:
            print('record={} {}'.format(i, str(datetime.datetime.now())))
        v = bads[i]
        title = decoder.latex_to_text(v['title'])
        date = '{}-01-01'.format(v['year'])
        res = works.query(bibliographic=title, author=decoder.latex_to_text(', '.join(v['author'])))#.filter(from_online_pub_date=date)
        items = []
        counter = 0
        for r in res:
            if 'title' in r and len(r['title']) and 'author' in r:
                counter += 1
                if counter > args.num_results:
                    break
                item = json.loads(json.dumps(r))
                for useless_key in ['abstract',
                                    'content-domain',
                                    'deposited',
                                    'funder',
                                    'indexed',
                                    'isbn-type',
                                    'ISBN',
                                    'ISSN',
                                    'issn-type',
                                    'issued',
                                    'is-referenced-by-count',
                                    'language',
                                    'license',
                                    'member',
                                    'publisher-location',
                                    'reference',
                                    'reference-count',
                                    'source',
                                    'references-count',
                                    'update-policy']:
                    if useless_key in item:
                        del item[useless_key]
                items.append(item)
        lookup = {'i': i,
                  'bibtex': v,
                  'url': res.url,
                  'search': items}
        out_file.write(json.dumps(lookup, indent=2))
        out_file.write('\n')
        out_file.flush()
    out_file.write(']')
    
    
