# -*- coding: utf-8 -*-
"""雅楠 & 玉环的小窝 —— 入口文件。

运行：
    cd couple-app
    .venv/bin/streamlit run app.py

页面逻辑在 views.py，样式在 ui.py，数据读写在上 storage.py。
"""

from __future__ import annotations

import json
from datetime import date, datetime

import streamlit as st

# set_page_config 必须是第一个 Streamlit 命令，所以放在所有其他 import 之前
st.set_page_config(page_title="雅楠 & 玉环的小窝", page_icon="💗", layout="centered")

import storage as db  # noqa: E402
import ui  # noqa: E402
from views import (  # noqa: E402
    page_countdown,
    page_diary,
    page_home,
    page_meals,
    page_money,
    page_mood,
    page_photos,
    page_study,
    page_tasks,
)

#: 页面名 → 渲染函数
PAGES = {
    "🏠 我们的小窝": page_home,
    "💗 今天心情": page_mood,
    "📔 我们的故事": page_diary,
    "🍽️ 一日三餐": page_meals,
    "🖼️ 照片墙": page_photos,
    "💰 记账本": page_money,
    "⏳ 期待与你相见": page_countdown,
    "📚 一起变优秀": page_study,
    "🐣 今天也要加油鸭": page_tasks,
}


def sidebar() -> None:
    """侧边栏：选择「我是谁」、修改纪念日、导出全部数据。"""
    with st.sidebar:
        st.markdown("### 💗 小设置")

        # ---- 我是谁：决定打卡 / 上传的署名（每台手机各选各的） ---- #
        default_index = 0 if ui.who_am_i() == ui.HER_NICK else 1
        choice = st.selectbox(
            "我是谁（用于标记是谁记录的）",
            ui.PEOPLE,
            index=default_index,
            key="who_select",
        )
        st.session_state["who"] = ui.HER_NICK if ui.HER_NICK in choice else ui.ME_NICK
        ui.muted(f"当前身份：{st.session_state['who']}")

        st.divider()
        # ---- 纪念日：默认 2022-09-01，可以随时改 ---- #
        since = db.together_since()
        picked = st.date_input(
            "我们的纪念日",
            value=since,
            min_value=date(2000, 1, 1),
            max_value=date.today(),
            key="since_input",
        )
        if picked != since:
            cfg = db.load_config()
            cfg["together_since"] = picked.isoformat()
            db.save_config(cfg)
            ui.rerun()
        ui.muted(f"在一起 {db.days_together():,} 天")

        st.divider()
        # ---- 数据备份：把 data/ 下所有 JSON 打包下载 ---- #
        st.markdown("### 💾 数据备份")
        backup = {
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "config": db.load_config(),
            "checkins": db.read_json(db.CHECKINS, []),
            "moods": db.read_json(db.MOODS, []),
            "diaries": db.read_json(db.DIARIES, []),
            "meals": db.read_json(db.MEALS, []),
            "photos": db.read_json(db.PHOTOS, []),
            "expenses": db.read_json(db.EXPENSES, []),
            "countdowns": db.read_json(db.COUNTDOWNS, []),
            "learning": db.read_json(db.LEARNING, {}),
            "transcripts": db.read_json(db.TRANSCRIPTS, []),
            "tasks": db.read_json(db.TASKS, {}),
            "task_done": db.read_json(db.TASK_DONE, {}),
        }
        st.download_button(
            "⬇️ 下载全部记录（JSON）",
            data=json.dumps(backup, ensure_ascii=False, indent=2),
            file_name=f"our-days-{date.today().isoformat()}.json",
            mime="application/json",
            key="btn_backup",
        )
        ui.muted("记录都存在 data/*.json，照片存在 uploads/。部署到云端时记得定期下载备份。")

        st.divider()
        ui.muted("💗 玉环（李玉环）· 洛阳")
        ui.muted("💜 楠（孙雅楠）· 成都")
        ui.muted("隔着 900 多公里，也要好好在一起")


def main() -> None:
    ui.inject_css()
    sidebar()

    # 开屏欢迎语（随机一句 + 淡入动画）
    ui.splash()

    # 记录提示（打卡成功之类）
    ui.show_flash()

    # ---- 导航：用下拉框，手机上一点就好，切页也不会跳回第一页 ---- #
    page_name = st.selectbox("选择页面", list(PAGES), key="nav", label_visibility="collapsed")
    st.write("")
    PAGES[page_name]()

    # ---- 页脚 ---- #
    st.markdown(
        '<div class="muted" style="text-align:center;margin-top:30px;">'
        f"{ui.esc(ui.APP_TITLE)} · 用 Streamlit 做的专属小窝 ♡</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
