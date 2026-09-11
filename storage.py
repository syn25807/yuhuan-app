# -*- coding: utf-8 -*-
"""数据层：所有「记下来」的东西都经过这里。

设计原则
--------
1. **全部落地成 JSON**：心情、日记、三餐、照片索引、记账、倒计时、
   学习记录、任务，都写在 ``data/`` 目录下的 JSON 文件里，刷新不丢。
2. **图片只存路径**：上传的照片放到 ``uploads/``，JSON 里只记录相对路径，
   这样 JSON 文件始终很小，也方便以后换成云存储（把 save_upload 改一下就行）。
3. **原子写入**：先写临时文件再 ``os.replace``，避免写到一半中断把数据写坏。
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------- #
# 路径
# --------------------------------------------------------------------------- #

BASE_DIR = Path(__file__).resolve().parent

# 数据目录可以用环境变量覆盖（测试时指到临时目录，不污染真实记录）
DATA_DIR = Path(os.environ.get("COUPLE_DATA_DIR") or (BASE_DIR / "data"))
UPLOAD_DIR = Path(os.environ.get("COUPLE_UPLOAD_DIR") or (BASE_DIR / "uploads"))

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 各个数据文件名
CONFIG = "config.json"
CHECKINS = "checkins.json"
MOODS = "moods.json"
DIARIES = "diaries.json"
MEALS = "meals.json"
PHOTOS = "photos.json"
EXPENSES = "expenses.json"
COUNTDOWNS = "countdowns.json"
LEARNING = "learning.json"      # 英语角「我记住了」的计数
TRANSCRIPTS = "transcripts.json"  # 文学角「抄写一遍」的记录
TASKS = "tasks.json"            # 任务清单（只有条目本身）
TASK_DONE = "task_done.json"    # 任务完成情况，按日期存 → 跨天自动重置

_LOCK = threading.Lock()


# --------------------------------------------------------------------------- #
# JSON 读写
# --------------------------------------------------------------------------- #


def path_of(name: str) -> Path:
    """取某个数据文件的完整路径。"""
    return DATA_DIR / name


def read_json(name: str, default: Any) -> Any:
    """读 JSON；文件不存在或损坏时返回默认值（保证页面不会崩）。"""
    target = path_of(name)
    try:
        with target.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(name: str, data: Any) -> None:
    """原子写 JSON：先写 .tmp，再整体替换，避免写坏原文件。"""
    target = path_of(name)
    with _LOCK:
        tmp = target.with_suffix(target.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, target)


def append_json(name: str, record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """往列表型 JSON 里追加一条记录，返回新列表。"""
    data = read_json(name, [])
    if not isinstance(data, list):
        data = []
    data.append(record)
    write_json(name, data)
    return data


def remove_by_id(name: str, record_id: str) -> List[Dict[str, Any]]:
    """按 id 删除一条记录。"""
    data = [r for r in read_json(name, []) if r.get("id") != record_id]
    write_json(name, data)
    return data


# --------------------------------------------------------------------------- #
# 时间与 id
# --------------------------------------------------------------------------- #


def new_id() -> str:
    """生成一个短 id，用于定位和删除记录。"""
    return uuid.uuid4().hex[:12]


def now_stamp() -> Dict[str, str]:
    """当前日期 / 时间 / 时间戳。"""
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "ts": now.isoformat(timespec="seconds"),
        "weekday": "一二三四五六日"[now.weekday()],
    }


def today_str() -> str:
    """今天的日期字符串，如 2026-09-10。"""
    return date.today().isoformat()


def pretty_date(value: str) -> str:
    """把 2026-09-10 变成 2026年9月10日（周五）。"""
    try:
        d = date.fromisoformat(value)
    except (TypeError, ValueError):
        return value or ""
    return f"{d.year}年{d.month}月{d.day}日（周{'一二三四五六日'[d.weekday()]}）"


def month_of(value: str) -> str:
    """取日期字符串的月份，如 2026-09。"""
    return (value or "")[:7]


# --------------------------------------------------------------------------- #
# 图片上传
# --------------------------------------------------------------------------- #


def save_upload(uploaded_file, subdir: str = "misc") -> str:
    """把上传的图片存到 uploads/<subdir>/ 下，返回相对路径。

    文件名用「日期_随机码.后缀」的格式，避免同名覆盖，也方便按时间翻看。
    返回的路径是相对 uploads/ 的，例如 ``photos/20260910_ab12cd34ef56.jpg``。
    """
    folder = UPLOAD_DIR / subdir
    folder.mkdir(parents=True, exist_ok=True)

    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".heic"):
        suffix = ".jpg"
    filename = f"{datetime.now().strftime('%Y%m%d')}_{new_id()}{suffix}"
    target = folder / filename
    target.write_bytes(uploaded_file.getbuffer())

    # 只存相对 uploads/ 的路径，换机器 / 换目录都不会失效
    return str(target.relative_to(UPLOAD_DIR)).replace(os.sep, "/")


def upload_path(relative: str) -> Path:
    """把 JSON 里存的相对路径还原成绝对路径。"""
    return UPLOAD_DIR / relative


def upload_exists(relative: str) -> bool:
    """图片文件是否还在（防止图片被手动删掉后页面报错）。"""
    return bool(relative) and upload_path(relative).exists()


def delete_upload(relative: str) -> None:
    """删除图片文件（记录删除时一起调用）。"""
    try:
        upload_path(relative).unlink(missing_ok=True)
    except OSError:
        pass


# --------------------------------------------------------------------------- #
# 配置（纪念日、昵称）
# --------------------------------------------------------------------------- #

DEFAULT_SINCE = "2022-09-01"


def load_config() -> Dict[str, Any]:
    cfg = read_json(CONFIG, {})
    if not isinstance(cfg, dict):
        cfg = {}
    cfg.setdefault("together_since", DEFAULT_SINCE)
    return cfg


def save_config(cfg: Dict[str, Any]) -> None:
    write_json(CONFIG, cfg)


def together_since() -> date:
    """在一起的起始日期。"""
    raw = load_config().get("together_since", DEFAULT_SINCE)
    try:
        return date.fromisoformat(raw)
    except (TypeError, ValueError):
        return date.fromisoformat(DEFAULT_SINCE)


def days_together() -> int:
    """在一起多少天。"""
    return (date.today() - together_since()).days


# --------------------------------------------------------------------------- #
# 通用查询小工具
# --------------------------------------------------------------------------- #


def filter_by_date(records: List[Dict[str, Any]], day: Optional[str]) -> List[Dict[str, Any]]:
    """按日期筛选记录。"""
    if not day:
        return list(records)
    return [r for r in records if r.get("date") == day]


def all_dates(records: List[Dict[str, Any]]) -> List[str]:
    """记录里出现过的所有日期，倒序（新的在前）。"""
    return sorted({r.get("date", "") for r in records if r.get("date")}, reverse=True)


def all_months(records: List[Dict[str, Any]]) -> List[str]:
    """记录里出现过的所有月份，倒序。"""
    return sorted({month_of(r.get("date", "")) for r in records if r.get("date")}, reverse=True)
