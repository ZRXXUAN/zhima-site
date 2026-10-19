# 知码 · 程序员知识库

前端、Flutter、Android 和算法知识网站，汇集配套 `ti` 仓库中的 223 篇 Markdown 文档。

功能包括全文搜索、领域筛选、学习路径、文章目录、代码复制、收藏、掌握状态、学习记录、深色模式与手机布局。收藏和进度保存在当前浏览器，不跨设备同步。

## 本地访问

不需要构建或安装 Node 依赖，使用 Python 3 启动：

```bash
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist
```

打开 `http://127.0.0.1:4173`。直接打开 `dist/index.html` 会受浏览器文件请求限制，请使用本地服务器或离线版。

## 离线访问

```bash
python3 export_offline.py
```

双击生成的 `offline/知码知识库.html` 即可阅读，不需要服务器和网络。全文搜索、代码复制（以浏览器权限为准）、收藏、掌握状态均保留。浏览器可能限制本地文件持久化，界面会在存储不可用时提示。

## 更新学习资料

两个仓库默认并排放置：

```text
owner/
  ti/
  zhima-site/
```

安装内容转换依赖并更新：

```bash
python3 -m pip install -r requirements.txt
python3 import_content.py
# 或指定 ti 的路径
python3 import_content.py --source /path/to/ti
```

`dist/` 是已生成的静态网站，所有资源均使用相对路径，支持部署到子目录。更新原始 Markdown 后需重新运行导入，再部署更新。

## 托管

`.openai/hosting.json` 记录原 Sites 站点身份。原网址为 `https://dev-atlas-ruixuan.daintytulip6.chatgpt.site`，访问权限仅所有者；当前网络会被该域名的 Cloudflare 服务拦截。

`dist/` 可部署到其他静态托管平台。公开托管会公开全部收录的文章，请先确认访问范围。
