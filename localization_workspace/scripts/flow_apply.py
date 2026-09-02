import json,io,sys,re,os
def load(p):
    with io.open(p,encoding='utf-8') as f: return json.load(f)
def ph(s):
    return sorted(re.findall(r'\{[A-Za-z0-9_]+\}|%[sd]|<[^<>]{1,40}>',s))
patch=load(sys.argv[1])  # {"120": {"<keytail>": "new ar", ...}, ...}
for n,pat in sorted(patch.items()):
    src=load('batches/batch_%s.json'%n); tr=load('translated/batch_%s.json'%n)
    bykey={r['key']:r for r in src['rows']}
    from collections import Counter
    tails=[r['key'].split('/')[-1][:8] for r in src['rows']]
    dup={k for k,v in Counter(tails).items() if v>1}
    tail={t:r['key'] for t,r in zip(tails,src['rows']) if t not in dup}
    log=[]
    used=set()
    for k,new in pat.items():
        full=(src['rows'][int(k[1:])]['key'] if k.startswith('#') else (k if k in bykey else tail.get(k)))
        if not full: print('!! %s: unknown key %s'%(n,k)); sys.exit(1)
        used.add(full)
        row=[r for r in tr['rows'] if r['key']==full][0]
        if row['ar']==new: continue
        log.append({'key':full,'before':row['ar'],'after':new,'why':'flow'})
        row['ar']=new
    # verify
    assert [r['key'] for r in tr['rows']]==[r['key'] for r in src['rows']], 'key order mismatch '+n
    bad=[]
    for r in tr['rows']:
        if ph(r['ar'])!=ph(bykey[r['key']]['source_en']): bad.append(r['key'])
    if bad: print('!! %s placeholder mismatch: %s'%(n,bad)); sys.exit(1)
    with io.open('translated/batch_%s.json'%n,'w',encoding='utf-8') as f:
        json.dump(tr,f,ensure_ascii=False,indent=1)
    print('batch %s: %d/%d changed'%(n,len(log),len(tr['rows'])))
    old=[]
    lp='flow_logs/flow_batch_%s.json'%n
    with io.open(lp,'w',encoding='utf-8') as f:
        json.dump(log,f,ensure_ascii=False,indent=1)
