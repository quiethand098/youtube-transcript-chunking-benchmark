"""What an MCP client receives from the Actor: run result size, default dataset fetch, nested-field projection."""
import json,urllib.request,sys
import os
env={'APIFY_TOKEN':os.environ['APIFY_TOKEN']}
URL='https://mcp.apify.com/?tools=quiethand098/youtube-transcript-rag-extractor'
H={'Authorization':'Bearer '+env['APIFY_TOKEN'],'Content-Type':'application/json','Accept':'application/json, text/event-stream'}
sid=None
def rpc(method,params=None,id=1,notify=False):
    global sid
    body={'jsonrpc':'2.0','method':method}
    if params is not None: body['params']=params
    if not notify: body['id']=id
    h=dict(H); 
    if sid: h['Mcp-Session-Id']=sid
    r=urllib.request.urlopen(urllib.request.Request(URL,data=json.dumps(body).encode(),headers=h),timeout=300)
    sid=r.headers.get('Mcp-Session-Id') or sid
    t=r.read().decode()
    if notify: return None
    if t.startswith('event') or 'data:' in t[:20]:
        t=[l[5:].strip() for l in t.splitlines() if l.startswith('data:')][-1]
    return json.loads(t)
rpc('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'probe','version':'1'}})
rpc('notifications/initialized',notify=True)
tl=rpc('tools/list',id=2)['result']['tools']
for t in tl: print('TOOL',t['name'],len(json.dumps(t)),'chars schema')
yt=[t for t in tl if 'youtube' in t['name']][0]
json.dump(yt,open('mcp_tool_def.json','w'),indent=1)
print(yt['description'][:600])
args={"videos":["https://www.youtube.com/watch?v=zjkBMFhNj_g"],"chunkChars":1000}
res=rpc('tools/call',{'name':yt['name'],'arguments':args},id=3)
json.dump(res,open('mcp_call_result.json','w'),indent=1)
c=res.get('result',{}).get('content',[])
for x in c: print('CONTENT',x.get('type'),len(x.get('text','')),x.get('text','')[:500].replace('\n',' '))

ds=json.loads(res['result']['content'][0]['text'])['storages']['datasets']['default']['id']
for i,a in enumerate([{'datasetId':ds,'limit':20},{'datasetId':ds,'limit':20,'fields':'title,chunks.startSeconds,chunks.link,chunks.text'}]):
    r=rpc('tools/call',{'name':'get-dataset-items','arguments':a},id=10+i)
    print(a.get('fields'),'->',len(''.join(x.get('text','') for x in r['result']['content'])),'chars')
