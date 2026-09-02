import json,sys,io
def load(p):
    with io.open(p,encoding='utf-8') as f: return json.load(f)
for n in sys.argv[1:]:
    src=load('batches/batch_%s.json'%n); tr=load('translated/batch_%s.json'%n)
    ar={r['key']:r['ar'] for r in tr['rows']}
    print('#### BATCH %s | group=%s speaker=%s register=%s | rows=%d'%(n,src.get('group'),src.get('speaker'),src.get('register'),len(src['rows'])))
    ns=None
    for i,r in enumerate(src['rows']):
        if r.get('namespace')!=ns:
            ns=r.get('namespace'); print('--- NS: %s'%ns)
        e=r['source_en'].replace('\n','\n'); a=ar.get(r['key'],'<<MISSING>>').replace('\n','\n')
        print('[%d] %s'%(i,r['key'].split('/')[-1][:8]))
        print('  EN: %s'%e)
        print('  AR: %s'%a)
