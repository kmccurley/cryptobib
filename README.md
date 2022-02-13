# cryptobib

The purpose of this repository is to provide some conversion tools on top
of cryptobib. The output from these tools is something more usable for
an API that supports the following:
1. given an author, find their coauthors
In order to convert cryptobib into a json file, use the following:
```
cat months.bib abbrev0.bib crypto.bib >all.bib
pybtex-convert all.bib all.yaml
yq -o=json '.' all.yaml >all.json
```
The schema for 

