import json,sys
d=sys.argv[1]
b=json.load(open(f'cases/{d}/brief.json'));n=json.load(open(f'cases/{d}/NOTE.json'))
print('=====',d)
print('CLAIM:',b['claim'])
for k in b['data_keys']: print('KEY',k['key'],k['shape'],k['dtype'],k['dims'],'|',k['meaning'])
print('SIZES',b['sizes'])
for k,v in n.items():
  if k=='id':continue
  if k=='structure_statistic':
    for kk,vv in v.items(): print('  SS.'+kk+':',vv)
  else: print('N.'+k+':',v)
