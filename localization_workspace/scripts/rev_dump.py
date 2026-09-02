import json,io,sys
for n in sys.argv[1:]:
    d=json.load(io.open('review_chunks/chunk_%s.json'%n,encoding='utf-8'))
    print('#### CHUNK %s rows=%d'%(n,len(d['rows'])))
    bc=d['batch_context']
    for k,v in bc.items(): print('  ctx b%s: %s | speaker=%s | reg=%s'%(k,v.get('group'),v.get('speaker'),v.get('register')))
    ns=None
    for i,r in enumerate(d['rows']):
        if r.get('namespace')!=ns:
            ns=r.get('namespace'); print('--- NS %s'%ns)
        print('[%d] li=%s %s'%(i,r.get('line_index'),r['key'].split('/')[-1]))
        print('  EN: %s'%r['source_en'].replace('\n','\n'))
        print('  AR: %s'%r['ar'].replace('\n','\n'))
