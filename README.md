# 知码 · 程序员知识库

使用 Sites 托管的静态知识网站，收录用户 ti 目录中的 223 篇学习文档。

功能：四大领域、全文搜索、文章目录、代码复制、学习路径、收藏、掌握状态、学习记录、暗色模式和移动端导航。

`dist/` 为可直接部署的静态资源，不需要 Node 构建。使用 `python3 -m http.server 4173 --directory dist` 可在本地预览。

`import_content.py` 用于重新导入原目录中的 Markdown，依赖 Python markdown-it-py。导入后需重新同步和部署 Sites，源文件改动不会自动同步到线上。

收藏与学习进度只保存在浏览器 localStorage，不会跨设备同步。网站默认访问权限仅站点所有者。
