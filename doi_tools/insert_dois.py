import argparse
import json
from pathlib import Path
import re

parser = argparse.ArgumentParser("Add DOIs from a flat file")
parser.add_argument("--doi_file",
                    required=True,
                    help="file with key,doi in it")
args = parser.parse_args()
doi_file = Path(args.doi_file)
if not doi_file.is_file():
    print('unable to open ', args.doi_file)
    sys.exit(2)
lines = doi_file.read_text(encoding='UTF-8').splitlines()
dois = dict()
for line in lines:
    parts = line.split(',')
    assert len(parts) == 2
    dois[parts[0]] = parts[1]
biblines = Path('../db/crypto_db.bib').read_text(encoding='UTF-8').splitlines()
patt = re.compile(r'^@(article|inproceedings){([^,]+),$', re.IGNORECASE)
key = None
for line in biblines:
    m = patt.match(line)
    if m:
        key = m.group(2)
        if key not in dois:
            key = None
    if line == '}':
        if key:
            print('  doi =          "{}",'.format(dois[key]))
            del dois[key]
            key = None
    print(line)
