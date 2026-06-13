from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SPEC_PATH = ROOT / "docs" / "SPEC.md"
SNAPSHOT_START = "<!-- AUTO_SPEC_SNAPSHOT:START -->"
SNAPSHOT_END = "<!-- AUTO_SPEC_SNAPSHOT:END -->"
LOG_START = "<!-- AUTO_REFLECTION_LOG:START -->"
LOG_END = "<!-- AUTO_REFLECTION_LOG:END -->"


RISK_RULES = [
    {
        "label": "真实交易/自动交易风险",
        "keywords": ("自动下单", "自动交易", "真实交易", "真实下单", "实盘", "买入", "卖出"),
        "risk": "可能绕过人工确认或扩大真实资金风险。",
        "required": "必须单独确认总开关、单笔限额、退出策略和人工审批流程。",
    },
    {
        "label": "阈值放松风险",
        "keywords": ("降低阈值", "降低 edge", "edge 阈值", "阈值", "放松", "更多候选", "提高候选", "扩大机会", "减少过滤"),
        "risk": "可能为了看到更多机会而降低交易纪律。",
        "required": "先证明新增样本只是研究展示，不进入可交易候选。",
    },
    {
        "label": "模型调参/过拟合风险",
        "keywords": ("调参", "权重", "漂移", "vol", "波动率", "模型", "因子", "校准"),
        "risk": "可能把短期样本噪声固化进模型。",
        "required": "检查 resolved 样本量、分组稳定性、Brier 对比和回滚方案。",
    },
    {
        "label": "数据源风险",
        "keywords": ("新增数据源", "链上", "ETF", "funding", "OI", "宏观", "抓取", "API"),
        "risk": "新数据源可能不稳定、延迟、口径不一致或污染模型。",
        "required": "先进入观察/解释层，记录健康状态，再决定是否参与模型计算。",
    },
    {
        "label": "范围扩张风险",
        "keywords": ("扩大币种", "增加币种", "15分钟", "5分钟", "高频", "更多市场"),
        "risk": "扩大范围可能增加噪声、盘口成本和维护复杂度。",
        "required": "确认新增范围有可靠价格、K 线、盘口、结算和足够样本。",
    },
]


def read_spec(path: Path = DEFAULT_SPEC_PATH) -> str:
    if not path.exists() and path != DEFAULT_SPEC_PATH and DEFAULT_SPEC_PATH.exists():
        return DEFAULT_SPEC_PATH.read_text(encoding="utf-8")
    return path.read_text(encoding="utf-8")


def _replace_between(text: str, start: str, end: str, replacement: str) -> str:
    pattern = re.compile(rf"{re.escape(start)}.*?{re.escape(end)}", re.DOTALL)
    block = f"{start}\n{replacement.rstrip()}\n{end}"
    if pattern.search(text):
        return pattern.sub(block, text)
    return text.rstrip() + "\n\n" + block + "\n"


def _fmt_percent(value: Any) -> str:
    try:
        return f"{float(value) * 100:.0f}%"
    except (TypeError, ValueError):
        return "--"


def _progress_line(label: str, item: dict[str, Any]) -> str:
    return f"- {label}: {item.get('current', 0)}/{item.get('target', 0)} ({_fmt_percent(item.get('pct'))})，还差 {item.get('remaining', 0)}"


def build_snapshot(reflection: dict[str, Any]) -> str:
    activity = reflection.get("activity") or {}
    observations = reflection.get("observations") or {}
    candidate = reflection.get("candidate_review") or {}
    paper = reflection.get("paper_trading") or {}
    calibration = reflection.get("calibration") or {}
    progress = reflection.get("validation_progress") or {}
    generated_at = reflection.get("generated_at") or datetime.utcnow().isoformat()
    return "\n".join(
        [
            f"最近更新：{generated_at}",
            "",
            "数据积累：",
            f"- 累计 runs {observations.get('runs', 0)}，rows {observations.get('rows', 0)}，candidates {observations.get('candidates', 0)}",
            f"- 24h 增量 rows +{activity.get('rows_24h', 0)}，candidates +{activity.get('candidates_24h', 0)}，watch +{activity.get('watch_24h', 0)}，avoid +{activity.get('avoid_24h', 0)}",
            "",
            "验证进展：",
            _progress_line("候选复盘初判", progress.get("candidate_50") or {}),
            _progress_line("候选复盘分组", progress.get("candidate_100") or {}),
            _progress_line("Paper trading 初判", progress.get("paper_30") or {}),
            _progress_line("模型校准初判", progress.get("calibration_50") or {}),
            "",
            "当前表现：",
            f"- 候选复盘 resolved {candidate.get('resolved', 0)}，win {_fmt_percent(candidate.get('win_rate'))}，ROI {_fmt_percent(candidate.get('roi'))}",
            f"- Paper trading resolved {paper.get('resolved', 0)}，open {paper.get('open', 0)}，ROI {_fmt_percent(paper.get('roi'))}",
            f"- 校准 better={calibration.get('better_calibration') or '--'}，model_brier={calibration.get('model_brier') if calibration.get('model_brier') is not None else '--'}，market_brier={calibration.get('market_brier') if calibration.get('market_brier') is not None else '--'}",
        ]
    )


