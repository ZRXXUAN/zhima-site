"""Create a self-contained HTML knowledge base that works from file://."""
from pathlib import Path
import argparse,json,re
root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description='导出无网络也可阅读的知码知识库')
parser.add_argument('--output', type=Path, default=root/'offline'/'知码知识库.html')
args=parser.parse_args()
assets=root/'dist'
articles={p.stem:json.loads(p.read_text()) for p in (assets/'articles').glob('*.json')}
search=json.loads((assets/'search.json').read_text())
style=(assets/'style.css').read_text()
style=re.sub(r"@import url\([^;]+;",'',style)
app=(assets/'app.js').read_text()
app=app.replace('await fetch(`articles/${id}.json`)', '({ok:true,json:async()=>OFFLINE_ARTICLES[id]})')
app=app.replace("await fetch('search.json')", '({ok:true,json:async()=>OFFLINE_SEARCH})')
data='const OFFLINE_ARTICLES='+json.dumps(articles,ensure_ascii=False)+';\nconst OFFLINE_SEARCH='+json.dumps(search,ensure_ascii=False)+';\n'+(assets/'data.js').read_text()+'\n'+app
data=data.replace('</script','<\\/script')
page=(assets/'index.html').read_text()
page=page.replace('<link rel="stylesheet" href="style.css">','<style>'+style+'</style>')
page=re.sub(r'<link rel="icon"[^>]*>','',page)
page=page.replace('<script src="data.js"></script><script src="app.js"></script>','<script>'+data+'</script>')
page=page.replace('<title>知码 · 程序员知识库</title>','<title>知码 · 离线知识库</title>')
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(page)
print(f'已导出 {len(articles)} 篇知识笔记：{args.output}')
