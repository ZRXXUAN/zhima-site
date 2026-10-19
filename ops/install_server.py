#!/usr/bin/env python3
"""Install server synchronization without storing panel or GitHub credentials."""
from pathlib import Path
import argparse
import json
import re
import shutil
import subprocess
import time
from server_sync import sync,validate,promote

HERE=Path(__file__).resolve().parent

def command(*args):subprocess.run(args,check=True)

def install(root,config,nginx):
    state=Path('/www/server/zhima-publisher');state.mkdir(parents=True,exist_ok=True)
    shutil.copy2(HERE/'server_sync.py',state/'server_sync.py')
    (state/'server_sync.py').chmod(0o644)
    original=config.read_text()
    if not re.search(r'server_name\s+[^;]*8\.140\.56\.163',original):raise ValueError('站点配置不属于目标 IP，已停止')
    if not re.search(r'(?m)^\s*root\s+[^;]+;',original):raise ValueError('未找到站点根目录配置')
    result=sync(state,root)
    # A working release must exist before any Nginx configuration changes.
    release=validate(root/'current')
    backups=state/'backups';backups.mkdir(exist_ok=True)
    backup=backups/(config.name+'.'+str(int(time.time())))
    backup.write_text(original)
    updated=re.sub(r'(?m)^(\s*root\s+)[^;]+;',lambda m:m.group(1)+str(root/'current')+';',original,count=1)
    config.write_text(updated)
    try:
        command(str(nginx),'-t')
        command(str(nginx),'-s','reload')
    except BaseException:
        config.write_text(original)
        subprocess.run([str(nginx),'-t'])
        raise
    service=Path('/etc/systemd/system/zhima-sync.service')
    timer=Path('/etc/systemd/system/zhima-sync.timer')
    service.write_text('[Unit]\nDescription=Synchronize Zhima static website\nAfter=network-online.target\nWants=network-online.target\n\n[Service]\nType=oneshot\nExecStart=/usr/bin/python3 /www/server/zhima-publisher/server_sync.py --root '+str(root)+'\nTimeoutStartSec=150\nUMask=0022\n')
    timer.write_text('[Unit]\nDescription=Check Zhima website publications every minute\n\n[Timer]\nOnBootSec=30s\nOnUnitActiveSec=60s\nUnit=zhima-sync.service\n\n[Install]\nWantedBy=timers.target\n')
    command('systemctl','daemon-reload')
    command('systemctl','enable','--now','zhima-sync.timer')
    print(json.dumps({'status':'installed','url':'http://8.140.56.163/','revision':release['revision'],'total':release['total'],'previous_nginx_config':str(backup),'sync':result},ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path('/www/wwwroot/8.140.56.163'))
    parser.add_argument('--config',type=Path,default=Path('/www/server/panel/vhost/nginx/8.140.56.163.conf'))
    parser.add_argument('--nginx',type=Path,default=Path('/www/server/nginx/sbin/nginx'))
    args=parser.parse_args()
    install(args.root,args.config,args.nginx)
