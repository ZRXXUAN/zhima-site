#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo '请先提交网站改动，再发布 GitHub Pages。' >&2
  exit 1
fi
site_commit=$(git subtree split --prefix=dist HEAD)
git push origin "$site_commit:refs/heads/gh-pages"
echo '静态网站已推送到 gh-pages。GitHub Pages 构建完成后可访问线上网站。'
