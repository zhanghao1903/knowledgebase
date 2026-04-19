"""Root conftest — test log plugin + shared fixtures.

Automatically records every test run to tests/logs/ as a JSON file
with version, timestamp, duration, and per-test results.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.config import settings

LOGS_DIR = Path(__file__).parent / "logs"


# ---------------------------------------------------------------------------
# Test Log Plugin — writes JSON report after each test session
# ---------------------------------------------------------------------------

class TestLogPlugin:
    """Pytest plugin that records test results to tests/logs/."""

    def __init__(self):
        self.results: list[dict] = []
        self.start_time: float = 0

    def pytest_sessionstart(self, session):
        self.start_time = time.time()

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            self.results.append({
                "name": report.nodeid,
                "status": report.outcome,  # passed / failed / skipped
                "duration_seconds": round(report.duration, 4),
            })

    def pytest_sessionfinish(self, session, exitstatus):
        duration = round(time.time() - self.start_time, 2)
        passed = sum(1 for r in self.results if r["status"] == "passed")
        failed = sum(1 for r in self.results if r["status"] == "failed")
        skipped = sum(1 for r in self.results if r["status"] == "skipped")

        report = {
            "version": settings.VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": duration,
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "exit_code": exitstatus,
            "results": self.results,
        }

        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        log_path = LOGS_DIR / f"test_run_{ts}.json"
        log_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))


def pytest_configure(config):
    config.pluginmanager.register(TestLogPlugin(), "test_log_plugin")


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_txt_content() -> str:
    """A multi-paragraph Chinese + English text for testing."""
    return (
        "知识库系统设计文档\n\n"
        "本文档描述了知识库系统的核心架构设计。系统支持PDF、TXT、DOCX三种文件格式。\n\n"
        "第一章：技术选型\n"
        "后端使用FastAPI框架，数据库使用PostgreSQL配合pgvector扩展。"
        "这套方案能同时支持关系型查询和向量检索。\n\n"
        "第二章：文档处理流程\n"
        "文档上传后经过解析、切块、向量化三个步骤，最终存入数据库。"
        "切块时使用滑动窗口策略，保持语义完整性。\n\n"
        "第三章：检索与问答\n"
        "用户提问后系统会将问题向量化，然后在pgvector中进行余弦相似度搜索。"
        "检索到的内容会被拼接成prompt发送给LLM生成回答。"
    )
