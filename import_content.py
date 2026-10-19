"""Build the complete static website from configured Markdown sources."""
from pathlib import Path, PurePosixPath
import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from markdown_it import MarkdownIt

HERE = Path(__file__).resolve().parent
KEYWORDS = ['JavaScript','TypeScript','React','Vue','Kotlin','Dart','Compose','Widget','Flutter','Android','Promise','HTTP','CSS','Hooks','Fiber','Riverpod']

def valid_pattern(value):
    if not isinstance(value, str) or not value or PurePosixPath(value).is_absolute() or '..' in PurePosixPath(value).parts:
        raise ValueError(f'配置中包含无效的相对路径：{value!r}')
    return value

def load_config(path):
    config = json.loads(path.read_text(encoding='utf-8'))
    subjects = config.get('subjects', [])
    if not subjects:
        raise ValueError('至少需要配置一个知识模块')
    ids = set()
    for subject in subjects:
        sid = subject.get('id', '')
        if not re.fullmatch(r'[a-z][a-z0-9_-]*', sid) or sid == 'all' or sid in ids:
            raise ValueError(f'模块 id 无效或重复：{sid}')
        ids.add(sid)
        for field in ['name', 'description', 'icon']:
            if not isinstance(subject.get(field), str) or not subject[field]:
                raise ValueError(f'模块 {sid} 缺少 {field}')
        if not subject.get('include'):
            raise ValueError(f'模块 {sid} 缺少 include 路径')
        for pattern in subject['include']:
            valid_pattern(pattern)
        if not isinstance(subject.get('stages', []), list):
            raise ValueError(f'模块 {sid} 的 stages 必须是数组')
    for pattern in config.get('exclude', []):
        valid_pattern(pattern)
    return config

def article_metadata(path, source, subject, body, order):
    relative = path.relative_to(source).as_posix()
    title = next((line[2:].strip() for line in body.splitlines() if line.startswith('# ')), path.stem)
    title = re.sub(r'^[📅📚📝🔖📖🔷📘📗🧩🟢🔴🟡⭐✅🎯\s]+', '', title)
    title = re.sub(r'^Day\s*(\d+)\s*[：:—–-]\s*', r'Day \1 · ', title)
    category = re.sub(r'^\d+-', '', path.parent.name)
    if path.parent.name in ('frontend-interview', 'lessons'):
        category = subject.get('defaultCategory', '知识笔记')
    if path.parent.name == 'android-interview':
        category = '面试专题'
    plain = re.sub(r'```[\s\S]*?```', '', body)
    plain = re.sub(r'^\s*[#>].*$', '', plain, flags=re.M)
    plain = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', plain)
    plain = re.sub(r'[#*`>|\[\]_-]', '', plain)
    summary = next((line.strip() for line in plain.splitlines() if len(line.strip()) > 35 and not line.startswith('http')), plain[:100])[:115]
    tags = [tag for tag in KEYWORDS if tag.lower() in (title+' '+body[:700]).lower()]
    if subject.get('tags'):
        tags = [category, *subject['tags']]
    return {
        'id': hashlib.sha1(relative.encode()).hexdigest()[:12], 'title': title,
        'subject': subject['id'], 'category': category, 'tags': (tags or [category])[:3],
        'summary': summary, 'minutes': max(3, round(len(body)/850)),
        'source': relative, 'order': order,
    }

