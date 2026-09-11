#!/bin/bash
# 一键启动「雅楠 & 玉环的小窝」+ 公网隧道
#
# 用法：在「终端」里执行  bash ~/yuhuan-app/start.sh
# 看到 trycloudflare.com 的网址后，把它发给玉环就行。

cd "$(dirname "$0")" || exit 1
PORT=8505

echo "① 正在启动网站（端口 $PORT）..."
".venv/bin/streamlit" run app.py --server.headless true --server.port "$PORT" &
APP_PID=$!

sleep 8

echo "② 正在打开公网隧道，稍等十几秒会打印一个 https://xxx.trycloudflare.com 的网址"
echo "   （这个网址就是发给朋友的链接，Ctrl+C 可以全部关掉）"
echo
cloudflared tunnel --url "http://localhost:$PORT" --no-autoupdate

kill "$APP_PID" 2>/dev/null
