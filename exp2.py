import json,re,sys,numpy as np
sys.argv=[sys.argv[0]]
exec(open('exp.py').read().split("emb=TextEmbedding")[0])
from fastembed import TextEmbedding
emb=TextEmbedding('BAAI/bge-small-en-v1.5')
vids=sorted(set(q[0] for q in QA))
for SIZE in [500,1000,2000]:
  print('== size',SIZE)
  for name in ['fixed+20%overlap','actor_v1','pause_aware_v2']:
    for prefix in [False,True]:
      chunks=[]
      for v in vids:
        it=T[v]
        for c in strategies(v,SIZE)[name]:
          chunks.append((v,c['text'],(f"{it['title']} ({it['channel']}): " if prefix else '')+c['text']))
      E=np.array(list(emb.embed([c[2] for c in chunks],batch_size=8)))
      bm=BM25Okapi([norm(c[2]).split() for c in chunks])
      r={'d1':0,'d3':0,'b3':0,'wrongvid1':0}
      Qe=np.array(list(emb.embed(['Represent this sentence for searching relevant passages: '+q[1] for q in QA])))
      for q,qe in zip(QA,Qe):
        ok={k for k,c in enumerate(chunks) if c[0]==q[0] and norm(q[2]) in norm(c[1])}
        d=list(np.argsort(-E@qe)[:3]); b=list(np.argsort(-np.array(bm.get_scores(norm(q[1]).split())))[:3])
        r['d1']+=bool(set(d[:1])&ok); r['d3']+=bool(set(d)&ok); r['b3']+=bool(set(b)&ok); r['wrongvid1']+=chunks[d[0]][0]!=q[0]
      n=len(QA)
      print(f"  {name:17s} title_prefix={prefix!s:5s} chunks={len(chunks)} dense@1={r['d1']}/{n} dense@3={r['d3']}/{n} bm25@3={r['b3']}/{n} top1_wrong_video={r['wrongvid1']}/{n}")
