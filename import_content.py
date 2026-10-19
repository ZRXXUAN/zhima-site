from pathlib import Path
import json,re,hashlib,argparse
from markdown_it import MarkdownIt
renderer=MarkdownIt('commonmark', {'html':False}).enable('table')
parser=argparse.ArgumentParser(description='从 ti 导入知码知识文档')
parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parent.parent/'ti')
args=parser.parse_args()
ROOT=args.source.expanduser().resolve()
required=['frontend-interview','flutter-interview-prep/题库','android-learning/lessons','android-interview','leetcode-hot100']
missing=[name for name in required if not (ROOT/name).is_dir()]
if missing:parser.error(f'资料目录不完整：{ROOT}，缺少 '+', '.join(missing))
OUT=Path(__file__).parent/'dist'
(OUT/'articles').mkdir(exist_ok=True,parents=True)
subjects=[('frontend','前端开发','frontend-interview','从 JavaScript 基础到 React / Vue 源码，建立完整的前端知识体系。','JS',26),('flutter','Flutter 跨端','flutter-interview-prep/题库','深入 Dart、三棵树与渲染机制，把跨端开发的原理串起来。','Fl',72),('android','Android 开发','android-learning/lessons','从 Kotlin 与生命周期出发，走向 Jetpack Compose 和完整项目。','An',19),('algorithm','算法与数据结构','leetcode-hot100','用 Hot 100 连接解题思路、复杂度分析与可运行代码。','{ }',100)]
allitems=[]
for sid,name,folder,desc,icon,_ in subjects:
 files=sorted((ROOT/folder).rglob('*.md'))
 if sid=='android':files+=sorted((ROOT/'android-interview').glob('*.md'))
 for p in files:
  rel=p.relative_to(ROOT)
  if p.name=='README.md':continue
  if p.is_relative_to(ROOT/folder) and 'learning' in p.relative_to(ROOT/folder).parts:continue
  if sid=='algorithm' and not re.match(r'\d+-',p.parent.name):continue
  body=p.read_text()
  title=next((l.lstrip('# ').strip() for l in body.splitlines() if l.startswith('# ')),p.stem)
  title=re.sub(r'^[📅📚📝🔖📖🔷📘📗🧩🟢🔴🟡⭐✅🎯\s]+','',title)
  title=re.sub(r'^Day\s*(\d+)\s*[：:—–-]\s*',r'Day \1 · ',title)
  slug=hashlib.sha1(str(rel).encode()).hexdigest()[:12]
  sub=re.sub(r'^\d+-','',p.parent.name) if p.parent!=ROOT/folder else ('核心知识' if sid=='frontend' else '开发课程')
  if p.parent.name=='android-interview':sub='面试专题'
  plain=re.sub(r'```[\s\S]*?```','',body)
  plain=re.sub(r'^\s*[#>].*$', '', plain, flags=re.M)
  plain=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',plain)
  plain=re.sub(r'[#*`>|\[\]_-]','',plain)
  summary=next((l.strip() for l in plain.splitlines() if len(l.strip())>35 and not l.startswith('http')),plain[:100])[:115]
  tags=[]
  for tag in ['JavaScript','TypeScript','React','Vue','Kotlin','Dart','Compose','Widget','Flutter','Android','Promise','HTTP','CSS','Hooks','Fiber','Riverpod']:
   if tag.lower() in (title+' '+body[:700]).lower():tags.append(tag)
  if sid=='algorithm':tags=[sub,'Hot 100']
  if not tags:tags=[sub]
  item={'id':slug,'title':title,'subject':sid,'category':sub,'tags':tags[:3],'summary':summary,'minutes':max(3,round(len(body)/850)),'source':str(rel),'order':len(allitems)}
  rendered=renderer.render(body)
  (OUT/'articles'/f'{slug}.json').write_text(json.dumps({'html':rendered,'markdown':body},ensure_ascii=False))
  allitems.append(item)
  item['_search']=body.lower()
subjectsdata=[{'id':s,'name':n,'description':d,'icon':i,'count':sum(x['subject']==s for x in allitems)} for s,n,f,d,i,c in subjects]
(OUT/'search.json').write_text(json.dumps({x['id']:x.pop('_search') for x in allitems},ensure_ascii=False))
(OUT/'data.js').write_text('window.KNOWLEDGE='+json.dumps({'subjects':subjectsdata,'articles':allitems},ensure_ascii=False)+';')
print(json.dumps({'total':len(allitems),'subjects':subjectsdata},ensure_ascii=False))
