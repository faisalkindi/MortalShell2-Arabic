import json,io,re,sys
def load(p): return json.load(io.open(p,encoding='utf-8'))
def ph(s): return sorted(re.findall(r'\{[A-Za-z0-9_]+\}|%[sd]|<[^<>]{1,40}>',s))
patch=load(sys.argv[1])
for n,pat in sorted(patch.items()):
    src=load('batches/batch_%s.json'%n); tr=load('translated/batch_%s.json'%n)
    bykey={r['key']:r for r in src['rows']}
    from collections import Counter
    tails=[r['key'].split('/')[-1][:8] for r in src['rows']]
    dup={k for k,v in Counter(tails).items() if v>1}
    tail={t:r['key'] for t,r in zip(tails,src['rows']) if t not in dup}
    lp='flow_logs/flow_batch_%s.json'%n
    import os
    log=load(lp) if os.path.exists(lp) else []
    for k,new in pat.items():
        full=src['rows'][int(k[1:])]['key'] if k.startswith('#') else (k if k in bykey else tail.get(k))
        if not full: print('!! %s unknown key %s'%(n,k)); sys.exit(1)
        row=[r for r in tr['rows'] if r['key']==full][0]
        if row['ar']==new: continue
        log=[e for e in log if e['key']!=full]+[{'key':full,'before':row['ar'],'after':new,'why':'flow'}]
        row['ar']=new
    assert [r['key'] for r in tr['rows']]==[r['key'] for r in src['rows']]
    for r in tr['rows']:
        assert ph(r['ar'])==ph(bykey[r['key']]['source_en']), (n,r['key'])
    json.dump(tr,io.open('translated/batch_%s.json'%n,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    json.dump(log,io.open(lp,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print('batch %s: %d/%d changed'%(n,len(log),len(tr['rows'])))
