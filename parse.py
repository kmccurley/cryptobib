from nameparser import HumanName
import json

authornum = 1
authors = {}
with open('all.json', 'r') as f:
    jstr = f.read()
    data = json.loads(jstr)
    data = data.get('entries')
    for k, entry in data.items():
        if 'author' in entry:
            for a in entry.get('author'):
                author = ''
                if 'first' in a:
                    author = a.get('first')
                if 'middle' in a:
                    author = author + ' ' + a.get('middle')
                if 'last' in a:
                    author = author + ' ' + a.get('last')
                if author not in authors:
                    authors[author] = authornum
                    authornum += 1
print(json.dumps(authors, indent=2))
