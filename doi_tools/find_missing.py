"""
This script reads the database to find which entries are lacking a
DOI, and exports them as JSON for easier handling. It uses the bibtexparser
python package.
"""

import json
from pathlib import Path
import re
import sys

import bibtexparser
from bibtexparser.model import Entry, String
from bibtexparser.middlewares import LibraryMiddleware, SeparateCoAuthors, SplitNameParts, MergeNameParts, LatexDecodingMiddleware
from bibtexparser.middlewares.enclosing import RemoveEnclosingMiddleware
from bibtexparser.middlewares.interpolate import _value_is_nonstring_or_enclosed

class StringExpansionMiddleware(LibraryMiddleware):
    """Replace string references in Strings and values. We split on the # character inside both."""
    def __init__(self):
        """We use _strings to keep track of strings we have seen and expand them further.
        This splits strings by the concatenation operator '#' and replaces things successively."""
        self._months = {
            'jan': 'January',
            'feb': 'February',
            'mar': 'March',
            'apr': 'April',
            'may': 'May',
            'jun': 'June',
            'jul': 'July',
            'aug': 'August',
            'sep': 'September',
            'oct': 'October',
            'nov': 'November',
            'dec': 'December'}
        super().__init__()
    def transform(self, library):
        # expand strings inside strings.
        for key, value in self._months.items():
            library.add(String(key, value))
        string_dict = library.strings_dict
        for s in library.strings:
            parts = re.split(r' # ', s.value)
            vals = []
            for part in parts:
                spart = part.strip('"')
                if spart in string_dict:
                    vals.append(string_dict[spart].value)
                else:
                    vals.append(spart)
            s._value = ''.join(vals)
        for entry in library.entries:
            resolved_fields = list()
            for field in entry.fields:
                if _value_is_nonstring_or_enclosed(field.value):
                    continue
                vals = []
                parts = re.split(r' # ', field.value)
                expanded = False
                for part in parts:
                    spart = part.strip('"')
                    if spart in string_dict:
                        expanded = True
                        vals.append(string_dict[spart].value.strip('"'))
                    else:
                        vals.append(spart)
                if expanded:
                    field.value = ''.join(vals)
                if field.value not in library.strings_dict:
                    continue
                field.value = library.strings_dict[field.value].value
                resolved_fields.append(field.key)

            if resolved_fields:
                entry.parser_metadata[self.metadata_key()] = resolved_fields

        return library
                                
# TODO: make this librarymiddleware
def expand_crossref(db):
    """This expands crossref entries to fill in missing fields."""
    entries = db.entries_dict
    for entry in db.entries:
        fields_dict = entry.fields_dict
        crossref = fields_dict.get('crossref')
        if crossref:
            crossref_entry = entries[crossref.value]
            for f in crossref_entry.fields:
                if f.key != 'key' and f.key not in fields_dict:
                    entry.set_field(f)

def fix_strings(db):
    """Replace non-breaking space with space, and and em-dash with dash."""
    for entry in db.entries:
        for field in entry.fields:
            if isinstance(field.value, str):
                field._value = field.value.replace('\xa0', ' ').replace('\u2013', '-')

parse_stack = (StringExpansionMiddleware(),
               RemoveEnclosingMiddleware(),
               LatexDecodingMiddleware(),
               SeparateCoAuthors(),
               SplitNameParts(),
               MergeNameParts(style='first'))
bibstr = Path('../db/abbrev0.bib').read_text(encoding='UTF-8')
bibstr += Path('../db/crypto_conf_list.bib').read_text(encoding='UTF-8')
bibstr += Path('../db/crypto_db.bib').read_text(encoding='UTF-8')
db = bibtexparser.parse_string(bibstr, parse_stack = parse_stack)
expand_crossref(db)
fix_strings(db)
missing = []
for entry in db.entries:
    fields = entry.fields_dict
    entry_type = entry.entry_type.lower()
    if 'doi' not in fields and (entry_type == 'inproceedings' or entry_type == 'article'):
        values = {key: value.value for key,value in fields.items()}
        values['bibkey'] = entry.key
        values['entry_type'] = entry.entry_type
        missing.append(values)
print(json.dumps(missing, indent=2))
    
