cat months.bib cryptobib/abbrev0.bib cryptobib/crypto.bib >all.bib
pybtex-convert all.bib all.yaml
yq -o=json '.' all.yaml >all.json
python3 parse.py
