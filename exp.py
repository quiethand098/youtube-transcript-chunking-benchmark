import json,re,sys
from fastembed import TextEmbedding
import numpy as np
from rank_bm25 import BM25Okapi
SIZES=[int(x) for x in sys.argv[1:]] or [1000]
T={i['videoId']:i for i in json.load(open('transcripts.json'))}
W=json.load(open('asr_words.json'))
QA=json.load(open('qa.json'))
norm=lambda s:re.sub(r'\s+',' ',s.lower()).strip()

def actor_v1(segs,size):  # current actor algorithm, verbatim port
    out=[];cur=None;prev=None
    for s in segs:
        if cur and prev is not None and s['start']-prev>=2 and len(cur['text'])>=size/2: out.append(cur);cur=None
        prev=s['start']+s['duration'] if s.get('duration') is not None else None
        if not cur: cur={'start':s['start'],'text':''}
        cur['text']+=(' ' if cur['text'] else '')+s['text']
        if (len(cur['text'])>=size and re.search(r'[.!?]$',s['text'])) or len(cur['text'])>=size*1.5: out.append(cur);cur=None
    if cur: out.append(cur)
    return out
def fixed(text,size):
    return [{'start':None,'text':text[i:i+size]} for i in range(0,len(text),size)]
def fixed_overlap(text,size,ov=0.2):
    st=int(size*(1-ov)); return [{'start':None,'text':text[i:i+size]} for i in range(0,len(text),st)]
def pause_words(ws,size):
    # cut at the longest pause between words once the chunk is between 0.6x and 1.4x of target
    out=[];i=0;n=len(ws)
    while i<n:
        L=0;j=i;best=None
        while j<n:
            L+=len(ws[j]['w'])+1
            if L>=0.6*size and j+1<n:
                g=ws[j+1]['t']-ws[j]['t']
                if best is None or g>best[0]: best=(g,j)
            if L>=1.4*size: break
            j+=1
        end=best[1] if (best and j<n) else min(j,n-1)
        out.append({'start':ws[i]['t'],'text':' '.join(w['w'] for w in ws[i:end+1])}); i=end+1
    return out
def segs_to_words(segs):  # manual captions: treat each segment as a "word" with its start time
    return [{'t':s['start'],'w':s['text']} for s in segs]
def pause_segs(segs,size):
    ws=[]; 
    for k,s in enumerate(segs):
        end=s['start']+(s.get('duration') or 0)
        ws.append({'t':s['start'],'w':s['text'],'gap':(segs[k+1]['start']-end) if k+1<len(segs) else 0})
    # gap-aware for segment-level: same as pause_words but using real end-gap and sentence end bonus
    out=[];i=0;n=len(ws)
    while i<n:
        L=0;j=i;best=None
        while j<n:
            L+=len(ws[j]['w'])+1
            if L>=0.6*size and j+1<n:
                sc=ws[j]['gap']+(1.0 if re.search(r'[.!?]["\')]?$',ws[j]['w']) else 0)
                if best is None or sc>best[0]: best=(sc,j)
            if L>=1.4*size: break
            j+=1
        end=best[1] if (best and j<n) else min(j,n-1)
        out.append({'start':ws[i]['t'],'text':' '.join(w['w'] for w in ws[i:end+1])}); i=end+1
    return out

def strategies(v,SIZE):
    it=T[v]; segs=it['segments']; text=' '.join(s['text'] for s in segs)
    S={'fixed':fixed(text,SIZE),'fixed+20%overlap':fixed_overlap(text,SIZE),'actor_v1':actor_v1(segs,SIZE)}
    S['pause_aware_v2']=pause_words(W[v],SIZE) if v in W else pause_segs(segs,SIZE)
    return S
emb=TextEmbedding('BAAI/bge-small-en-v1.5')
vids=sorted(set(q[0] for q in QA))
for SIZE in SIZES:
  print('== target chunk size',SIZE)
  stats={}
  for v in vids:
    for name,ch in strategies(v,SIZE).items():
          texts=[c['text'] for c in ch]
          E=np.array(list(emb.embed(texts))); 
          bm=BM25Okapi([norm(t).split() for t in texts])
          lens=[len(t) for t in texts]
          midword=sum(1 for c in ch[:-1] if not re.search(r'[.!?,]["\')]?$',c['text'].strip()))/max(1,len(ch)-1)
          st=stats.setdefault(name,{'chunks':0,'cut_not_at_punct':[],'asr':{},'man':{}})
          st['chunks']+=len(ch)
          kind='asr' if v in W else 'man'
          for q in [q for q in QA if q[0]==v]:
              gold=norm(q[2])
              contain=[k for k,t in enumerate(texts) if gold in norm(t)]
              qe=np.array(list(emb.embed(['Represent this sentence for searching relevant passages: '+q[1]])))[0]
              dense=list(np.argsort(-E@qe)[:3])
              sparse=list(np.argsort(-np.array(bm.get_scores(norm(q[1]).split())))[:3])
              d=st[kind].setdefault('n',0); st[kind]['n']+=1
              for key,rk in [('dense@1',dense[:1]),('dense@3',dense),('bm25@3',sparse)]:
                  st[kind][key]=st[kind].get(key,0)+(1 if set(rk)&set(contain) else 0)
              st[kind]['split']=st[kind].get('split',0)+(0 if contain else 1)
  for name,st in stats.items():
      line=f"{name:18s} chunks={st['chunks']:4d}"
      for kind in ('asr','man'):
          k=st[kind]; n=k['n']
          line+=f" | {kind} n={n} answer-split={k['split']}/{n} dense@1={k['dense@1']}/{n} dense@3={k['dense@3']}/{n} bm25@3={k['bm25@3']}/{n}"
      print(line)
