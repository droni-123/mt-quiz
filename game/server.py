import asyncio, json, os, random, socket, sys, time, secrets, io
from pathlib import Path
from aiohttp import web, WSMsgType
import qrcode

ROOT=Path(__file__).resolve().parent
PORT=int(os.environ.get('PORT','8765'))
PIN=os.environ.get('HOST_PIN') or str(random.randint(1000,9999))
TEAMS=['🔥 불꽃팀','⚡ 번개팀','🌊 파도팀','🌟 별빛팀']
RAW=[
('음식','ㄱㅊㅉㄱ','김치찌개','한국인의 소울푸드, 빨간 국물'),('음식','ㅂㅂㅂ','비빔밥','여러 재료를 섞어서 먹는 밥'),('음식','ㄸㅂㅇ','떡볶이','분식집의 대표 메뉴'),('음식','ㅅㄱㅅ','삼겹살','불판에 구워 먹는 고기'),('음식','ㅂㅅㅌ','붕어빵','겨울철 길거리 간식'),('음식','ㅁㄹㅌ','마라탕','얼얼한 맛의 중국식 국물'),('음식','ㅊㅋㅁ','초코몽','초콜릿과 몽? 이 문제는 제외'),
('동물','ㅋㅍㅂㄹ','카피바라','세계에서 가장 큰 설치류'),('동물','ㄱㄹ','기린','목이 아주 긴 초식동물'),('동물','ㅋㅇㄹ','코알라','유칼립투스 잎을 먹어요'),('동물','ㅍㄱ','펭귄','날지 못하지만 수영을 잘해요'),('동물','ㅂㄷㄱ','바다거북','바다에서 사는 등딱지 동물'),('동물','ㄷㄹㅈ','다람쥐','도토리를 좋아하는 작은 동물'),
('영화·드라마','ㅂㅅㅊ','부산행','좀비가 등장하는 한국 영화'),('영화·드라마','ㄱㅅㅊ','기생충','봉준호 감독 작품'),('영화·드라마','ㅅㅈㄱ','신세계','황정민과 이정재 출연 범죄 영화'),('영화·드라마','ㅇㅈㄱㅇ','오징어게임','넷플릭스 생존 게임 드라마'),('영화·드라마','ㄷㄲㅂ','도깨비','공유가 출연한 판타지 드라마'),('영화·드라마','ㅌㅌㄴ','타이타닉','유명한 대형 여객선 영화'),
('일상·상식','ㅅㅁㅍ','스마트폰','손에 들고 다니는 통신 기기'),('일상·상식','ㅂㅈㄱ','보조개','웃으면 볼에 쏙 들어가는 부분'),('일상·상식','ㅊㅅㅌ','충전탭','전기 연결 도구? 제외'),('일상·상식','ㄴㅈㅇ','냉장고','음식물을 차갑게 보관해요'),('일상·상식','ㅈㄷㅊ','자동차','도로를 달리는 교통수단'),('일상·상식','ㅎㄷㅍ','핸드폰','전화와 인터넷이 가능한 기기'),('일상·상식','ㅇㅅㅋㄹ','아이스크림','차갑고 달콤한 간식'),
('MT·레크','ㅂㅂㅂ','복불복','운에 따라 벌칙이 달라지는 게임'),('MT·레크','ㅁㅊㄱㅇ','몸치게임','몸동작으로 추리하는 게임? 제외'),('MT·레크','ㅂㅅㄱㅇ','빙수게임','얼음 디저트 게임? 제외'),('MT·레크','ㅅㅁㄱㅇ','신문게임','신문지 위에서 버티는 게임'),('MT·레크','ㅈㄱㅊㄱ','장기자랑','모임에서 재능을 보여주는 시간'),('MT·레크','ㅇㄱㄷㅈ','인간도전','제외'),('MT·레크','ㅈㅇㅈ','제일조','제외'),('MT·레크','ㄱㅊㄱㅇ','고추게임','제외'),('MT·레크','ㅅㅅㄱㅇ','순서게임','순서를 맞추는 활동'),
('여행·장소','ㅈㅈㄷ','제주도','돌하르방과 한라산이 있는 섬'),('여행·장소','ㅎㄹㅅ','한라산','제주도의 높은 산'),('여행·장소','ㄴㅅㅌ','남산타워','서울의 전망대'),('여행·장소','ㄱㅂㄱ','경복궁','서울의 대표 궁궐'),('여행·장소','ㄱㄷㄹ','광대리','제외'),('여행·장소','ㅂㄷㅂ','바닷바람','해변에서 부는 바람'),
]
RAW.extend([
('음식','','순두부찌개','부드러운 두부가 들어간 얼큰한 찌개'),
('음식','','감자탕','등뼈와 감자를 푹 끓인 음식'),
('음식','','치즈볼','치즈가 들어간 동그란 간식'),
('음식','','닭갈비','춘천이 유명한 철판 요리'),
('동물','','고슴도치','몸에 가시가 있는 작은 포유류'),
('동물','','하마','입이 아주 크고 물속을 좋아하는 동물'),
('동물','','오랑우탄','긴 팔을 지닌 유인원'),
('동물','','얼룩말','검고 흰 줄무늬가 있는 동물'),
('영화·드라마','','극한직업','치킨집을 운영하는 형사들 영화'),
('영화·드라마','','범죄도시','마동석 주연 액션 영화 시리즈'),
('영화·드라마','','미스터션샤인','대한제국 말기를 배경으로 한 드라마'),
('일상·상식','','이어폰','귀에 꽂고 소리를 듣는 기기'),
('일상·상식','','전자레인지','음식물을 빠르게 데우는 가전제품'),
('일상·상식','','노트북','휴대용 컴퓨터'),
('MT·레크','','눈치게임','순서를 서로 눈치 보며 말하는 게임'),
('MT·레크','','손병호게임','손가락을 접으며 진행하는 게임'),
('MT·레크','','의자게임','음악이 멈추면 앉는 놀이'),
('여행·장소','','남이섬','가평 근처의 유명한 관광 섬'),
('여행·장소','','광안대교','부산 바다를 가로지르는 큰 다리'),
('여행·장소','','롯데월드','잠실에 있는 놀이공원'),
])
CHOSE='ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'
def initial(word):
 out=''
 for c in word:
  v=ord(c)-0xAC00
  if 0<=v<11172:out+=CHOSE[v//588]
  elif c.isalpha():out+=c
 return out
QUESTIONS=[{'cat':c,'text':w,'hint':h,'initial':initial(w)} for c,i,w,h in RAW if not h.endswith('제외') and (initial(w)==i or not i)]
assert len(QUESTIONS)>=40, len(QUESTIONS)
clients=set(); players={}; current=None; order=[]; idx=-1; ends=0; duration=25; paused=False; remaining=0; revealed=False; round_winners=[]; round_submissions={}; started=False; auto_advance=False; categories=[]

def now():return time.monotonic()
def safe_player(p):return {'id':p['id'],'name':p['name'],'team':p['team'],'score':p['score'],'correct':p['correct'],'online':p['online']}
def scoreboard():
 scores=[{'name':t,'score':sum(p['score'] for p in players.values() if p['team']==t),'correct':sum(p['correct'] for p in players.values() if p['team']==t)} for t in TEAMS]
 return sorted(scores,key=lambda x:(-x['score'],-x['correct'],x['name']))
def seconds_left():return max(0,round(remaining if paused else ends-now(),1)) if current else 0
def state(role,pid=None):
 q=None
 if current:
  q={'index':idx+1,'total':len(order),'cat':current['cat'],'initial':current['initial'],'hint':current['hint'] if current.get('hintShown') else None,'answer':current['text'] if revealed else None,'remaining':seconds_left(),'duration':duration,'revealed':revealed,'paused':paused,'winners':round_winners}
 return {'type':'state','role':role,'q':q,'players':sorted([safe_player(p) for p in players.values()],key=lambda p:(-p['score'],p['name'])),'teams':TEAMS,'standings':scoreboard(),'started':started,'finished':started and idx==len(order)-1 and revealed,'count':len(order),'myId':pid,'submitted':round_submissions.get(pid,0),'correctMe':any(x['id']==pid for x in round_winners),'pin':PIN if role=='host' else None}
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
 idx=-1;started=True;current=None;revealed=False;paused=False;round_winners=[];round_submissions={}
 await next_question()
async def next_question():
 global idx,current,revealed,ends,paused,round_winners,round_submissions
 if not order:return
 if idx+1>=len(order):
  await broadcast({'type':'effect','kind':'finish','message':'🏆 모든 문제가 끝났습니다!'})
  return
 idx+=1;current=order[idx];revealed=False;paused=False;round_winners=[];round_submissions={};current['hintShown']=False;ends=now()+duration
 await broadcast({'type':'effect','kind':'next','message':'새 문제가 시작됐어요!'})
async def handle(ws,obj):
 global ends,paused,remaining,revealed
 act=obj.get('action');role=ws._role; pid=ws._pid
 if act=='join':
  if role=='host':return
  name=str(obj.get('name','')).strip()[:16]
  team=str(obj.get('team',''))
  token=str(obj.get('token',''))[:100]
  if not name or team not in TEAMS:return await send(ws,{'type':'error','message':'이름과 팀을 선택해 주세요.'})
  if token in players:
   p=players[token];p.update(name=name,team=team,online=True)
  else:
   token=secrets.token_urlsafe(16);players[token]={'id':token,'name':name,'team':team,'score':0,'correct':0,'online':True}
  ws._pid=token;ws._role='player'
  await send(ws,{'type':'joined','token':token});await broadcast();return
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
   round_winners.append({'id':pid,'name':p['name'],'team':p['team'],'points':points})
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
 return web.json_response({'joinUrl':BASE_URL+'/?join=1','teams':TEAMS,'categories':sorted(set(q['cat'] for q in QUESTIONS)),'questionCount':len(QUESTIONS)})
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
