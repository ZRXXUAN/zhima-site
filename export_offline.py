"""Export the built website as a self-contained HTML document."""
from pathlib import Path
import argparse
import json
import re

HERE = Path(__file__).resolve().parent

def export(assets, output):
    assets, output = Path(assets), Path(output)
    content = {'articles': {p.stem: json.loads(p.read_text()) for p in (assets/'articles').glob('*.json')}, 'search': json.loads((assets/'search.json').read_text())}
    style = re.sub(r'@import url\([^;]+;', '', (assets/'style.css').read_text())
    script = 'window.ZHIMA_OFFLINE='+json.dumps(content, ensure_ascii=False)+';\n'+(assets/'data.js').read_text()+'\n'+(assets/'app.js').read_text()
    script = re.sub(r'</script', r'<\\/script', script, flags=re.I)
    page = (assets/'index.html').read_text()
    page = re.sub(r'<link rel="stylesheet"[^>]+>', lambda _: '<style>'+style+'</style>', page)
    page = re.sub(r'<link rel="icon"[^>]+>', '', page)
    page = re.sub(r'<script src="data.js[^\"]*"></script><script src="app.js[^\"]*"></script>', lambda _: '<script>'+script+'</script>', page)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding='utf-8')
    return len(content['articles'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--assets', type=Path, default=HERE/'dist')
    parser.add_argument('--output', type=Path, default=HERE/'offline'/'知码知识库.html')
    args = parser.parse_args()
    print(f'已导出 {export(args.assets,args.output)} 篇笔记：{args.output}')
