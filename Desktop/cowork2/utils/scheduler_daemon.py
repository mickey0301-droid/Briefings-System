"""
scheduler_daemon.py

背景排程執行器。使用 st.cache_resource 確保每個 Streamlit 伺服器
程序只啟動一個 APScheduler 實例，即使有多個使用者同時連線也不會
重複建立排程器。

每 60 秒檢查一次是否有到期的排程，若有則呼叫 run_schedule_job()。
"""

from __future__ import annotations

import logging
from datetime import datetime
import pytz

import streamlit as st

TW_TZ = pytz.timezone("Asia/Taipei")

def now_tw() -> datetime:
    return datetime.now(TW_TZ).replace(tzinfo=None)

logger = logging.getLogger(__name__)


def _tick() -> None:
    """每分鐘由 APScheduler 呼叫一次，檢查並執行到期的排程。"""
    try:
        # 使用與 app.py 相同的 loaders 函式，確保讀取同一份設定
        from utils.loaders import load_auto_export, load_auto_export_state, save_auto_export_state
        from utils.auto_export import should_run, run_schedule_job

        config = load_auto_export()
        if not config.get("enabled", True):
            return

        state = load_auto_export_state()
        now = now_tw()

        for schedule in config.get("schedules", []):
            schedule_name = schedule.get("name", "unnamed")
            try:
                ok, run_key = should_run(schedule, state=state, now=now)
                if not ok:
                    continue

                logger.info(f"[Scheduler] 執行排程: {schedule_name} @ {run_key}")

                # 標記正在執行
                state.setdefault("running_now", [])
                if schedule_name not in state["running_now"]:
                    state["running_now"].append(schedule_name)
                state["running_started_at"] = state.get("running_started_at", {})
                state["running_started_at"][schedule_name] = now.strftime("%Y-%m-%d %H:%M:%S")
                save_auto_export_state(state)

                started_at = now_tw()
                result = run_schedule_job(schedule)
                finished_at = now_tw()
                duration_sec = int((finished_at - started_at).total_seconds())

                # 清除「正在執行」標記
                state["running_now"] = [n for n in state.get("running_now", []) if n != schedule_name]
                if schedule_name in state.get("running_started_at", {}):
                    del state["running_started_at"][schedule_name]

                # 寫入執行歷史（保留最近 50 筆）
                history_entry = {
                    "name": schedule_name,
                    "started_at": started_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "finished_at": finished_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "duration_sec": duration_sec,
                    "ok": bool(result.get("ok")),
                    "message": result.get("message", "") or result.get("error", ""),
                }
                history = state.setdefault("run_history", [])
                history.insert(0, history_entry)
                state["run_history"] = history[:50]

                if result.get("ok"):
                    state.setdefault("last_run_keys", {})[schedule_name] = run_key
                    state.setdefault("last_runs", {})[schedule_name] = run_key
                    save_auto_export_state(state)
                    logger.info(f"[Scheduler] 完成: {result.get('message', '')}")
                else:
                    save_auto_export_state(state)
                    logger.error(f"[Scheduler] 失敗: {result.get('error', '')}")

            except Exception as e:
                # 確保即使出錯也清除「正在執行」標記
                state["running_now"] = [n for n in state.get("running_now", []) if n != schedule_name]
                history = state.setdefault("run_history", [])
                history.insert(0, {
                    "name": schedule_name,
                    "started_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "finished_at": now_tw().strftime("%Y-%m-%d %H:%M:%S"),
                    "duration_sec": 0,
                    "ok": False,
                    "message": str(e),
                })
                state["run_history"] = history[:50]
                save_auto_export_state(state)
                logger.error(f"[Scheduler] 排程 {schedule_name} 錯誤: {e}")

    except Exception as e:
        logger.error(f"[Scheduler] _tick 整體錯誤: {e}")


@st.cache_resource
def start_background_scheduler():
    """
    啟動背景 APScheduler。
    st.cache_resource 保證此函式在整個伺服器生命週期只執行一次，
    即使多個使用者同時造訪也不會重複啟動排程器。
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler(daemon=True)
        # 每 60 秒執行一次 _tick，對齊整分鐘
        scheduler.add_job(
            _tick,
            trigger="interval",
            seconds=60,
            id="briefings_scheduler",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=30,
        )
        scheduler.start()
        logger.info("[Scheduler] APScheduler 已啟動（每 60 秒檢查一次排程）")
        return scheduler

    except ImportError:
        logger.warning(
            "[Scheduler] apscheduler 未安裝，排程功能停用。"
            " 請在 requirements.txt 加入 apscheduler 並重新部署。"
        )
        return None

    except Exception as e:
        logger.error(f"[Scheduler] 啟動失敗: {e}")
        return None
