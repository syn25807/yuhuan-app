# -*- coding: utf-8 -*-
"""整站测试。

运行：
    .venv/bin/python -m unittest discover -s tests -v

测试用临时目录当数据目录（COUPLE_DATA_DIR / COUPLE_UPLOAD_DIR），
不会动到 data/ 和 uploads/ 里的真实记录。
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

# 必须在导入 storage / app 之前设置
TMP = Path(tempfile.mkdtemp(prefix="couple-app-test-"))
os.environ["COUPLE_DATA_DIR"] = str(TMP / "data")
os.environ["COUPLE_UPLOAD_DIR"] = str(TMP / "uploads")
STATIC = ("quotes.json", "business_phrases.json", "poems.json")

# 把静态内容（语录 / 短语库 / 诗句库）复制到临时数据目录
Path(os.environ["COUPLE_DATA_DIR"]).mkdir(parents=True, exist_ok=True)
for _name in STATIC:
    shutil.copy(APP_DIR / "data" / _name, Path(os.environ["COUPLE_DATA_DIR"]) / _name)

import storage as db  # noqa: E402
import ui  # noqa: E402
from streamlit.testing.v1 import AppTest  # noqa: E402


class FakeUpload:
    """模拟 Streamlit 的 UploadedFile（AppTest 目前不支持 file_uploader）。"""

    def __init__(self, name: str = "photo.png", payload: bytes = None):
        self.name = name
        self._payload = payload if payload is not None else _png_bytes()

    def getbuffer(self):
        return self._payload


def _png_bytes() -> bytes:
    """生成一张真的 8x8 图片，st.image 会用 PIL 打开它，假字节会报错。"""
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (255, 192, 220)).save(buf, format="PNG")
    return buf.getvalue()


def by_key(app_test, kind: str, key: str):
    """按 key 找控件（AppTest 的元素顺序不一定稳定）。"""
    for widget in getattr(app_test, kind):
        if getattr(widget, "key", None) == key:
            return widget
    raise LookupError(f"找不到 {kind}[{key}]")


class SplashTest(unittest.TestCase):
    """开屏语轮播：打乱顺序、一轮之内不重复。"""

    def setUp(self):
        data_dir = Path(os.environ["COUPLE_DATA_DIR"])
        for path in data_dir.glob("*"):
            if path.name not in STATIC:
                path.unlink()

    def test_line_count(self):
        self.assertEqual(len(ui.SPLASH_LINES), 45)
        for line in ui.SPLASH_LINES:
            self.assertTrue(line.strip())

    def test_removed_lines_are_gone(self):
        """这几句按要求删掉，不再出现。"""
        for line in (
            "世界第二，小梨花第一",
            "未来的每一天，都多爱你一点",
            "你好像瘦了，头发也变长了，背影陌生到让我觉得见你好像是上个世纪的事。"
            "然后你开口叫我的名字，我就想笑，好像自己刚刚放学，只在门口等了你五分钟而已",
        ):
            self.assertNotIn(line, ui.SPLASH_LINES)

    def test_names_are_updated(self):
        """称呼和学校信息已更新，logo 是粉色爱心。"""
        self.assertEqual(ui.HER_NAME, "李玉环")
        self.assertEqual(ui.HER_NICK, "玉环")
        self.assertEqual(ui.ME_NAME, "孙雅楠")
        self.assertEqual(ui.LOGO, "💗")
        self.assertIn("李玉环", ui.PEOPLE[0])
        self.assertTrue(ui.PEOPLE[0].startswith("💗"))
        self.assertIn("孙雅楠", ui.PEOPLE[1])

    def test_every_line_shown_once_before_repeat(self):
        """连着取 48 次，应该把 48 句各播一次，不重不漏。"""
        import ui

        n = len(ui.SPLASH_LINES)
        seen = [ui.next_splash_line() for _ in range(n)]
        self.assertEqual(len(set(seen)), n)
        self.assertEqual(set(seen), set(ui.SPLASH_LINES))

    def test_new_round_reshuffles_without_immediate_repeat(self):
        """一轮播完会重新洗牌，且新一轮第一句不等于上一轮最后一句。"""
        import ui

        n = len(ui.SPLASH_LINES)
        first_round = [ui.next_splash_line() for _ in range(n)]
        second_round_first = ui.next_splash_line()
        self.assertIn(second_round_first, ui.SPLASH_LINES)
        self.assertNotEqual(second_round_first, first_round[-1])

    def test_state_is_persisted_to_file(self):
        """顺序要落盘，否则刷新页面就记不住播到第几句了。"""
        import ui

        ui.next_splash_line()
        state = json.loads((Path(os.environ["COUPLE_DATA_DIR"]) / "splash_state.json")
                           .read_text(encoding="utf-8"))
        self.assertEqual(sorted(state["order"]), list(range(len(ui.SPLASH_LINES))))
        self.assertEqual(state["index"], 1)


class PasswordGateTest(unittest.TestCase):
    """可选的访问暗号：配了 APP_PASSWORD 才生效。"""

    def setUp(self):
        os.environ["APP_PASSWORD"] = "our-secret"
        self.at = AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=60)
        self.at.run()

    def tearDown(self):
        os.environ.pop("APP_PASSWORD", None)

    def test_gate_blocks_then_unlocks(self):
        # 一开始只有暗号输入框，页面内容还没出来
        self.assertEqual(len(self.at.text_input), 1)
        self.assertEqual(len(self.at.selectbox), 0)

        # 输错了要提示
        self.at.text_input[0].set_value("wrong").run()
        self.assertTrue(self.at.error)
        self.assertEqual(len(self.at.selectbox), 0)

        # 输对了才进得去
        self.at.text_input[0].set_value("our-secret").run()
        self.assertTrue(self.at.session_state["_pwd_ok"])
        self.assertTrue(len(self.at.selectbox) >= 1)


class CoupleAppTest(unittest.TestCase):
    """每个测试都从干净的数据目录开始。"""

    def setUp(self):
        # 清空临时数据目录（保留三个静态内容文件）
        for path in Path(os.environ["COUPLE_DATA_DIR"]).glob("*"):
            if path.name not in STATIC:
                path.unlink()
        uploads = Path(os.environ["COUPLE_UPLOAD_DIR"])
        if uploads.exists():
            shutil.rmtree(uploads)
        uploads.mkdir(parents=True, exist_ok=True)

        self.at = AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=60)
        self.at.run()

    # -------- 工具方法 -------- #

    def goto(self, page: str) -> None:
        """切换到某个页面。"""
        by_key(self.at, "selectbox", "nav").set_value(page).run()
        self.assertFalse(self.at.exception, self.at.exception)

    def load(self, name: str, default=None):
        path = Path(os.environ["COUPLE_DATA_DIR"]) / name
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def click(self, label_part: str):
        """点击 label 里包含某段文字的按钮。"""
        target = next(b for b in self.at.button if label_part in b.label)
        return target.click().run()

    # -------- 基础 -------- #

    def test_app_runs_and_shows_splash(self):
        self.assertFalse(self.at.exception, self.at.exception)
        # 开屏语一定来自那 48 句之一
        from ui import SPLASH_LINES

        text = " ".join(m.value for m in self.at.markdown)
        self.assertTrue(any(line in text for line in SPLASH_LINES))
        self.assertIn("小窝", text)

    def test_splash_next_button_changes_line(self):
        """点「✨ 下一句」会换成另一句，而且不会连着重复。"""
        before = self.at.session_state["splash_line"]
        self.click("下一句")
        after = self.at.session_state["splash_line"]
        self.assertNotEqual(before, after)

    def test_home_checkin(self):
        self.click("早安打卡")
        records = self.load("checkins.json")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["type"], "morning")
        self.assertTrue(records[0]["quote_zh"])
        self.assertTrue(records[0]["quote_en"])

    # -------- 心情 -------- #

    def test_mood_and_note(self):
        self.goto("💗 今天心情")
        self.click("😊 开心")
        moods = self.load("moods.json")
        self.assertEqual(moods[0]["mood"], "开心")

        by_key(self.at, "text_area", "note_input").set_value("今天也想你").run()
        self.click("保存这句话")
        records = self.load("moods.json")
        notes = [r for r in records if r.get("text")]
        self.assertEqual(notes[0]["text"], "今天也想你")
        # 输入框会被回调清空
        self.assertEqual(self.at.session_state["note_input"], "")

    # -------- 日记 -------- #

    def test_diary(self):
        self.goto("📔 我们的故事")
        self.at.text_area[0].set_value("今天上完口译课，超级累但很充实。").run()
        self.click("保存这篇日记")
        diaries = self.load("diaries.json")
        self.assertEqual(len(diaries), 1)
        self.assertIn("口译课", diaries[0]["text"])
        self.assertTrue(diaries[0]["date"])          # 自动记录日期

    # -------- 记账 -------- #

    def test_expense(self):
        self.goto("💰 记账本")
        self.at.number_input[0].set_value(28.5).run()
        self.click("记一笔")
        expenses = self.load("expenses.json")
        self.assertEqual(len(expenses), 1)
        self.assertAlmostEqual(expenses[0]["amount"], 28.5)
        self.assertIn(expenses[0]["category"], ("餐饮", "交通", "学习", "购物", "其他"))

    # -------- 倒计时 -------- #

    def test_countdown_add_and_delete(self):
        self.goto("⏳ 期待与你相见")
        by_key(self.at, "text_input", "cd_name").set_value("下次见面").run()
        self.click("添加倒计时")
        events = self.load("countdowns.json")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["name"], "下次见面")

        self.click("🗑")
        self.assertEqual(self.load("countdowns.json"), [])

    # -------- 学习角 -------- #

    def test_study_remember_phrase(self):
        self.goto("📚 一起变优秀")
        self.click("我记住了")
        learning = self.load("learning.json")
        self.assertEqual(sum(learning.values()), 1)

    # -------- 任务清单 -------- #

    def test_tasks_add_and_check(self):
        self.goto("🐣 今天也要加油鸭")
        by_key(self.at, "text_input", "newtask_玉环").set_value("背30个单词").run()
        self.click("➕ 添加")
        tasks = self.load("tasks.json")
        self.assertEqual(len(tasks["玉环"]), 1)
        self.assertEqual(tasks["玉环"][0]["text"], "背30个单词")

        self.at.checkbox[0].check().run()
        done = self.load("task_done.json")
        today = list(done)[0]
        self.assertTrue(all(done[today].values()))
        # 打勾后标签会变成删除线样式
        self.assertTrue(self.at.checkbox[0].label.startswith("~~"))

    def test_tasks_reset_next_day(self):
        """跨天自动重置：完成记录按日期存，新的一天查不到旧记录。"""
        self.goto("🐣 今天也要加油鸭")
        by_key(self.at, "text_input", "newtask_玉环").set_value("练听力30分钟").run()
        self.click("➕ 添加")
        self.at.checkbox[0].check().run()
        done = self.load("task_done.json")
        done["2000-01-01"] = done.pop(list(done)[0])   # 假装完成记录是昨天的
        db.write_json(db.TASK_DONE, done)

        at2 = AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=60)
        at2.run()
        by_key(at2, "selectbox", "nav").set_value("🐣 今天也要加油鸭").run()
        self.assertFalse(at2.checkbox[0].value)        # 新的一天是未完成

    # -------- 照片与三餐（直接测数据层） -------- #

    def test_photo_upload_and_filter(self):
        path = db.save_upload(FakeUpload("sky.jpg"), "photos")
        self.assertTrue(db.upload_exists(path))
        db.append_json(db.PHOTOS, {
            "id": db.new_id(), "path": path, "tag": "好看的天空",
            "desc": "今天的天是粉色的", "who": "玉环",
            "date": "2026-09-10", "time": "18:20",
        })
        db.append_json(db.PHOTOS, {
            "id": db.new_id(), "path": path, "tag": "今天的学习桌",
            "desc": "自习到十点", "who": "楠",
            "date": "2026-09-11", "time": "22:10",
        })
        photos = db.read_json(db.PHOTOS, [])
        self.assertEqual(len(photos), 2)
        self.assertEqual([p["who"] for p in photos if p["date"] == "2026-09-11"], ["楠"])
        self.assertEqual(db.all_dates(photos)[0], "2026-09-11")   # 日期倒序，新的在前

    def test_meal_upload_replaces_same_day(self):
        """同一天同一餐再上传一次，旧记录和旧图片都会被替换掉。"""
        import views

        with mock.patch.object(views, "flash"), mock.patch.object(views, "rerun"):
            views.save_meal("午餐", "2026-09-10", FakeUpload("a.jpg"), "第一张", "玉环")
            first = self.load("meals.json")[0]["path"]
            views.save_meal("午餐", "2026-09-10", FakeUpload("b.jpg"), "第二张", "玉环")

        meals = self.load("meals.json")
        self.assertEqual(len(meals), 1)
        self.assertEqual(meals[0]["desc"], "第二张")
        self.assertFalse(db.upload_exists(first))          # 旧图已删
        self.assertTrue(db.upload_exists(meals[0]["path"]))

    def test_photo_delete_removes_file(self):
        """删除照片记录时，文件也会一起删掉。"""
        path = db.save_upload(FakeUpload("flower.jpg"), "photos")
        record = {
            "id": db.new_id(), "path": path, "tag": "路边的花",
            "desc": "", "who": "楠", "date": "2026-09-10", "time": "09:00",
        }
        db.append_json(db.PHOTOS, record)
        db.remove_by_id(db.PHOTOS, record["id"])
        db.delete_upload(path)
        self.assertEqual(self.load("photos.json"), [])
        self.assertFalse(db.upload_exists(path))

    def test_photos_page_renders_with_data(self):
        """照片墙能正常渲染图片、筛选框和放大按钮。"""
        for who, day in (("玉环", "2026-09-10"), ("楠", "2026-09-11")):
            db.append_json(db.PHOTOS, {
                "id": db.new_id(),
                "path": db.save_upload(FakeUpload(f"{who}.jpg"), "photos"),
                "tag": "好看的天空", "desc": "想给你看", "who": who,
                "date": day, "time": "18:00",
            })
        self.goto("🖼️ 照片墙")
        self.assertEqual(len(self.at.get("imgs")), 2)    # 两张照片都渲染出来了
        self.assertTrue(any("2" in m.value and "瞬间" in m.value for m in self.at.markdown))
        self.assertTrue(any("🔍 放大" == b.label for b in self.at.button))

    def test_meals_page_placeholder_and_upload(self):
        """没打卡时显示空盘子占位；有记录时显示照片和描述。"""
        self.goto("🍽️ 一日三餐")
        self.assertTrue(any("plate" in m.value for m in self.at.markdown))   # 占位图

        import views

        with mock.patch.object(views, "flash"), mock.patch.object(views, "rerun"):
            views.save_meal("早餐", db.today_str(), FakeUpload("bf.jpg"), "豆浆油条", "玉环")
        at2 = AppTest.from_file(str(APP_DIR / "app.py"), default_timeout=60)
        at2.run()
        by_key(at2, "selectbox", "nav").set_value("🍽️ 一日三餐").run()
        self.assertFalse(at2.exception, at2.exception)
        self.assertTrue(any("豆浆油条" in m.value for m in at2.markdown))
        self.assertEqual(len(at2.get("imgs")), 1)


if __name__ == "__main__":
    unittest.main()