def build(source, output, config_path=None, static_path=None, source_commit=None):
    source, output = Path(source).resolve(), Path(output).resolve()
    config_path = Path(config_path or HERE/'subjects.json').resolve()
    static_path = Path(static_path or HERE/'static').resolve()
    if not source.is_dir():
        raise ValueError(f'资料目录不存在：{source}')
    if output == source or output in source.parents or output == static_path or output in static_path.parents:
        raise ValueError('输出目录不能覆盖资料或模板目录')
    config = load_config(config_path)
    digest = hashlib.sha256(config_path.read_bytes()+Path(__file__).read_bytes())
    renderer = MarkdownIt('commonmark', {'html': False}).enable('table')
    documents, search, subjects, claimed = {}, {}, [], set()
    for definition in config['subjects']:
        matches = set()
        for pattern in definition['include']:
            matches.update(source.glob(pattern))
        selected = []
        for path in sorted(matches):
            if path.suffix.lower() != '.md' or not path.is_file():
                continue
            if not path.resolve().is_relative_to(source):
                raise ValueError(f'资料链接指向仓库外部：{path}')
            relative = path.relative_to(source).as_posix()
            if any(part.startswith('.') for part in path.relative_to(source).parts):
                continue
            if any(fnmatch.fnmatch(relative, pattern) for pattern in config.get('exclude', [])):
                continue
            if relative in claimed:
                raise ValueError(f'一篇资料被多个模块重复收录：{relative}')
            claimed.add(relative)
            selected.append(path)
        if not selected:
            raise ValueError(f'模块 {definition["id"]} 没有匹配到文章，请检查 include')
        for path in selected:
            body = path.read_text(encoding='utf-8')
            item = article_metadata(path, source, definition, body, len(documents))
            if item['id'] in documents:
                raise ValueError(f'文章 ID 冲突：{item["source"]}')
            digest.update(item['source'].encode()+b'\0'+body.encode())
            documents[item['id']] = {'item': item, 'html': renderer.render(body), 'markdown': body}
            search[item['id']] = body.lower()
        subjects.append({key: definition[key] for key in ('id','name','description','icon')})
        subjects[-1].update(count=len(selected), stages=definition.get('stages', ['基础知识','进阶原理','实践应用']))
    for path in sorted(static_path.rglob('*')):
        if path.is_file():
            digest.update(path.relative_to(static_path).as_posix().encode()+b'\0'+path.read_bytes())
    revision = digest.hexdigest()[:16]
    payload = {'revision': revision, 'subjects': subjects, 'articles': [d['item'] for d in documents.values()], 'featured': config.get('featured', [])}
    release = {'version': 1, 'revision': revision, 'sourceCommit': source_commit, 'total': len(documents), 'subjects': [{'id': s['id'], 'count': s['count']} for s in subjects]}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.zhima-build-', dir=output.parent) as temp:
        staging = Path(temp)/'site'
        shutil.copytree(static_path, staging)
        (staging/'articles').mkdir(exist_ok=True)
        for aid, document in documents.items():
            (staging/'articles'/f'{aid}.json').write_text(json.dumps({k: document[k] for k in ('html','markdown')}, ensure_ascii=False), encoding='utf-8')
        (staging/'data.js').write_text('window.KNOWLEDGE='+json.dumps(payload, ensure_ascii=False)+';', encoding='utf-8')
        (staging/'search.json').write_text(json.dumps(search, ensure_ascii=False), encoding='utf-8')
        (staging/'release.json').write_text(json.dumps(release, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        (staging/'.nojekyll').touch()
        html = (staging/'index.html').read_text(encoding='utf-8')
        for key, value in {'article_count': len(documents), 'subject_count': len(subjects), 'subject_count_pad': str(len(subjects)).zfill(2), 'revision': revision}.items():
            html = html.replace('{{'+key+'}}', str(value))
        if re.search(r'\{\{\w+\}\}', html):
            raise ValueError('首页模板含有未替换的构建变量')
        (staging/'index.html').write_text(html, encoding='utf-8')
        # Only swap complete builds; invalid input never replaces a working site.
        previous = Path(temp)/'previous'
        if output.exists():
            output.rename(previous)
        try:
            staging.rename(output)
        except BaseException:
            if previous.exists():
                previous.rename(output)
            raise
    return release

def main():
    parser = argparse.ArgumentParser(description='一次构建知码网站：资料、模块、搜索索引与版本信息')
    parser.add_argument('--source', type=Path, default=HERE.parent)
    parser.add_argument('--output', type=Path, default=HERE/'dist')
    parser.add_argument('--config', type=Path, default=HERE/'subjects.json')
    parser.add_argument('--revision', help='源仓库提交 SHA，用于追踪发布来源')
    args = parser.parse_args()
    try:
        result = build(args.source, args.output, args.config, source_commit=args.revision)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        parser.exit(1, f'构建失败：{error}\n')
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    main()
