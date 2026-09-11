# -*- coding: utf-8 -*-
"""界面层：配色、样式和一堆可复用的小组件。

风格关键词：浅粉 + 薰衣草紫 + 奶油黄、圆角白卡片、柔和渐变按钮，
像两个女生一起贴贴纸做出来的手账本。
"""

from __future__ import annotations

import html
import random
from typing import Any, Dict, List, Optional

import streamlit as st

# --------------------------------------------------------------------------- #
# 常量：人物、开屏文案、选项
# --------------------------------------------------------------------------- #

APP_TITLE = "雅楠 & 玉环的小窝"
LOGO = "💗"                # 代表性 logo：粉色爱心

HER_NAME = "李玉环"        # 洛阳理工学院 · 商务英语
HER_NICK = "玉环"
ME_NAME = "孙雅楠"         # 西南民大 · 汉语言文学
ME_NICK = "楠"

# 上传 / 打卡时选择「我是谁」
PEOPLE = [f"{LOGO} {HER_NICK}（{HER_NAME}）", f"💜 {ME_NICK}（{ME_NAME}）"]

# 开屏欢迎语：每次刷新显示下一句，一轮之内不重复（顺序存在 splash_state.json）
SPLASH_LINES = [
    "想讨厌全世界，却发现这个世界还有个你",
    "如果爱是一本书，那你将是我的标题封面",
    "我们可以是彼此的第二颗心脏吗",
    "被你喜欢和喜欢你都好幸福",
    "请继续成为我生命中不可或缺的存在",
    "天天开心，My angel",
    "我们拉勾，头抵着头，发小小的誓，于是时间有了柔软的刻度",
    "用这颗心去拥抱你呀",
    "爱真好，比一切都好",
    "我们应该坐在一起发呆，发很久很久的呆。然后我说，人类好渺小啊。你说，但是，爱很伟大呀",
    "上天赐予我一段真挚的感情，赐予我可以随意依靠的肩膀",
    "幸福万万岁",
    "没什么秘诀呀，热恋期就热恋的在一起，平淡期就平淡的在一起，"
    "爱吵架就天天吵在一起，反正怎样都要在一起",
    "你的坏，你的可爱，我照单全收",
    "保持长久的羁绊唯一条件就是对方都不愿松手，如果你想松手，那我就抓得更紧一点好吗",
    "庞大的世界也稀释不了痛苦，但你能",
    "你不用道歉，学会撒娇就好了",
    "拜托拜托，请紧握这一刻",
    "承诺、诚挚、尊重、宽容、享受、珍惜、信任，是破译幸福的七个密码",
    "你没有什么要改变的，我只想爱你",
    "那我也流浪，逃去你的磁场",
    "牙齿会咬到舌头，眼睫毛偶尔刺进眼睛，我们都存在伤害彼此的可能，"
    "但我们都无法舍弃对方",
    "请你一直作为一道很深的痕迹留在我的生命里吧",
    "两颗心，在靠近",
    "爱到 1440 分钟",
    "像两个星球碰撞在瞬间融化",
    "偏偏能成为，彼此的最完美",
    "目之所及，只看背影就能找到你",
    "引来诗人提笔，老巷和风朦胧细雨",
    "不只一眼，就动心",
    "管对错，永远对我附和",
    "勇敢的你，值得更好的自己",
    "我闭上双眼迎接无尽的黑夜，因为有你，每一片雪花都有意义",
    "接受所有收获与错过",
    "大时代佩戴重生的徽章",
    "直到我的所有对策不太灵",
    "盼春草明年绿，和久别重逢的相聚",
    "想要去遥远的地方，终点是沿途的花香",
    "我把夙愿叠纸飞机飞上天",
    "相遇不一定有结局，但一定有意义",
    "小小的小孩，会完成你所有的期待",
    "涌动无声眷恋推着我向前，一年一年",
    "这一秒我就是全世界最接近幸福的一位",
    "极光像打翻的调色瓶",
    "有你陪伴的季节都是晴天",
]

# 心情选项
MOODS = [
    ("开心", "😊"),
    ("平静", "😌"),
    ("想念", "🥺"),
    ("疲惫", "😪"),
    ("难过", "😢"),
]

