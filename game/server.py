import asyncio, json, os, random, socket, sys, time, secrets, io
from pathlib import Path
from aiohttp import web, WSMsgType
import qrcode

ROOT=Path(__file__).resolve().parent
PORT=int(os.environ.get('PORT','8765'))
PIN=os.environ.get('HOST_PIN') or str(random.randint(1000,9999))
RAW = [
    ('음식', '김치찌개', '김치가 들어간 빨간 찌개'),
    ('음식', '떡볶이', '매콤달콤한 떡 요리'),
    ('음식', '비빔밥', '나물과 밥을 비벼 먹어요'),
    ('음식', '삼겹살', '불판 위에서 굽는 돼지고기'),
    ('음식', '치킨', '닭을 튀긴 배달 음식'),
    ('음식', '피자', '동그란 도우 위에 치즈가 올라가요'),
    ('음식', '햄버거', '빵 사이에 고기 패티가 있어요'),
    ('음식', '라면', '냄비에 끓이는 면 요리'),
    ('음식', '김밥', '김에 밥과 채소를 말았어요'),
    ('음식', '아이스크림', '여름에 먹는 차가운 디저트'),
    ('음식', '수박', '초록 껍질과 빨간 속살의 과일'),
    ('음식', '바나나', '노랗고 길쭉한 과일'),
    ('음식', '딸기', '빨갛고 씨가 바깥쪽에 있는 과일'),
    ('음식', '붕어빵', '물고기 모양 겨울 간식'),
    ('음식', '커피', '카페에서 자주 마시는 카페인 음료'),
    ('동물', '강아지', '멍멍 짖는 반려동물'),
    ('동물', '고양이', '야옹 하고 우는 반려동물'),
    ('동물', '토끼', '귀가 길고 깡충깡충 뛰어요'),
    ('동물', '기린', '목이 가장 유명하게 긴 동물'),
    ('동물', '코끼리', '긴 코와 큰 귀가 있어요'),
    ('동물', '호랑이', '주황색 털에 검은 줄무늬'),
    ('동물', '사자', '갈기가 있는 백수의 왕'),
    ('동물', '펭귄', '검은색과 흰색 몸으로 뒤뚱뒤뚱 걸어요'),
    ('동물', '돌고래', '바다에서 똑똑하기로 유명해요'),
    ('동물', '다람쥐', '도토리를 모으는 작은 동물'),
    ('동물', '얼룩말', '흑백 줄무늬가 있는 말과 동물'),
    ('일상', '휴대폰', '전화도 하고 사진도 찍어요'),
    ('일상', '컴퓨터', '키보드와 마우스로 조작해요'),
    ('일상', '냉장고', '음식을 시원하게 보관하는 가전제품'),
    ('일상', '자동차', '네 바퀴로 도로를 달려요'),
    ('일상', '우산', '비 올 때 머리 위에 펼쳐요'),
    ('일상', '칫솔', '이를 닦을 때 사용해요'),
    ('일상', '가방', '물건을 넣고 메고 다녀요'),
    ('일상', '선풍기', '날개가 돌아가 시원한 바람을 만들어요'),
    ('일상', '에어컨', '여름철 실내를 시원하게 해요'),
    ('일상', '이어폰', '귀에 꽂아 음악을 들어요'),
    ('장소', '학교', '학생들이 공부하러 가는 곳'),
    ('장소', '편의점', '24시간 운영하는 곳도 있는 작은 가게'),
    ('장소', '도서관', '조용히 책을 읽거나 공부하는 곳'),
    ('장소', '놀이공원', '롤러코스터를 탈 수 있는 곳'),
    ('장소', '제주도', '한라산과 돌하르방으로 유명한 섬'),
    ('장소', '한라산', '제주도에 있는 높은 산'),
    ('장소', '바다', '파도가 치는 넓은 물'),
    ('장소', '공항', '비행기를 타고 내리는 곳'),
    ('장소', '영화관', '큰 스크린으로 영화를 보는 곳'),
    ('MT·놀이', '노래방', '마이크를 잡고 노래 부르는 곳'),
    ('MT·놀이', '가위바위보', '손으로 셋 중 하나를 내는 놀이'),
    ('MT·놀이', '숨바꼭질', '술래가 숨은 사람을 찾는 놀이'),
    ('MT·놀이', '보물찾기', '숨겨 놓은 물건을 찾아요'),
    ('MT·놀이', '장기자랑', '사람들 앞에서 노래나 춤을 선보여요'),
    ('MT·놀이', '눈치게임', '서로 눈치를 보며 숫자를 외쳐요'),
    ('MT·놀이', '물총놀이', '물총으로 물을 쏘며 놀아요'),
]
CHOSE='ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'
def initial(word):
 out=''
 for c in word:
  v=ord(c)-0xAC00
  if 0<=v<11172:out+=CHOSE[v//588]
  elif c.isalpha():out+=c
 return out
QUESTIONS=[{'cat':c,'text':w,'hint':h,'initial':initial(w)} for c,w,h in RAW]
assert len(QUESTIONS)>=40, len(QUESTIONS)
clients=set(); players={}; current=None; order=[]; idx=-1; ends=0; duration=25; paused=False; remaining=0; revealed=False; round_winners=[]; round_submissions={}; started=False; auto_advance=False; categories=[]; personal_hints=set()

def now():return time.monotonic()
def safe_player(p):return {'id':p['id'],'name':p['name'],'score':p['score'],'correct':p['correct'],'online':p['online']}
def scoreboard():
 return sorted([{'name':p['name'],'score':p['score'],'correct':p['correct']} for p in players.values()], key=lambda x:(-x['score'],-x['correct'],x['name']))
def seconds_left():return max(0,round(remaining if paused else ends-now(),1)) if current else 0
def state(role,pid=None):
 q=None
 if current:
  q={'index':idx+1,'total':len(order),'cat':current['cat'],'initial':current['initial'],'hint':current['hint'] if current.get('hintShown') or (pid in personal_hints) else None,'answer':current['text'] if revealed else None,'remaining':seconds_left(),'duration':duration,'revealed':revealed,'paused':paused,'winners':round_winners}
 return {'type':'state','role':role,'q':q,'players':sorted([safe_player(p) for p in players.values()],key=lambda p:(-p['score'],p['name'])),'teams':[],'standings':scoreboard(),'started':started,'finished':started and idx==len(order)-1 and revealed,'count':len(order),'myId':pid,'submitted':round_submissions.get(pid,0),'correctMe':any(x['id']==pid for x in round_winners),'pin':PIN if role=='host' else None}
async def send(ws,data):
 try:await ws.send_json(data)
 except:pass
async def broadcast(extra=None):
 for ws in list(clients):
  role=ws._role if hasattr(ws,'_role') else 'guest'; pid=getattr(ws,'_pid',None)
  await send(ws,state(role,pid))
 if extra:
  for ws in list(clients):await send(ws,extra)
async def watch_clock(app):
 global revealed
 while True:
  await asyncio.sleep(.3)
  if current and not paused and not revealed and seconds_left()<=0:
   revealed=True
   await broadcast({'type':'effect','kind':'timeout','message':'시간 종료! ⏰'})
async def start_game(opts):
 global players,idx,order,started,current,revealed,ends,duration,round_winners,round_submissions,paused,categories
 duration=max(10,min(90,int(opts.get('duration',25))))
 cats=opts.get('categories') or []
 categories=cats
 order=[dict(q) for q in QUESTIONS if not cats or q['cat'] in cats]
 random.shuffle(order)
 if opts.get('limit'):
  order=order[:max(5,min(len(order),int(opts['limit'])))]
 if not order:order=[dict(q) for q in QUESTIONS];random.shuffle(order)
 for p in players.values():p['score']=0;p['correct']=0
 personal_hints.clear();idx=-1;started=True;current=None;revealed=False;paused=False;round_winners=[];round_submissions={}
 await next_question()
async def next_question():
 global idx,current,revealed,ends,paused,round_winners,round_submissions,personal_hints
 if not order:return
 if idx+1>=len(order):
  await broadcast({'type':'effect','kind':'finish','message':'🏆 모든 문제가 끝났습니다!'})
  return
 idx+=1;personal_hints.clear();current=order[idx];revealed=False;paused=False;round_winners=[];round_submissions={};current['hintShown']=False;ends=now()+duration
 await broadcast({'type':'effect','kind':'next','message':'새 문제가 시작됐어요!'})
async def handle(ws,obj):
 global ends,paused,remaining,revealed
 act=obj.get('action');role=ws._role; pid=ws._pid
 if act=='join':
  if role=='host':return
  name=str(obj.get('name','')).strip()[:16]
  token=str(obj.get('token',''))[:100]
  if not name:return await send(ws,{'type':'error','message':'이름을 입력해 주세요.'})
  if token in players:
   p=players[token];p.update(name=name,online=True)
  else:
   token=secrets.token_urlsafe(16);players[token]={'id':token,'name':name,'score':0,'correct':0,'online':True}
  ws._pid=token;ws._role='player'
  await send(ws,{'type':'joined','token':token});await broadcast();return
 if act=='my_hint':
  if role=='player' and pid and current and not revealed:
   personal_hints.add(pid);await send(ws,state(role,pid))
  return
 if act=='answer':
  if role!='player' or not pid or not current or revealed or paused or seconds_left()<=0:return
  if round_submissions.get(pid,0)>=2:return await send(ws,{'type':'feedback','correct':False,'message':'이번 문제는 2번까지만 제출할 수 있어요.'})
  ans=''.join(str(obj.get('value','')).split()).lower(); gold=''.join(current['text'].split()).lower()
  if not ans:return
  round_submissions[pid]=round_submissions.get(pid,0)+1
  correct=ans==gold
  if correct and not any(x['id']==pid for x in round_winners):
   rank=len(round_winners);points=max(40,100-rank*20)+(20 if round_submissions[pid]==1 else 0)
   p=players[pid];p['score']+=points;p['correct']+=1
   round_winners.append({'id':pid,'name':p['name'],'points':points})
   await send(ws,{'type':'feedback','correct':True,'message':f'정답! +{points}점 🎉'})
   await broadcast({'type':'effect','kind':'correct','message':f"{p['name']} 정답! +{points}점"})
  else:
   await send(ws,{'type':'feedback','correct':False,'message':'아쉽지만 오답! 다시 도전해보세요.'})
   await broadcast()
  return
 if role!='host':return
 if act=='start':await start_game(obj)
 elif act=='next':await next_question()
 elif act=='hint' and current:current['hintShown']=True;await broadcast({'type':'effect','kind':'hint','message':'힌트 공개 💡'})
 elif act=='reveal' and current:revealed=True;await broadcast({'type':'effect','kind':'reveal','message':'정답 공개!'})
 elif act=='pause' and current and not revealed:
  if paused:ends=now()+remaining;paused=False
  else:remaining=seconds_left();paused=True
  await broadcast()
 elif act=='adjust':
  target=str(obj.get('id',''));delta=max(-500,min(500,int(obj.get('delta',0))))
  if target in players:players[target]['score']=max(0,players[target]['score']+delta)
  await broadcast()
 elif act=='reset':
  for p in players.values():p['score']=0;p['correct']=0
  await broadcast()
 elif act=='kick':
  target=str(obj.get('id',''))
  if target in players:del players[target]
  await broadcast()

async def ws_handler(request):
 ws=web.WebSocketResponse(heartbeat=25);await ws.prepare(request)
 ws._role='host' if request.query.get('pin')==PIN else 'guest';ws._pid=None
 clients.add(ws);await send(ws,state(ws._role))
 try:
  async for msg in ws:
   if msg.type==WSMsgType.TEXT:
    try:await handle(ws,json.loads(msg.data))
    except Exception as e:await send(ws,{'type':'error','message':f'처리 오류: {e}'})
 finally:
  clients.discard(ws)
  if ws._pid and ws._pid in players:
   players[ws._pid]['online']=any(getattr(s,'_pid',None)==ws._pid for s in clients)
  await broadcast()
 return ws

def local_ip():
 s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
 try:s.connect(('8.8.8.8',80));return s.getsockname()[0]
 except:return '127.0.0.1'
 finally:s.close()
LAN_IP=os.environ.get('LAN_IP') or local_ip()
BASE_URL=os.environ.get('PUBLIC_URL') or ('https://'+os.environ['RENDER_EXTERNAL_HOSTNAME'] if os.environ.get('RENDER_EXTERNAL_HOSTNAME') else f'http://{LAN_IP}:{PORT}')
async def qr(request):
 url=BASE_URL+'/?join=1'
 img=qrcode.make(url);bio=io.BytesIO();img.save(bio,format='PNG')
 return web.Response(body=bio.getvalue(),content_type='image/png',headers={'Cache-Control':'no-store'})
async def index(request):
 return web.FileResponse(ROOT/'index.html')
async def config(request):
 return web.json_response({'joinUrl':BASE_URL+'/?join=1','teams':[],'categories':sorted(set(q['cat'] for q in QUESTIONS)),'questionCount':len(QUESTIONS)})
async def on_startup(app):app['clock']=asyncio.create_task(watch_clock(app))
async def on_cleanup(app):app['clock'].cancel()
app=web.Application();app.router.add_get('/',index);app.router.add_get('/ws',ws_handler);app.router.add_get('/qr.png',qr);app.router.add_get('/config',config)
app.on_startup.append(on_startup);app.on_cleanup.append(on_cleanup)
if __name__=='__main__':
 print('\n'+'='*64+'\n🎉 MT 초성퀴즈 QR 참여형\n'+'='*64)
 print('사회자:',BASE_URL+f'/?host=1&pin={PIN}')
 print('참가자:',BASE_URL+'/?join=1')
 print('사회자 PIN:',PIN)
 print('📱 온라인 배포 시 참가자에게 참가자 주소/QR코드만 공유하세요.\n'+'='*64+'\n',flush=True)
 web.run_app(app,host='0.0.0.0',port=PORT,print=None)
