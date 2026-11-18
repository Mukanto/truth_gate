import json,glob,os
os.chdir(r"E:\Claude Projects\Kapi\phase_d_work\structure\B2B\cases")
for d in sorted(os.listdir('.')):
    b=json.load(open(d+'/brief.json')); n=json.load(open(d+'/NOTE.json'))
    print('=====',b['id'])
    print('CLAIM:',b['claim'])
    for k in b['data_keys']: print('  KEY',k['key'],k['dtype'],k['dims'],k['shape'],'|',k['meaning'])
    print('  sizes',b['sizes'], [x for x in b if x not in('id','claim','data_keys','sizes')])
    for k in ('source','passage','estimand','exploited_structure','sizes_note','approved_value'): print(' ',k.upper(),':',n[k])
    s=n['structure_statistic']; print('  STAT:',s['code']); print('  ',{k:v for k,v in s.items() if k!='code'})
    print('  other note keys',[x for x in n if x not in('id','source','passage','estimand','exploited_structure','sizes_note','approved_value','structure_statistic')])
