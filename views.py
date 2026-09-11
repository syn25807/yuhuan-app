# -*- coding: utf-8 -*-
"""九个页面的具体实现。

页面清单：
    1. 我们的小窝   —— 计时器 + 早安/晚安打卡 + 双语语录
    2. 今天心情     —— 心情选项 + 想说的话
    3. 我们的故事   —— 日记 + 今日标签
    4. 一日三餐     —— 早/午/晚三张照片打卡
    5. 照片墙       —— 带报备标签的相册，可筛选、可放大
    6. 记账本       —— 今日花费 + 按月查看
    7. 期待与你相见 —— 多个倒计时事件
    8. 一起变优秀   —— 英语角 + 文学角
    9. 今天也要加油鸭 —— 两个人的每日任务清单
"""

from __future__ import annotations

import random
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import streamlit as st

import storage as db
from ui import (
    APP_TITLE,
    COUNTDOWN_ICONS,
    DIARY_TAGS,
    EXPENSE_CATEGORIES,
    HER_NAME,
    HER_NICK,
    LOGO,
    MEALS,
    ME_NAME,
    ME_NICK,
    MOODS,
    PHOTO_TAGS,
    card,
    esc,
    flash,
    muted,
    photo_src,
    pick_daily,
    rerun,
    section,
    show_image,
    who_am_i,
)


# --------------------------------------------------------------------------- #
# 页面一：我们的小窝
# --------------------------------------------------------------------------- #


def do_checkin(kind: str, label: str, icon: str) -> None:
    """打卡：记录时间，并随机附赠一句中英双语语录。"""
    quotes = db.read_json("quotes.json", [])
    quote = random.choice(quotes) if quotes else {"zh": "今天也要开心呀", "en": "Be happy today."}
    record = db.now_stamp()
    record.update({
        "id": db.new_id(),
        "type": kind,            # morning / night
        "label": label,          # 早安 / 晚安
        "icon": icon,
        "who": who_am_i(),       # 是谁打的卡
        "quote_zh": quote.get("zh", ""),
        "quote_en": quote.get("en", ""),
    })
    db.append_json(db.CHECKINS, record)
    flash(f"{icon} {label}打卡成功啦，今天也被好好记下来了 ♡")
    rerun()


def page_home() -> None:
    """首页：计时器 + 早安/晚安打卡 + 语录。"""
    since = db.together_since()
    passed = db.days_together()
    today = db.today_str()
    checkins = db.read_json(db.CHECKINS, [])
    today_recs = [c for c in checkins if c.get("date") == today]

    def latest(kind: str) -> Optional[Dict[str, Any]]:
        return next((c for c in reversed(today_recs) if c.get("type") == kind), None)

    # ---- 标题 ---- #
    card(
        f'<div class="center"><h2 style="margin:0 0 6px;color:#8a5f9e;letter-spacing:.06em;">'
        f"{esc(APP_TITLE)}</h2>"
        f'<div class="muted">洛阳 · 成都，隔着 900 多公里，也在好好相爱</div></div>',
        extra_class="tint",
    )

    # ---- 在一起天数计时器 ---- #
    card(
        '<div class="center">'
        f'<div class="timer-num">{passed:,}<span class="timer-unit">天</span></div>'
        f'<div class="timer-sub">已经在一起 {passed:,} 天 · 今天是第 {passed + 1:,} 天</div>'
        f'<div class="timer-sub">从 {since.strftime("%Y 年 %m 月 %d 日")} 开始 ♡</div>'
        "</div>"
    )

    # ---- 早安 / 晚安打卡 ---- #
    section("今日打卡", "🫶")
    left, right = st.columns(2)
    for col, kind, label, icon in (
        (left, "morning", "早安", "☀️"),
        (right, "night", "晚安", "🌙"),
    ):
        with col:
            rec = latest(kind)
            if rec:
                card(
                    f'<div class="center">{icon} {esc(label)}已打卡'
                    f'<div class="muted">{esc(rec.get("time", ""))} · {esc(rec.get("who", ""))}</div></div>'
                )
            elif st.button(f"{icon} {label}打卡", type="primary", key=f"btn_{kind}"):
                do_checkin(kind, label, icon)

    # ---- 今日语录 ---- #
    quote = None
    for rec in reversed(today_recs):
        if rec.get("quote_zh"):
            quote = {"zh": rec["quote_zh"], "en": rec.get("quote_en", "")}
            break
    if quote is None:
        quote = pick_daily(db.read_json("quotes.json", []))
    if quote:
        card(
            '<div class="muted">今日语录</div>'
            f'<p class="quote-zh">「{esc(quote.get("zh", ""))}」</p>'
            f'<p class="quote-en">{esc(quote.get("en", ""))}</p>'
        )

    # ---- 打卡小档案 ---- #
    if checkins:
        days_count = len({c.get("date") for c in checkins})
        morning = sum(1 for c in checkins if c.get("type") == "morning")
        night = sum(1 for c in checkins if c.get("type") == "night")
        card(
            '<div class="muted">打卡小档案</div>'
            f'<p class="rec-body">已经有 <b>{days_count}</b> 天留下记录 · '
            f"早安 <b>{morning}</b> 次 · 晚安 <b>{night}</b> 次</p>"
        )