# 日记标签
DIARY_TAGS = ["学习日", "约会日", "想你了", "普通的一天", "见面倒计时", "心情很好"]

# 照片「报备标签」
PHOTO_TAGS = ["今天的学习桌", "路边的花", "好看的天空", "和你分享的瞬间", "今天吃了什么", "自习室的夜"]

# 消费类别
EXPENSE_CATEGORIES = ["餐饮", "交通", "学习", "购物", "其他"]

# 三餐
MEALS = [("早餐", "🍳"), ("午餐", "🍜"), ("晚餐", "🍲")]

# 倒计时可选图标
COUNTDOWN_ICONS = ["💗", "🎂", "🎓", "✈️", "💖", "📚", "🎉", "🌙"]


# --------------------------------------------------------------------------- #
# 样式
# --------------------------------------------------------------------------- #

CSS = """
<style>
/* ========== 整体：浅粉 → 薰衣草紫 → 奶油黄 的柔和渐变 ========== */
.stApp {
    background: linear-gradient(160deg, #fff5f9 0%, #f7f1ff 42%, #fffaf0 100%);
    background-attachment: fixed;
    font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
                 "Noto Sans SC", "Source Han Sans SC", sans-serif;
    color: #6b5b73;
}
.block-container { max-width: 900px; padding-top: 1.6rem; padding-bottom: 3.5rem; }

/* ========== 开屏欢迎语：居中 + 淡入上浮动画 ========== */
@keyframes splashIn {
    0%   { opacity: 0; transform: translateY(16px) scale(.98); letter-spacing: .28em; }
    60%  { opacity: 1; }
    100% { opacity: 1; transform: translateY(0) scale(1); letter-spacing: .06em; }
}
.splash {
    text-align: center;
    padding: 30px 18px 26px;
    background: linear-gradient(135deg, #ffe6f1 0%, #f0e8ff 55%, #fff6de 100%);
    border-radius: 26px;
    border: 1px solid rgba(255, 255, 255, .8);
    box-shadow: 0 10px 30px rgba(196, 160, 214, .22);
    margin-bottom: 18px;
}
.splash-text {
    /* 衬线字体更有一点点文学气，和手账风也搭 */
    font-family: "Songti SC", "STSong", "Noto Serif SC", "Source Han Serif SC",
                 "SimSun", "PingFang SC", serif;
    font-size: 1.72rem;
    font-weight: 800;
    line-height: 1.8;
    color: #8a5f9e;
    letter-spacing: .06em;
    word-break: break-word;
    animation: splashIn 1.15s cubic-bezier(.22, .9, .3, 1) both;
}
.splash-sub { margin-top: 10px; color: #b394c4; font-size: .9rem; letter-spacing: .12em; }

/* ========== 卡片 ========== */
.soft-card {
    background: #ffffff;
    border-radius: 22px;
    padding: 18px 20px;
    margin-bottom: 14px;
    border: 1px solid rgba(233, 216, 246, .9);
    box-shadow: 0 8px 22px rgba(196, 160, 214, .14);
}
.soft-card.tint { background: linear-gradient(135deg, #fff8fc, #f8f4ff); }
.soft-card.center { text-align: center; }

/* ========== 计时器 ========== */
.timer-num { font-size: 3rem; font-weight: 800; color: #c86fa6; line-height: 1.1; }
.timer-unit { font-size: 1.05rem; color: #b394c4; margin-left: .3rem; }
.timer-sub { color: #a99bb8; font-size: .9rem; margin-top: 6px; }

/* ========== 文字 ========== */
.section-title { font-size: 1.12rem; font-weight: 700; color: #8a5f9e; margin: 6px 0 10px; }
.muted { color: #a99bb8; font-size: .88rem; }
.quote-zh { font-size: 1.16rem; font-weight: 600; color: #7d5e8c; margin: .2rem 0; }
.quote-en { font-size: .94rem; color: #a99bb8; font-style: italic; margin: 0; }
.pill {
    display: inline-block; background: linear-gradient(135deg, #ffe6f1, #f0e8ff);
    color: #9a6fb0; border-radius: 999px; padding: 4px 12px;
    font-size: .84rem; font-weight: 600; margin: 3px 6px 3px 0;
}
.tag {
    display: inline-block; background: #fff6de; color: #b58a4a;
    border-radius: 999px; padding: 3px 11px; font-size: .8rem; margin-right: 6px;
}

/* ========== 记录卡片 ========== */
.rec-head { color: #b394c4; font-size: .82rem; letter-spacing: .03em; }
.rec-body { color: #6b5b73; font-size: 1rem; margin-top: 5px; line-height: 1.75; white-space: pre-wrap; }

/* ========== 三餐占位 ========== */
.plate { font-size: 2.6rem; line-height: 1.2; }

/* ========== 照片：圆角 + 轻阴影 + 悬停放大 ========== */
[data-testid="stImage"] img, .stImage img {
    border-radius: 18px;
    box-shadow: 0 6px 18px rgba(196, 160, 214, .20);
    transition: transform .28s ease, box-shadow .28s ease;
}
[data-testid="stImage"] img:hover, .stImage img:hover {
    transform: scale(1.035);
    box-shadow: 0 12px 28px rgba(196, 160, 214, .34);
}

/* ========== 按钮：柔和渐变 ========== */
div.stButton > button, div.stFormSubmitButton > button {
    width: 100%;
    border: none;
    border-radius: 16px;
    padding: .55rem 1rem;
    font-weight: 600;
    font-size: .98rem;
    color: #7a5c8a;
    background: linear-gradient(135deg, #ffe3f0 0%, #ecdfFF 60%, #fff3d8 100%);
    box-shadow: 0 4px 14px rgba(196, 160, 214, .20);
    transition: transform .15s ease, box-shadow .15s ease;
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {
    color: #6b4a7c;
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(196, 160, 214, .32);
}
/* 主按钮（打卡、提交）用更饱和的粉紫渐变 */
div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {
    background: linear-gradient(135deg, #ffb8d8 0%, #cdb4f6 100%);
    color: #5c3f6e;
}

/* ========== 输入控件 ========== */
.stTextArea textarea, .stTextInput input, .stNumberInput input,
.stDateInput input {
    border-radius: 14px !important;
    border-color: #e9d8f6 !important;
    background: #fffdfe !important;
    color: #6b5b73 !important;
}

/* ========== 进度条配色 ========== */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #ffb8d8, #cdb4f6);
}

/* ========== 隐藏默认页脚 ========== */
footer { visibility: hidden; }
</style>
"""


