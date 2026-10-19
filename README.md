# 知码 · 程序员知识库

在线阅读：[服务器主站](http://8.140.56.163/) · [GitHub Pages 备用站](https://zrxxuan.github.io/zhima-site/)

这是由 [ZRXXUAN/ti](https://github.com/ZRXXUAN/ti) 自动生成的**公开网站镜像**。原始资料与网站源码统一在私有 `ti` 仓库维护；本仓库包含获准公开的内容、静态页面与构建脚本。

## 两人共同维护与一键更新

请在 `ti` 仓库修改：

- 题库和笔记：原有 `frontend-interview/`、`flutter-interview-prep/` 等目录。
- 页面或功能：`website/static/`。
- 知识模块与学习路径：`website/subjects.json`。

推送或合并到 `ti/main` 后，GitHub Actions 自动完成：验证 → 导入文章 → 更新模块数量和搜索索引 → 同步本仓库 → 发布网站。也可以运行 `ti/publish.sh` 或双击 `ti/一键发布网站.command`，并在 `ti` 的 Actions 页面手动重新发布。

**请勿直接在此镜像修改代码**，后续自动发布会以 `ti` 中的版本为准。

## 本地浏览与离线导出

已有构建无需安装依赖：

```bash
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist
```

打开 `http://127.0.0.1:4173`。导出单文件离线版：

```bash
python3 export_offline.py
```

更新构建需要 Python 依赖，并显式指定原始资料目录：

```bash
python3 -m pip install -r requirements.txt
python3 import_content.py --source ../ti --output dist
```

收藏与进度保存在浏览器；原文路径相同时，文章 ID 保持不变。`dist/release.json` 记录内容版本与发布来源。每次构建全量更新索引，并移除已删除的文章；校验失败不会替换上一份可用构建。

原 Sites 站点身份保留在 `.openai/hosting.json`，其访问权限不变。

## 服务器同步

服务器使用 `ops/server_sync.py` 获取本仓库 `main` 分支中的 `dist/`。同步器只提取静态文件，校验完整后切换 `current` 软链接；拉取或校验失败时继续使用上一版，不需要保存个人 GitHub 令牌。

配套 `zhima-sync.timer` 每分钟检查一次发布。查看状态：

```bash
systemctl status zhima-sync.timer
journalctl -u zhima-sync.service -n 30
```

原站点 Nginx 配置的备份记录在 `/www/server/zhima-publisher/backups/`，已发布版本保留在站点的 `releases/` 目录。
