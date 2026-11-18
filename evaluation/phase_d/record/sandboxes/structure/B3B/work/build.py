import json, os, glob
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for f in sorted(glob.glob(os.path.join(root, 'work', 'bodies', 'D-*.py'))):
    cid = os.path.basename(f)[:-3]
    brief = json.load(open(os.path.join(root, 'cases', cid, 'brief.json'), encoding='utf-8'))
    assert '"' not in brief['claim']
    body = open(f, encoding='utf-8').read()
    out = '"""%s: %s"""\n' % (cid, brief['claim']) + body
    open(os.path.join(root, 'cases', cid, 'reference.py'), 'w', encoding='utf-8', newline='\n').write(out)
print('built')
