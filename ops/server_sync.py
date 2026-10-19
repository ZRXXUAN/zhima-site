#!/usr/bin/env python3
"""Pull public build output and atomically promote a validated static release."""
from pathlib import Path, PurePosixPath
import argparse
import fcntl
import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import time

PUBLIC_REPOSITORY = 'https://github.com/ZRXXUAN/zhima-site.git'

def run(*args, cwd=None):
    result = subprocess.run(args, cwd=cwd, capture_output=True, timeout=65)
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors='replace')[-1500:])
    return result.stdout

def extract_release(archive, target):
    total=0
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:') as tar:
        members=tar.getmembers()
        if len(members)>10000:raise ValueError('发布文件数量异常')
        for member in members:
            parts=PurePosixPath(member.name)
            if parts.is_absolute() or '..' in parts.parts or not (member.isfile() or member.isdir()):
                raise ValueError('发布包包含无效路径或链接')
            total+=member.size
            if total>100*1024*1024:raise ValueError('发布包超过大小限制')
            dest=target/member.name
            if member.isdir():dest.mkdir(parents=True,exist_ok=True)
            else:
                dest.parent.mkdir(parents=True,exist_ok=True)
                with tar.extractfile(member) as source,dest.open('wb') as output:shutil.copyfileobj(source,output)
                dest.chmod(0o644)
    validate(target)

def validate(target):
    for name in ['index.html','app.js','style.css','data.js','search.json','release.json']:
        if not (target/name).is_file():raise ValueError('发布包缺少 '+name)
    release=json.loads((target/'release.json').read_text())
    data=json.loads((target/'data.js').read_text().removeprefix('window.KNOWLEDGE=').removesuffix(';'))
    ids={a['id'] for a in data['articles']}
    search=json.loads((target/'search.json').read_text())
    if not ids or release['total']!=len(ids) or set(search)!=ids:raise ValueError('文章数量和搜索索引不一致')
    if {p.stem for p in (target/'articles').glob('*.json')}!=ids:raise ValueError('文章文件不完整')
    return release

def promote(release_dir,root):
    current=root/'current'
    if current.exists() and not current.is_symlink():raise ValueError('current 已存在且不是发布链接，停止替换')
    temporary=root/'.current.next'
    if temporary.is_symlink():temporary.unlink()
    elif temporary.exists():raise ValueError('临时发布链接路径已被占用')
    temporary.symlink_to(os.path.relpath(release_dir,root))
    os.replace(temporary,current)

def sync(state,root):
    state.mkdir(parents=True,exist_ok=True)
    root.mkdir(parents=True,exist_ok=True)
    with (state/'sync.lock').open('w') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return {'status':'already_running'}
        repository=state/'repository.git'
        if not repository.exists():run('git','init','--bare',str(repository))
        run('git','--git-dir',str(repository),'fetch','--depth=1','--no-tags',PUBLIC_REPOSITORY,'main')
        commit=run('git','--git-dir',str(repository),'rev-parse','FETCH_HEAD').decode().strip()
        marker=state/'current-commit'
        if marker.exists() and marker.read_text().strip()==commit and (root/'current'/'index.html').is_file():
            return {'status':'unchanged','commit':commit}
        releases=root/'releases';releases.mkdir(exist_ok=True)
        destination=releases/commit
        if not destination.exists():
            archive=run('git','--git-dir',str(repository),'archive','--format=tar',commit+':dist')
            with tempfile.TemporaryDirectory(prefix='.incoming-',dir=releases) as temp:
                staging=Path(temp)/'site';staging.mkdir()
                extract_release(archive,staging)
                staging.rename(destination)
        release=validate(destination)
        promote(destination,root)
        marker.write_text(commit+'\n')
        (state/'last-success.json').write_text(json.dumps({'commit':commit,'revision':release['revision'],'total':release['total'],'time':int(time.time())}))
        return {'status':'deployed','commit':commit,'revision':release['revision'],'total':release['total']}

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--state',type=Path,default=Path('/www/server/zhima-publisher'))
    parser.add_argument('--root',type=Path,default=Path('/www/wwwroot/8.140.56.163'))
    args=parser.parse_args()
    try:print(json.dumps(sync(args.state,args.root),ensure_ascii=False))
    except Exception as error:raise SystemExit('同步失败，继续保留上一版网站：'+str(error))
