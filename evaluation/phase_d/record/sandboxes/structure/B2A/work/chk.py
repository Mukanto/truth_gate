import json,glob
for f in sorted(glob.glob('cases/D-*/brief.json')):
    b=json.load(open(f,encoding='utf-8')); c=b['claim']
    print(b['id'], '"' in c, chr(92) in c, len(c))
