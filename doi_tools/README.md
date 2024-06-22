This directory contains code to backfill some missing DOIs for
entries. It is built using the bibtexparser class instead of pybtex
(or mybibtex) because that has better encoding of LaTeX to strings.

The algorithm is to dump out the data for missing DOIs as a big JSON file,
and then read these with another tool to look up the entry using the
crossref or openalex api to find the DOI for the entry. This last part
is error-prone and matching must be done carefully and conservatively.

The code is as follows:
- `find_missing.py` reads the database and finds entries of type @article
  and @inproceedings that are missing a DOI. It then dumps them as JSON.
- `lookup_doi.py` reads the output from `find_missing.py` and performs
  a lookup for the entry using the crossref API.