def inject_css() -> None:
    """注入样式（每次 rerun 都要重新注入一遍）。"""
    st.markdown(CSS, unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# 小工具
# --------------------------------------------------------------------------- #


def esc(value: Any) -> str:
    """转义用户输入，避免把 HTML 结构弄乱。"""
    return html.escape(str(value if value is not None else ""))


def card(body_html: str, extra_class: str = "") -> None:
    """渲染一张圆角白卡片。"""
    st.markdown(
        f'<div class="soft-card {extra_class}">{body_html}</div>',
        unsafe_allow_html=True,
    )


def section(title: str, icon: str = "") -> None:
    """小标题。"""
    st.markdown(
        f'<div class="section-title">{esc(icon)} {esc(title)}</div>',
        unsafe_allow_html=True,
    )


def muted(text: str) -> None:
    """灰色小字说明。"""
    st.markdown(f'<div class="muted">{esc(text)}</div>', unsafe_allow_html=True)


def flash(message: str) -> None:
    """记一条提示，rerun 之后显示（st.success 在 rerun 后就没了）。"""
    st.session_state["_flash"] = message


def show_flash() -> None:
    """显示并清空提示。"""
    message = st.session_state.pop("_flash", None)
    if message:
        card(f'<div style="text-align:center;">{esc(message)}</div>', extra_class="tint")


SPLASH_STATE = "splash_state.json"   # 记录当前轮到第几句


def next_splash_line() -> str:
    """按「打乱后的顺序」取下一句开屏语，一轮之内不会重复。

    为什么要把顺序写到文件里？因为浏览器每次刷新都会开一个新的 session，
    st.session_state 会被清空，只有落盘的顺序才能跨刷新记住「播到第几句了」。

    规则：
      * 第一次使用时把 48 句随机打乱，存下来，从第一句开始播；
      * 之后每次刷新取下一句，播完一轮重新洗牌，并且避免和上一句重复。
    """
    from storage import read_json, write_json

    total = len(SPLASH_LINES)
    state = read_json(SPLASH_STATE, {})
    if not isinstance(state, dict):
        state = {}
    order = state.get("order")
    index = int(state.get("index", 0) or 0)
    last_index = state.get("last_index")

    # 顺序缺失或内容变了（比如你改了文案条数）就重新洗牌
    if not isinstance(order, list) or sorted(order) != list(range(total)):
        order = list(range(total))
        random.shuffle(order)
        index = 0
        last_index = None

    # 一轮播完 → 重新洗牌，并保证这一轮的第一句和上一轮最后一句不同
    if index >= total:
        random.shuffle(order)
        if total > 1 and last_index is not None and order[0] == last_index:
            order[0], order[-1] = order[-1], order[0]
        index = 0

    current = order[index]
    write_json(SPLASH_STATE, {
        "order": order,
        "index": index + 1,      # 下次刷新从这里开始
        "last_index": current,
    })
    return SPLASH_LINES[current]


def splash() -> None:
    """顶部开屏欢迎语：每次刷新显示下一句 + 淡入动画。

    session_state 只负责「这次会话显示哪句」，避免点按钮时文案乱跳；
    跨刷新换句由 next_splash_line() 通过文件状态完成。
    """
    if "splash_line" not in st.session_state:
        st.session_state["splash_line"] = next_splash_line()
    line = st.session_state["splash_line"]

    # 文案长短差很多，长的自动缩小字号，保证一行到三行都好看
    if len(line) <= 14:
        size = "1.85rem"
    elif len(line) <= 26:
        size = "1.5rem"
    else:
        size = "1.12rem"

    st.markdown(
        '<div class="splash">'
        f'<div class="splash-text" style="font-size:{size};">{esc(line)}</div>'
        f'<div class="splash-sub">{LOGO} {esc(HER_NICK)} ♡ {esc(ME_NICK)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )
    # 小按钮：不想等刷新就手动看下一句
    _left, middle, _right = st.columns([2, 1, 2])
    with middle:
        if st.button("✨ 下一句", key="btn_splash"):
            st.session_state["splash_line"] = next_splash_line()
            rerun()


def rerun() -> None:
    """兼容不同版本的页面刷新。"""
    if hasattr(st, "rerun"):
        st.rerun()
    else:  # pragma: no cover
        st.experimental_rerun()


def pick_daily(items: List[Dict[str, Any]], offset: int = 0, salt: int = 0) -> Dict[str, Any]:
    """按日期抽一条内容。

    用日期做随机种子：同一天刷新结果不变，第二天自动换新。
    offset 供「换一个」按钮使用，salt 用来让不同板块互相独立。
    """
    if not items:
        return {}
    from datetime import date

    seed = date.today().toordinal() + offset * 7919 + salt * 104729
    return random.Random(seed).choice(items)


def who_am_i() -> str:
    """当前设备选的身份（玉环 / 楠）。存在 session 里，两台手机互不干扰。"""
    return st.session_state.get("who", HER_NICK)


def photo_src(relative: str) -> Optional[str]:
    """把 JSON 里的相对路径转成 st.image 能用的绝对路径；文件不在则返回 None。"""
    from storage import upload_exists, upload_path

    if not relative or not upload_exists(relative):
        return None
    return str(upload_path(relative))


def show_image(path: str) -> bool:
    """显示一张图片。

    上传的文件有可能损坏或格式不对，直接交给 st.image 会让整个页面报错，
    所以这里兜一层：显示不出来就换成占位卡片。返回是否显示成功。
    """
    try:
        # 新版 Streamlit 用 width="stretch"，旧版用 use_container_width
        try:
            st.image(path, width="stretch")
        except TypeError:
            st.image(path, use_container_width=True)
        return True
    except Exception:  # noqa: BLE001 - 坏图不该让整页崩掉
        card(
            '<div class="center"><div class="plate">🖼️</div>'
            '<div class="muted">这张图片读不出来，可能上传时损坏了</div></div>'
        )
        return False