# --------------------------------------------------------------------------- #
# 页面二：今天心情如何
# --------------------------------------------------------------------------- #


def save_mood(mood: str, emoji: str) -> None:
    """记录一次心情。"""
    record = db.now_stamp()
    record.update({"id": db.new_id(), "mood": mood, "emoji": emoji, "who": who_am_i()})
    db.append_json(db.MOODS, record)
    flash(f"{emoji} 已记下「{mood}」这个心情，谢谢你愿意告诉我 ♡")
    rerun()


def save_note_callback() -> None:
    """保存「今天想说的话」。

    放在 on_click 回调里做，因为 Streamlit 不允许在同一个 run 中、
    控件创建之后再改它的 session_state（保存完要清空输入框）。
    """
    text = (st.session_state.get("note_input") or "").strip()
    if not text:
        flash("📝 先写点什么再保存吧～")
        return
    record = db.now_stamp()
    record.update({"id": db.new_id(), "who": who_am_i(), "text": text})
    db.append_json(db.MOODS, record)   # 和心情存在同一个文件，靠 kind 区分
    st.session_state["note_input"] = ""
    flash("💌 已经收好了，我会好好保管。")


def page_mood() -> None:
    """心情页：选心情 + 写想说的话 + 看最近记录。"""
    section("今天心情如何？", "💗")
    muted("点一下最像今天的那一个就好。")
    st.write("")

    cols = st.columns(len(MOODS))
    for col, (name, emoji) in zip(cols, MOODS):
        if col.button(f"{emoji} {name}", key=f"mood_{name}"):
            save_mood(name, emoji)

    records = db.read_json(db.MOODS, [])
    today = db.today_str()
    today_mood = next(
        (r for r in reversed(records) if r.get("date") == today and r.get("mood")), None
    )
    if today_mood:
        card(
            '<div class="center">今天记录的心情是 '
            f'<span class="pill">{esc(today_mood.get("emoji", ""))} {esc(today_mood.get("mood", ""))}</span>'
            f'<div class="muted">{esc(today_mood.get("time", ""))} 记录</div></div>',
            extra_class="tint",
        )

    st.write("")
    section("今天想说的话", "✍️")
    text = st.text_area(
        "今天想说的话",
        height=120,
        key="note_input",
        label_visibility="collapsed",
        placeholder="开心的、委屈的、想吃的、想去的……都可以写在这里",
    )
    st.button("💌 保存这句话", key="btn_save_note", on_click=save_note_callback)

    notes = [r for r in records if r.get("text")]
    if notes:
        st.write("")
        section("最近的心里话", "💬")
        for n in list(reversed(notes))[:5]:
            card(
                f'<div class="rec-head">{esc(db.pretty_date(n.get("date", "")))} '
                f'{esc(n.get("time", ""))} · {esc(n.get("who", ""))}</div>'
                f'<div class="rec-body">{esc(n.get("text", ""))}</div>'
            )

    mood_records = [r for r in records if r.get("mood")]
    if mood_records:
        st.write("")
        section("最近的心情", "🫧")
        for m in list(reversed(mood_records))[:8]:
            card(
                f'<div class="rec-head">{esc(db.pretty_date(m.get("date", "")))} '
                f'{esc(m.get("time", ""))} · {esc(m.get("who", ""))}</div>'
                f'<div class="rec-body">{esc(m.get("emoji", ""))} {esc(m.get("mood", ""))}</div>'
            )


# --------------------------------------------------------------------------- #
# 页面三：我们的故事（日记）
# --------------------------------------------------------------------------- #


