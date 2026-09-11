# 雅楠 & 玉环的小窝 💗

两个异地恋女生的专属网页小应用：**洛阳理工学院的玉环（李玉环）** 和 **西南民大的楠（孙雅楠）**，
隔着 900 多公里，用手机浏览器打开同一个网址，记录日常、互相陪伴。代表性的 logo 是一颗粉色爱心 💗。

配色是浅粉 + 薰衣草紫 + 奶油黄，圆角白卡片、柔和渐变按钮，像两个人一起做的手账本。

## 九个页面

| 页面 | 有什么 |
| --- | --- |
| 🏠 我们的小窝 | 「在一起 XX 天」计时器（默认从 2022-09-01 算）＋ 早安/晚安打卡，打卡后随机送一句中英双语语录 |
| 💗 今天心情 | 开心 😊 平静 😌 想念 🥺 疲惫 😪 难过 😢 五个心情按钮 ＋「今天想说的话」＋ 最近记录 |
| 📔 我们的故事 | 写日记（自动记日期时间）、贴今日标签（学习日 / 约会日 / 想你了…）、按标签回看 |
| 🍽️ 一日三餐 | 早/午/晚三格，各上传一张照片 + 一句描述；没打卡时是可爱的空盘子占位 |
| 🖼️ 照片墙 | 照片 + 报备标签（今天的学习桌 / 路边的花 / 好看的天空…），网格瀑布流、按日期和上传者筛选、点开放大、可删除 |
| 💰 记账本 | 金额 + 类别（餐饮/交通/学习/购物/其他）+ 备注，今日总花费、每笔明细、按月汇总 |
| ⏳ 期待与你相见 | 多个倒计时卡片（下次见面 / 生日 / 纪念日），显示「还有 XX 天 XX 小时」，可加可删 |
| 📚 一起变优秀 | 玉环的英语角（60 个商务英语表达，含释义、例句、「我记住了」计数）＋ 楠的文学角（75 句诗词名句 + 赏析 + 「抄写一遍」并保存抄写记录） |
| 🐣 今天也要加油鸭 | 两个人的每日任务清单，勾选后带删除线、进度条、跨天自动重置，还能看到对方完成了几条 |

页面顶部有一个开屏语轮播，内置 **45 句**你们之间的文案（「想讨厌全世界，却发现这个世界
还有个你」「爱真好，比一切都好」「幸福万万岁」…）。规则是：**每次刷新显示下一句，
一轮 45 句播完之前不会重复**——首次使用时把 45 句随机打乱存进
`data/splash_state.json`，之后每刷新一次取下一句，播完一轮重新洗牌（并避免和上一句
撞车）。文案带淡入上浮动画，长短不一的行会自动调整字号，旁边还有「✨ 下一句」小按钮。

## 一、本地运行

需要 Python 3.9 以上。

```bash
cd ~/couple-app

# 1. 建虚拟环境（只做一次）
python3 -m venv .venv

# 2. 装依赖（只做一次）
.venv/bin/pip install -r requirements.txt

# 3. 启动
.venv/bin/streamlit run app.py
```

浏览器会自动打开 <http://localhost:8501>。

## 二、让手机也能打开

### 同一 Wi-Fi（最快）

```bash
.venv/bin/streamlit run app.py --server.address 0.0.0.0 --server.port 8501
ipconfig getifaddr en0     # macOS 查本机 IP，比如 192.168.1.8
```

手机浏览器打开 `http://192.168.1.8:8501` 即可（电脑要保持开机并运行着命令）。
想真正做到异地随时打开，就往下看部署部分。

## 三、目录结构

```
couple-app/
├── app.py                  # 入口：导航、侧边栏、页面分发
├── views.py                # 九个页面的具体实现
├── ui.py                   # 配色样式 + 卡片/按钮等小组件
├── storage.py              # 数据层：JSON 读写、图片保存、日期工具
├── data/
│   ├── quotes.json             # 中英双语语录（静态内容，可以自己加）
│   ├── business_phrases.json   # 60 个商务英语表达
│   ├── poems.json              # 75 句诗词 + 赏析
│   └── （其余 JSON 运行时自动生成：打卡/心情/日记/三餐/照片/记账/倒计时/学习/任务，
│        以及记录开屏语轮播进度的 splash_state.json）
├── uploads/                # 上传的图片（按 meals/、photos/ 分目录）
├── tests/test_couple_app.py
├── requirements.txt
└── README.md
```

数据规则：**文字记录存 JSON，图片存 uploads/，JSON 里只保存图片路径**。
每次写入都是「先写临时文件再整体替换」的原子操作，写一半断电也不会把数据写坏。

## 四、部署到公网（GitHub + Streamlit Cloud）

### 第 1 步：把项目传到 GitHub

1. 注册/登录 <https://github.com>，点右上角 `+` → `New repository`，
   仓库名填 `couple-app`，**选择 Private（私有）**，不要勾选 Add README。创建后复制仓库地址备用。

2. 在电脑上初始化 git 并推送（把下面的地址换成你自己的）：

   ```bash
   cd ~/couple-app
   git init
   git add app.py views.py ui.py storage.py requirements.txt README.md .gitignore \
           data/quotes.json data/business_phrases.json data/poems.json
   git commit -m "我们的专属小窝"
   git branch -M main
   git remote add origin git@github.com:你的用户名/couple-app.git
   git push -u origin main
   ```

   > 注意**不要**用 `git add -A`：`.gitignore` 已经把 `uploads/` 和两个人的
   > 私人记录（日记、照片索引、记账…）排除掉了，这样仓库里只有代码和内容库。
   >
   > 没配过 SSH 的话，用 HTTPS 地址 `https://github.com/你的用户名/couple-app.git` 也行，
   > 推送时会让你输入 GitHub 用户名和 **Personal Access Token**（在
   > GitHub → Settings → Developer settings → Personal access tokens 里生成，勾选 repo 权限）。

