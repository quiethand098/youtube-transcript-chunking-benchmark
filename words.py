import json,urllib.request,re,html
KEY='AIzaSyA8eiZmM1FaDVjRy-df2KTyQ_vz_yYM39w'
def player(v):
    r=urllib.request.Request(f'https://www.youtube.com/youtubei/v1/player?key={KEY}',data=json.dumps({'context':{'client':{'clientName':'ANDROID','clientVersion':'20.10.38','hl':'en'}},'videoId':v}).encode(),headers={'Content-Type':'application/json','User-Agent':'com.google.android.youtube/20.10.38 (Linux; U; Android 14)'})
    return json.load(urllib.request.urlopen(r,timeout=30))
def words(xml):
    out=[]
    for m in re.finditer(r'<p t="(\d+)"[^>]*>(.*?)</p>',xml,re.S):
        t0=int(m.group(1))
        for s in re.finditer(r'<s(?: t="(\d+)")?[^>]*>(.*?)</s>',m.group(2),re.S):
            w=html.unescape(s.group(2)).strip()
            if w: out.append({'t':(t0+int(s.group(1) or 0))/1000,'w':w})
    return out
if __name__=='__main__':
    res={}
    for v in ['zjkBMFhNj_g','kCc8FmEb1nY']:
        j=player(v); t=[x for x in j['captions']['playerCaptionsTracklistRenderer']['captionTracks'] if x.get('kind')=='asr'][0]
        x=urllib.request.urlopen(urllib.request.Request(t['baseUrl'],headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read().decode()
        res[v]=words(x); print(v,len(res[v]))
    json.dump(res,open('asr_words.json','w'))