def page_diary() -> None:
    """日记页：写当天日记 + 今日标签 + 历史日记卡片。"""
    diaries = db.read_json(db.DIARIES, [])

    section("今天的故事", "📔")
    with st.form("diary_form", clear_on_submit=True):
        col1, col2 = st.columns([1, 1])
        day = col1.date_input("日期", value=date.today())
        who = col2.selectbox("谁写的", [HER_NICK, ME_NICK], index=0 if who_am_i() == HER_NICK else 1)
        tags = st.multiselect("今日标签", DIARY_TAGS + ["自定义"])
        custom_tag = st.text_input("自定义标签（可留空）", placeholder="比如：第一次一起看演唱会")
        text = st.text_area(
            "今天发生了什么",
            height=220,
            placeholder="今天上了什么课、吃了什么、想对她说的话……",
        )
        submitted = st.form_submit_button("📖 保存这篇日记", type="primary")

    if submitted:
        final_tags = [t for t in tags if t != "自定义"]
        if custom_tag.strip():
            final_tags.append(custom_tag.strip())
        if not text.strip():
            st.warning("先写一点内容再保存吧～")
        else:
            record = db.now_stamp()
            record.update({
                "id": db.new_id(),
                "date": day.isoformat(),      # 用选择的日期，可以补写以前的日记
                "who": who,
                "tags": final_tags,
                "text": text.strip(),
            })
            db.append_json(db.DIARIES, record)
            flash("📖 这篇日记已经收进我们的故事里啦。")
            rerun()

    if not diaries:
        muted("还没有日记，写下第一篇吧～")
        return

    # ---- 历史日记：按日期倒序 ---- #
    st.write("")
    section("我们的故事本", "📚")
    all_tags = sorted({t for d in diaries for t in d.get("tags", [])})
    picked = st.multiselect("按标签筛选（可多选）", all_tags)
    shown = [
        d for d in sorted(diaries, key=lambda x: (x.get("date", ""), x.get("ts", "")), reverse=True)
        if not picked or set(picked) & set(d.get("tags", []))
    ]
    muted(f"共 {len(shown)} 篇")
    for d in shown:
        tags_html = "".join(f'<span class="tag">{esc(t)}</span>' for t in d.get("tags", []))
        card(
            f'<div class="rec-head">{esc(db.pretty_date(d.get("date", "")))} '
            f'{esc(d.get("time", ""))} · {esc(d.get("who", ""))}</div>'
            f"<div style='margin:6px 0;'>{tags_html}</div>"
            f'<div class="rec-body">{esc(d.get("text", ""))}</div>'
        )


# --------------------------------------------------------------------------- #
# 页面四：一日三餐
# --------------------------------------------------------------------------- #


def save_meal(meal: str, day: str, uploaded, desc: str, who: str) -> None:
    """保存一餐：同一天同一餐只留最新的一条（旧图会一起删掉）。"""
    meals = db.read_json(db.MEALS, [])
    # 先删掉这一天这一餐的旧记录
    for old in [m for m in meals if m.get("date") == day and m.get("meal") == meal]:
        db.delete_upload(old.get("path", ""))
    meals = [m for m in meals if not (m.get("date") == day and m.get("meal") == meal)]

    path = db.save_upload(uploaded, "meals")
    record = db.now_stamp()
    record.update({
        "id": db.new_id(),
        "date": day,
        "meal": meal,
        "path": path,
        "desc": desc.strip(),
        "who": who,
    })
    meals.append(record)
    db.write_json(db.MEALS, meals)
    flash(f"🍽️ {meal}已经记下来啦！")
    rerun()


def page_meals() -> None:
    """一日三餐：每餐一张照片 + 一句描述，没打卡时显示空盘子占位。"""
    section("今天吃了什么", "🍽️")
    day = st.date_input("看哪一天", value=date.today(), key="meal_day").isoformat()
    meals = db.read_json(db.MEALS, [])

    for meal, icon in MEALS:
        record = next(
            (m for m in meals if m.get("date") == day and m.get("meal") == meal), None
        )
        st.write("")
        st.markdown(f"#### {icon} {meal}")

        if record:
            src = photo_src(record.get("path", ""))
            left, right = st.columns([1, 1])
            with left:
                if src:
                    show_image(src)
                else:
                    card('<div class="center plate">🍽️</div><div class="center muted">图片找不到了</div>')
            with right:
                card(
                    f'<div class="rec-head">{esc(record.get("who", ""))} · '
                    f'{esc(record.get("time", ""))}</div>'
                    f'<div class="rec-body">{esc(record.get("desc") or "（没有写描述）")}</div>'
                )
            with st.expander(f"换一张 / 改描述（{meal}）"):
                with st.form(f"meal_form_{meal}", clear_on_submit=True):
                    up = st.file_uploader(
                        "重新上传照片", type=["jpg", "jpeg", "png", "webp"], key=f"up2_{meal}"
                    )
                    desc = st.text_input("新的描述", value=record.get("desc", ""))
                    who = st.selectbox(
                        "我是谁", [HER_NICK, ME_NICK],
                        index=0 if who_am_i() == HER_NICK else 1, key=f"who2_{meal}",
                    )
                    if st.form_submit_button(f"更新{meal}"):
                        if up is None:
                            st.warning("先选一张照片吧～")
                        else:
                            save_meal(meal, day, up, desc, who)
        else:
            # 没打卡：显示可爱的空盘子占位图
            card(
                '<div class="center">'
                f'<div class="plate">{esc(icon)}</div>'
                f'<div class="muted">今天还没有记录{esc(meal)}，等你来打卡～</div>'
                "</div>"
            )
            with st.form(f"meal_new_{meal}", clear_on_submit=True):
                up = st.file_uploader(
                    f"上传{meal}照片（拍照或从相册选）",
                    type=["jpg", "jpeg", "png", "webp"],
                    key=f"up_{meal}",
                )
                desc = st.text_input(
                    "一句话描述", placeholder="今天食堂的糖醋排骨好好吃", key=f"desc_{meal}"
                )
                who = st.selectbox(
                    "我是谁", [HER_NICK, ME_NICK],
                    index=0 if who_am_i() == HER_NICK else 1, key=f"who_{meal}",
                )
                if st.form_submit_button(f"上传{meal}", type="primary"):
                    if up is None:
                        st.warning("先选一张照片吧～")
                    else:
                        save_meal(meal, day, up, desc, who)