def build_log_entry(reflection: dict[str, Any]) -> str:
    generated_at = reflection.get("generated_at") or datetime.utcnow().isoformat()
    todos = reflection.get("todos") or []
    findings = (reflection.get("data_quality") or {}).get("findings") or []
    source_findings = (reflection.get("health") or {}).get("source_findings") or []
    lines = [
        f"### {generated_at}",
        "",
        "- 数据积累和验证进展已写入自动快照。",
    ]
    if findings or source_findings:
        lines.append(f"- 风险：{'; '.join((findings + source_findings)[:3])}")
    else:
        lines.append("- 风险：暂无阻断级异常。")
    if todos:
        lines.append("- 下一步：" + "；".join(f"[{item.get('priority')}] {item.get('title')}" for item in todos[:3]))
    return "\n".join(lines)


def update_spec_with_reflection(
    reflection: dict[str, Any],
    *,
    path: Path = DEFAULT_SPEC_PATH,
    max_entries: int = 14,
) -> dict[str, Any]:
    text = read_spec(path)
    text = _replace_between(text, SNAPSHOT_START, SNAPSHOT_END, build_snapshot(reflection))
    current_match = re.search(rf"{re.escape(LOG_START)}(.*?){re.escape(LOG_END)}", text, re.DOTALL)
    current = current_match.group(1).strip() if current_match else ""
    entries = [] if current in {"", "暂无自动复盘记录。"} else re.split(r"\n(?=### )", current)
    entries = [build_log_entry(reflection)] + [entry.strip() for entry in entries if entry.strip()]
    text = _replace_between(text, LOG_START, LOG_END, "\n\n".join(entries[:max_entries]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return {"ok": True, "path": str(path), "entries": min(len(entries), max_entries)}


def check_proposal(proposal: str, *, path: Path = DEFAULT_SPEC_PATH) -> dict[str, Any]:
    _ = read_spec(path)
    matched = []
    lower = proposal.lower()
    for rule in RISK_RULES:
        if any(keyword.lower() in lower for keyword in rule["keywords"]):
            matched.append(
                {
                    "label": rule["label"],
                    "risk": rule["risk"],
                    "required_check": rule["required"],
                }
            )
    return {
        "ok": True,
        "aligned": not any(item["label"] in {"真实交易/自动交易风险", "阈值放松风险"} for item in matched),
        "proposal": proposal,
        "risks": matched,
        "required_checks": [
            "确认改动服务最终目标：证明或证伪可执行正期望 edge。",
            "确认不会降低交易纪律或绕过人工审批。",
            "确认有数据质量、样本量、回滚和日志记录。",
        ],
    }


def render_check(result: dict[str, Any]) -> str:
    lines = ["Spec Guard 检查", f"aligned: {result['aligned']}", ""]
    if result["risks"]:
        lines.append("风险:")
        for item in result["risks"]:
            lines.append(f"- {item['label']}: {item['risk']}")
            lines.append(f"  检查: {item['required_check']}")
    else:
        lines.append("风险: 未命中高风险规则。")
    lines.append("")
    lines.append("通用检查:")
    lines.extend(f"- {item}" for item in result["required_checks"])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check model/system changes against Polymtrade SPEC")
    parser.add_argument("--spec", default=str(DEFAULT_SPEC_PATH))
    parser.add_argument("--proposal", help="important change proposal to check")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.proposal:
        raise SystemExit("--proposal is required")
    result = check_proposal(args.proposal, path=Path(args.spec))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(render_check(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