### 第 2 步：在 Streamlit Cloud 上部署

1. 打开 <https://share.streamlit.io>，用 **GitHub 账号登录**，点 `Create app`（或 `New app`）。
2. 依次选择：
   - `Repository`：你的用户名/couple-app
   - `Branch`：main
   - `Main file path`：`app.py`
   - （可选）`Advanced settings` → Python version 选 3.11 或 3.12
3. 点 `Deploy!`，等 1～3 分钟，页面顶部会出现一个网址，形如
   `https://couple-app-xxxx.streamlit.app`。
4. 把这个网址发给对方，**手机浏览器打开 → 分享 → 添加到主屏幕**，
   就是一个能和 App 一样点开的小图标，异地随时都能打开。

以后改动代码只要 `git push`，云端会自动重新部署。

### ⚠️ 第 3 步：一定要知道的数据真相

Streamlit Cloud 的容器是**临时的**：应用休眠、重新部署、平台维护重启之后，
运行期间写进去的数据（打卡、日记、照片、记账、任务…）**会全部消失**，
回到仓库里的初始状态。这是免费平台的限制，不是程序的 bug。

| 方案 | 做法 | 适合 |
| --- | --- | --- |
| A. 定期备份 | 侧边栏点「⬇️ 下载全部记录（JSON）」存到本地；想恢复就把文件内容贴回 `data/` 下对应文件再 `git push` | 先玩起来，记录不多 |
| B. 接外部存储（推荐长期用） | 用免费的 Supabase（PostgreSQL）或 GitHub Gist 存数据：只要改 `storage.py` 里的 `read_json` / `write_json` 两个函数，其余代码一行都不用动；图片可用 Supabase Storage 或图床 | 想长期积累回忆 |
| C. 国内云服务器 | 阿里云/腾讯云轻量服务器（2核2G，约 ¥60～100/年）+ systemd 常驻 + Nginx 反代（要开 WebSocket）+ certbot 免费 HTTPS。数据在自己的硬盘上，不会丢，国内访问也更快 | 想要稳定 + 快 |

方案 C 的关键配置（Streamlit 必须走 WebSocket，`proxy_set_header Upgrade` 那几行不能省）：

```nginx
server {
    listen 80;
    server_name 你的域名;
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

### 第 4 步（建议）：给网站加个暗号

公网地址只要被人拿到就能打开，日记和照片都是很私密的东西，建议加一道口令：

1. 在项目里新建 `.streamlit/secrets.toml`（已被 .gitignore 排除）：

   ```toml
   APP_PASSWORD = "你俩才知道的暗号"
   ```

2. 在 `app.py` 的 `main()` 函数**最前面**加几行：

   ```python
   pwd = st.text_input("输入我们的暗号 🔒", type="password")
   if pwd != st.secrets.get("APP_PASSWORD", ""):
       st.stop()
   ```

3. 部署到 Streamlit Cloud 时，在应用的 `Settings → Secrets` 里填上同样的内容。

## 五、想改内容/样式？

| 想改什么 | 改哪里 |
| --- | --- |
| 语录 | `data/quotes.json`（`zh` 中文、`en` 英文） |
| 商务英语短语 | `data/business_phrases.json`（注意保持 JSON 格式，逗号别漏） |
| 诗句和赏析 | `data/poems.json` |
| 心情选项 / 日记标签 / 消费类别 / 倒计时图标 | `ui.py` 顶部常量（`MOODS`、`DIARY_TAGS`、`EXPENSE_CATEGORIES`、`COUNTDOWN_ICONS`） |
| 配色、圆角、按钮渐变 | `ui.py` 里的 `CSS`（背景看 `.stApp`，卡片看 `.soft-card`，按钮看 `div.stButton > button`） |
| 开屏语 | `ui.py` 里的 `SPLASH_LINES`（想加几句直接往列表里塞，程序发现条数变了会自动重新洗牌） |
| 纪念日 | 网页左侧边栏直接改，会存进 `data/config.json` |

## 六、常见问题

**照片传不上去 / 页面卡住**：手机拍的原图常常有 3～8MB，先压缩再传会顺畅很多。
Streamlit 默认单文件上限 200MB，可在 `.streamlit/config.toml` 里调。

**手机打不开局域网地址**：确认手机和电脑连同一个 Wi-Fi；启动时带了
`--server.address 0.0.0.0`；macOS 首次会弹窗问是否允许 Python 接受网络连接，要点「允许」。

**点了按钮页面会不会跳回第一页**：不会。导航用的是顶部下拉框（`st.selectbox`），
状态会保留，切换页面后再操作也不会被弹回去。

**任务为什么第二天自动变回未完成**：完成状态是按日期存的（`task_done.json`），
新的一天自然就没有记录，相当于自动重置。

**数据在哪、怎么备份**：`data/*.json`（文字）和 `uploads/`（图片）。
侧边栏有「下载全部记录」按钮可以一键导出。

## 七、开发者：跑测试

```bash
.venv/bin/python -m unittest discover -s tests -v
```

测试用 Streamlit 官方的 `AppTest` 把九个页面真跑一遍（打卡写文件、心情、日记、
记账、倒计时增删、学习计数、任务勾选与跨天重置、照片与三餐的保存和图片替换……），
数据写在临时目录里，不会碰你的真实记录。