# --------------------------------------------------------------------------- #
# 页面五：照片墙
# --------------------------------------------------------------------------- #


@st.dialog("📷 照片详情", width="large")
def photo_dialog(photo: Dict[str, Any]) -> None:
    """点「放大」后弹出的照片详情窗口（顺便可以删除）。"""
    src = photo_src(photo.get("path", ""))
    if src:
        show_image(src)
    st.markdown(
        f'<span class="tag">{esc(photo.get("tag", ""))}</span>'
        f'<div class="rec-body">{esc(photo.get("desc") or "（没有写描述）")}</div>'
        f'<div class="rec-head">{esc(photo.get("who", ""))} · '
        f'{esc(db.pretty_date(photo.get("date", "")))} {esc(photo.get("time", ""))}</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    sure = st.checkbox("我确认要删除这张照片", key=f"sure_{photo.get('id')}")
    if st.button("🗑 删除这张照片", key=f"del_{photo.get('id')}"):
        if not sure:
            st.warning("先勾选上面的确认框")
        else:
            db.remove_by_id(db.PHOTOS, photo.get("id", ""))
            db.delete_upload(photo.get("path", ""))
            st.session_state["zoom_photo"] = None
            flash("照片已删除。")
            rerun()
    if st.button("关闭", key=f"close_{photo.get('id')}"):
        st.session_state["zoom_photo"] = None
        rerun()


def save_photo(uploaded, tag: str, desc: str, who: str) -> None:
    """保存一张照片到照片墙。"""
    path = db.save_upload(uploaded, "photos")
    record = db.now_stamp()
    record.update({
        "id": db.new_id(),
        "path": path,        # JSON 里只存路径，图片本身在 uploads/photos/
        "tag": tag,
        "desc": desc.strip(),
        "who": who,
    })
    db.append_json(db.PHOTOS, record)
    flash("🖼️ 这个瞬间已经贴到照片墙上啦。")
    rerun()


def page_photos() -> None:
    """照片墙：带报备标签的相册，支持筛选、放大、删除。"""
    photos = sorted(
        db.read_json(db.PHOTOS, []),
        key=lambda p: (p.get("date", ""), p.get("ts", "")),
        reverse=True,   # 最新的排最前面
    )

    section("我们的照片墙", "🖼️")
    card(
        f'<div class="center">已记录 <b style="color:#c86fa6;font-size:1.3rem;">{len(photos)}</b> '
        "个瞬间</div>",
        extra_class="tint",
    )

    # ---- 上传 ---- #
    with st.form("photo_form", clear_on_submit=True):
        up = st.file_uploader(
            "选一张照片（手机可以直接拍照）",
            type=["jpg", "jpeg", "png", "webp", "heic"],
        )
        col1, col2 = st.columns(2)
        tag = col1.selectbox("报备标签", PHOTO_TAGS + ["自定义"])
        custom_tag = col2.text_input("自定义标签（可留空）")
        desc = st.text_input("一句描述", placeholder="今天的天空是粉色的，想给你看")
        who = st.selectbox(
            "上传者", [HER_NICK, ME_NICK], index=0 if who_am_i() == HER_NICK else 1
        )
        if st.form_submit_button("📤 上传到照片墙", type="primary"):
            if up is None:
                st.warning("先选一张照片吧～")
            else:
                save_photo(up, custom_tag.strip() or tag, desc, who)

    if not photos:
        muted("照片墙还是空的，上传第一张吧～")
        return

    # ---- 筛选 ---- #
    st.write("")
    col1, col2 = st.columns(2)
    who_filter = col1.selectbox("按上传者筛选", ["全部", HER_NICK, ME_NICK])
    date_options = ["全部"] + db.all_dates(photos)
    day_filter = col2.selectbox("按日期筛选", date_options)

    shown = [
        p for p in photos
        if (who_filter == "全部" or p.get("who") == who_filter)
        and (day_filter == "全部" or p.get("date") == day_filter)
    ]
    muted(f"筛选结果：{len(shown)} 张")
    st.write("")

    # ---- 网格展示（三列，手机上自动堆叠） ---- #
    cols = st.columns(3)
    for i, p in enumerate(shown):
        with cols[i % 3]:
            src = photo_src(p.get("path", ""))
            if src:
                show_image(src)
            else:
                card('<div class="center plate">🖼️</div><div class="center muted">图片丢了</div>')
            card(
                f'<span class="tag">{esc(p.get("tag", ""))}</span>'
                f'<div class="rec-body">{esc(p.get("desc") or "")}</div>'
                f'<div class="rec-head">{esc(p.get("who", ""))} · '
                f'{esc(db.pretty_date(p.get("date", "")))} {esc(p.get("time", ""))}</div>'
            )
            if st.button("🔍 放大", key=f"zoom_{p.get('id')}"):
                st.session_state["zoom_photo"] = p
                rerun()

    # 弹出详情（如果点了放大）
    zoom = st.session_state.get("zoom_photo")
    if zoom:
        photo_dialog(zoom)


# --------------------------------------------------------------------------- #
# 页面六：记账本
# --------------------------------------------------------------------------- #


def page_money() -> None:
    """记账本：今日花费 + 每笔明细 + 按月汇总。"""
    expenses = db.read_json(db.EXPENSES, [])
    today = db.today_str()
    today_list = [e for e in expenses if e.get("date") == today]
    today_total = sum(float(e.get("amount", 0)) for e in today_list)

    section("今天花了多少", "💰")
    card(
        f'<div class="center">今日总花费 '
        f'<b style="color:#c86fa6;font-size:1.5rem;">{today_total:.2f}</b> 元'
        f'<div class="muted">共 {len(today_list)} 笔</div></div>',
        extra_class="tint",
    )

    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        amount = col1.number_input("金额（元）", min_value=0.0, step=1.0, format="%.2f")
        category = col2.selectbox("消费类别", EXPENSE_CATEGORIES)
        col3, col4 = st.columns(2)
        who = col3.selectbox("谁花的", [HER_NICK, ME_NICK], index=0 if who_am_i() == HER_NICK else 1)
        note = col4.text_input("备注（可留空）", placeholder="和同学吃火锅")
        if st.form_submit_button("✏️ 记一笔", type="primary"):
            if amount <= 0:
                st.warning("金额要大于 0 哦～")
            else:
                record = db.now_stamp()
                record.update({
                    "id": db.new_id(),
                    "amount": round(float(amount), 2),
                    "category": category,
                    "note": note.strip(),
                    "who": who,
                })
                db.append_json(db.EXPENSES, record)
                flash(f"✏️ 已记下 {amount:.2f} 元（{category}）")
                rerun()

    if today_list:
        st.write("")
        section("今天的每一笔", "🧾")
        for e in reversed(today_list):
            card(
                f'<div class="rec-head">{esc(e.get("time", ""))} · {esc(e.get("who", ""))}</div>'
                f'<div class="rec-body">{esc(e.get("category", ""))} · '
                f'<b>{float(e.get("amount", 0)):.2f} 元</b>'
                f'{" · " + esc(e.get("note", "")) if e.get("note") else ""}</div>'
            )

    # ---- 按月查看 ---- #
    months = db.all_months(expenses)
    if months:
        st.write("")
        section("按月汇总", "📅")
        month = st.selectbox("选择月份", months, key="money_month")
        month_list = [e for e in expenses if db.month_of(e.get("date", "")) == month]
        month_total = sum(float(e.get("amount", 0)) for e in month_list)
        by_category: Dict[str, float] = {}
        for e in month_list:
            by_category[e.get("category", "其他")] = (
                by_category.get(e.get("category", "其他"), 0.0) + float(e.get("amount", 0))
            )
        card(
            f'<div class="muted">{esc(month)} 合计</div>'
            f'<div class="rec-body"><b style="color:#c86fa6;font-size:1.3rem;">{month_total:.2f}</b> 元 '
            f'· 共 {len(month_list)} 笔</div>'
            + "".join(
                f'<span class="pill">{esc(k)} {v:.2f} 元</span>'
                for k, v in sorted(by_category.items(), key=lambda kv: -kv[1])
            )
        )


# --------------------------------------------------------------------------- #
# 页面七：期待与你相见（倒计时）
# --------------------------------------------------------------------------- #


def _preset_name(value: str) -> None:
    """快捷按钮的回调：把事件名填进输入框。

    回调在页面渲染之前执行，所以这时改 session_state 是安全的。
    """
    st.session_state["cd_name"] = value


def page_countdown() -> None:
    """倒计时页：添加 / 删除事件，卡片显示剩余天数和小时。"""
    events = db.read_json(db.COUNTDOWNS, [])
    section("期待与你相见", "⏳")

    # ---- 快捷添加常见事件 ---- #
    muted("常用事件一键填入名称：")
    preset_cols = st.columns(4)
    for col, preset in zip(preset_cols, ["下次见面", "玉环生日", "雅楠生日", "在一起纪念日"]):
        col.button(preset, key=f"preset_{preset}", on_click=_preset_name, args=(preset,))

    with st.form("countdown_form", clear_on_submit=True):
        name = st.text_input("事件名称", key="cd_name", placeholder="下次见面")
        col1, col2 = st.columns([2, 1])
        target = col1.date_input("目标日期", value=date.today(), key="cd_date")
        icon = col2.selectbox("图标", COUNTDOWN_ICONS, key="cd_icon")
        if st.form_submit_button("➕ 添加倒计时", type="primary"):
            if not name.strip():
                st.warning("先给这个日子起个名字吧～")
            else:
                record = db.now_stamp()
                record.update({
                    "id": db.new_id(),
                    "name": name.strip(),
                    "target": target.isoformat(),
                    "icon": icon,
                    "who": who_am_i(),
                })
                db.append_json(db.COUNTDOWNS, record)
                flash(f"{icon} 「{name.strip()}」已加入倒计时")
                rerun()

    if not events:
        muted("还没有倒计时事件，上面的按钮可以快速添加哦～")
        return

    # ---- 按目标日期排序展示 ---- #
    st.write("")
    now = datetime.now()
    for e in sorted(events, key=lambda x: x.get("target", "")):
        try:
            target_dt = datetime.fromisoformat(e.get("target", "") + "T00:00:00")
        except ValueError:
            continue
        delta = target_dt - now
        total_seconds = int(delta.total_seconds())
        if total_seconds >= 0:
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            text = f"还有 <b>{days}</b> 天 <b>{hours}</b> 小时"
            sub = "正在期待"
        else:
            days = abs(total_seconds) // 86400
            text = f"已经过去 <b>{days}</b> 天"
            sub = "值得纪念"
        col1, col2 = st.columns([5, 1])
        with col1:
            card(
                f'<div style="display:flex;align-items:center;gap:14px;">'
                f'<div style="font-size:2rem;">{esc(e.get("icon", "💗"))}</div>'
                f"<div><div style='font-weight:700;color:#7d5e8c;font-size:1.05rem;'>"
                f'{esc(e.get("name", ""))}</div>'
                f'<div class="rec-body">距离 {esc(e.get("name", ""))} {text}</div>'
                f'<div class="rec-head">{esc(db.pretty_date(e.get("target", "")))} · {sub}</div>'
                f"</div></div>"
            )
        with col2:
            st.write("")
            if st.button("🗑", key=f"del_cd_{e.get('id')}", help="删除这个倒计时"):
                db.remove_by_id(db.COUNTDOWNS, e.get("id", ""))
                flash("已删除这个倒计时。")
                rerun()


# --------------------------------------------------------------------------- #
# 页面八：一起变优秀（英语角 + 文学角）
# --------------------------------------------------------------------------- #


def remember_phrase(phrase: str) -> None:
    """「我记住了」：给这个短语的计数 +1。"""
    data = db.read_json(db.LEARNING, {})
    if not isinstance(data, dict):
        data = {}
    data[phrase] = int(data.get(phrase, 0)) + 1
    db.write_json(db.LEARNING, data)
    flash(f"📌 「{phrase}」已记下，商务英语储备又厚了一点！")
    rerun()


@st.dialog("✍️ 抄写一遍")
def copy_dialog(poem: Dict[str, Any]) -> None:
    """文学角的抄写窗口：把诗句抄一遍，记录可以回看。"""
    st.markdown(
        f'<div class="rec-body" style="font-size:1.05rem;">{esc(poem.get("text", ""))}</div>'
        f'<div class="rec-head">—— {esc(poem.get("author", ""))} {esc(poem.get("source", ""))}</div>',
        unsafe_allow_html=True,
    )
    with st.form("copy_form", clear_on_submit=True):
        text = st.text_area(
            "抄写内容",
            height=150,
            placeholder="在这里把这句话抄一遍，手写一遍会记得更牢～",
        )
        submitted = st.form_submit_button("保存抄写", type="primary")
    if submitted:
        if not text.strip():
            st.warning("先抄一句再保存吧～")
        else:
            record = db.now_stamp()
            record.update({
                "id": db.new_id(),
                "poem": poem.get("text", ""),
                "author": poem.get("author", ""),
                "source": poem.get("source", ""),
                "text": text.strip(),
                "who": who_am_i(),
            })
            db.append_json(db.TRANSCRIPTS, record)
            st.session_state["copy_poem"] = None
            flash("✍️ 抄写记录已经保存，可以随时回看。")
            rerun()


def page_study() -> None:
    """学习角：玉环的商务英语 + 雅楠的文学积累。"""
    phrases = db.read_json("business_phrases.json", [])
    poems = db.read_json("poems.json", [])
    learning = db.read_json(db.LEARNING, {})
    if not isinstance(learning, dict):
        learning = {}
    transcripts = db.read_json(db.TRANSCRIPTS, [])

    offset = int(st.session_state.get("study_offset", 0))
    phrase = pick_daily(phrases, offset, salt=1)
    poem = pick_daily(poems, offset, salt=2)

    # ---------------- 玉环的英语角 ---------------- #
    section(f"{HER_NICK}的英语角", LOGO)
    muted(f"{HER_NAME} · 洛阳理工学院 · 商务英语 · 每天一个商务表达")
    if phrase:
        card(
            f'<div style="font-size:1.45rem;font-weight:800;color:#c86fa6;">'
            f'{esc(phrase.get("phrase", ""))}</div>'
            f'<div class="rec-body">释义：{esc(phrase.get("zh", ""))}</div>'
            f'<div class="quote-zh" style="font-size:1rem;margin-top:8px;">'
            f'💼 {esc(phrase.get("example", ""))}</div>'
            f'<div class="quote-en">{esc(phrase.get("example_zh", ""))}</div>'
        )
        learned = int(learning.get(phrase.get("phrase", ""), 0))
        mastered = sum(1 for v in learning.values() if int(v) > 0)
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("✅ 我记住了", key="btn_remember", type="primary"):
                remember_phrase(phrase.get("phrase", ""))
        with col2:
            st.markdown(
                f'<div style="padding-top:.5rem;">'
                f'<span class="pill">这句已记 {learned} 次</span>'
                f'<span class="pill">累计掌握 {mastered} / {len(phrases)} 个短语</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("短语库是空的，往 data/business_phrases.json 里加几条吧～")

    # ---------------- 雅楠的文学角 ---------------- #
    st.write("")
    section(f"{ME_NICK}的文学角", "📖")
    muted(f"{ME_NAME} · 西南民大 · 汉语言文学 · 每天一句诗")
    if poem:
        card(
            f'<div class="rec-body" style="font-size:1.16rem;font-weight:600;line-height:1.9;">'
            f'{esc(poem.get("text", ""))}</div>'
            f'<div class="rec-head" style="margin-top:8px;">—— {esc(poem.get("author", ""))} '
            f'{esc(poem.get("source", ""))}</div>'
            f'<div class="rec-body" style="margin-top:10px;">💭 {esc(poem.get("apprec", ""))}</div>'
        )
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("✍️ 抄写一遍", key="btn_copy", type="primary"):
                st.session_state["copy_poem"] = poem
                rerun()
        with col2:
            mine = sum(1 for t in transcripts if t.get("who") == ME_NICK)
            st.markdown(
                f'<div style="padding-top:.5rem;">'
                f'<span class="pill">{ME_NICK}已抄写 {mine} 句</span>'
                f'<span class="pill">诗词库共 {len(poems)} 句</span></div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("诗句库是空的，往 data/poems.json 里加几条吧～")

    st.write("")
    if st.button("🔄 换一个短语 / 换一句诗", key="btn_shuffle"):
        st.session_state["study_offset"] = offset + 1
        rerun()
    muted("每天自动换一条，同一天刷新内容不变；点上面的按钮可以手动翻。")

    # ---- 抄写记录（可回看） ---- #
    if transcripts:
        st.write("")
        section("抄写记录", "🖋️")
        for t in list(reversed(transcripts))[:10]:
            card(
                f'<div class="rec-head">{esc(db.pretty_date(t.get("date", "")))} '
                f'{esc(t.get("time", ""))} · {esc(t.get("who", ""))}</div>'
                f'<div class="rec-body" style="font-weight:600;">{esc(t.get("poem", ""))}</div>'
                f'<div class="rec-body" style="color:#8a7194;">抄写：{esc(t.get("text", ""))}</div>'
            )

    # 打开抄写窗口（如果点了按钮）
    pending = st.session_state.get("copy_poem")
    if pending:
        copy_dialog(pending)


# --------------------------------------------------------------------------- #
# 页面九：今天也要加油鸭（每日任务清单）
# --------------------------------------------------------------------------- #


def _owner_label(owner: str) -> str:
    """任务栏的小标题。"""
    if owner == HER_NICK:
        return f"{LOGO} {HER_NICK}（{HER_NAME}）"
    return f"💜 {ME_NICK}（{ME_NAME}）"


def page_tasks() -> None:
    """任务清单：两个人各自一份，每天自动重置，互相可见。"""
    tasks = db.read_json(db.TASKS, {})
    if not isinstance(tasks, dict):
        tasks = {}
    done_all = db.read_json(db.TASK_DONE, {})
    if not isinstance(done_all, dict):
        done_all = {}

    today = db.today_str()
    done_today = dict(done_all.get(today, {}))

    owners = [HER_NICK, ME_NICK]
    for owner in owners:                     # 保证两个人的列表都存在
        tasks.setdefault(owner, [])

    # ---- 总进度 ---- #
    all_tasks = [t for owner in owners for t in tasks[owner]]
    all_done = sum(1 for t in all_tasks if done_today.get(t["id"]))
    section("今天也要加油鸭", "🐣")
    card(
        f'<div class="center">今日完成进度：<b style="color:#c86fa6;font-size:1.25rem;">'
        f"{all_done}/{len(all_tasks)}</b>"
        f'<div class="muted">新的一天会自动全部重置，不用手动清空</div></div>',
        extra_class="tint",
    )
    st.progress(all_done / len(all_tasks) if all_tasks else 0.0)

    # ---- 两个人的清单并排展示（手机上会上下堆叠） ---- #
    cols = st.columns(2)
    for col, owner in zip(cols, owners):
        with col:
            st.markdown(f"#### {_owner_label(owner)}")
            items = tasks[owner]
            finished = sum(1 for t in items if done_today.get(t["id"]))
            st.progress(finished / len(items) if items else 0.0)
            muted(f"今日完成进度：{finished}/{len(items)}")

            if not items:
                muted("还没有任务，下面添加一条吧～")

            for t in items:
                is_done = bool(done_today.get(t["id"]))
                # 已完成的任务用删除线显示（Streamlit 的 label 支持 markdown）
                label = f"~~{t.get('text', '')}~~" if is_done else t.get("text", "")
                c1, c2 = st.columns([7, 1])
                checked = c1.checkbox(
                    label,
                    value=is_done,
                    key=f"task_{today}_{owner}_{t.get('id')}",
                )
                if bool(checked) != is_done:
                    done_today[t["id"]] = bool(checked)
                    done_all[today] = done_today
                    db.write_json(db.TASK_DONE, done_all)
                    rerun()
                if c2.button("🗑", key=f"deltask_{t.get('id')}", help="删除这条任务"):
                    tasks[owner] = [x for x in items if x.get("id") != t.get("id")]
                    db.write_json(db.TASKS, tasks)
                    flash("任务已删除。")
                    rerun()

            # ---- 添加任务 ---- #
            placeholder = "背 30 个单词" if owner == HER_NICK else "背诵一首古诗"
            with st.form(f"task_form_{owner}", clear_on_submit=True):
                new_text = st.text_input(
                    "添加今日任务", placeholder=placeholder, key=f"newtask_{owner}"
                )
                if st.form_submit_button("➕ 添加"):
                    if not new_text.strip():
                        st.warning("写点什么再添加吧～")
                    else:
                        tasks[owner].append({
                            "id": db.new_id(),
                            "text": new_text.strip(),
                            "created": db.now_stamp()["ts"],
                        })
                        db.write_json(db.TASKS, tasks)
                        flash("任务已添加，今天也要加油鸭！")
                        rerun()

    # ---- 给对方的鼓励 ---- #
    st.write("")
    me = who_am_i()
    other = ME_NICK if me == HER_NICK else HER_NICK
    other_items = tasks.get(other, [])
    other_done = sum(1 for t in other_items if done_today.get(t["id"]))
    if other_items and other_done == len(other_items):
        card(
            f'<div class="center">🎉 {esc(other)}今天全部完成啦，快去夸夸她！</div>',
            extra_class="tint",
        )
    elif other_items:
        card(
            f'<div class="center">💌 {esc(other)}今天还有 {len(other_items) - other_done} 条没做完，'
            "记得说一句「加油，我等你」。</div>"
        )
