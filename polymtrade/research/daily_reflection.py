from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from polymtrade.reporting.feishu import FeishuConfigError, send_feishu_report
from polymtrade.research.paper import (
    calibration_attribution_report,
    candidate_quality_report,
    candidate_review_report,
    paper_trading_report,
)
from polymtrade.research.spec_guard import update_spec_with_reflection
from polymtrade.storage.db import (
    automation_health,
    connect,
    data_quality_report,
    insert_daily_reflection,
    insert_log,
    latest_shadow_training_runs,
    scanner_observation_summary,
)


LOCAL_TZ = ZoneInfo("Asia/Shanghai")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Polymtrade loop-engineering daily reflection")
    parser.add_argument("--db", default="polymtrade.sqlite")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--stake", type=float, default=100.0)
    parser.add_argument("--send", action="store_true", help="send the reflection to Feishu")
    parser.add_argument("--write-report", action="store_true", help="write a markdown report under reports/daily_reflection")
    parser.add_argument("--output-dir", default="reports/daily_reflection")
    parser.add_argument("--spec-path", default="docs/SPEC.md")
    parser.add_argument("--skip-spec-update", action="store_true")
    return parser.parse_args()


def _local_now() -> datetime:
    return datetime.now(LOCAL_TZ)


def _fmt_percent(value: Any, digits: int = 1) -> str:
    try:
        return f"{float(value) * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return "--"


def _fmt_money(value: Any) -> str:
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return "--"


def _fmt_number(value: Any, digits: int = 4) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "--"


def _fmt_age_minutes(value: Any) -> str:
    try:
        minutes = float(value)
    except (TypeError, ValueError):
        return "--"
    if minutes < 60:
        return f"{minutes:.0f} 分钟"
    return f"{minutes / 60:.1f} 小时"


def _progress(current: Any, target: int) -> dict[str, Any]:
    try:
        value = int(current or 0)
    except (TypeError, ValueError):
        value = 0
    return {
        "current": value,
        "target": target,
        "remaining": max(0, target - value),
        "pct": min(1.0, value / target) if target else None,
    }


def _sql_count(conn, query: str, params: tuple[Any, ...]) -> int:
    row = conn.execute(query, params).fetchone()
    return int(row[0] or 0) if row else 0


def daily_activity(conn, now: datetime) -> dict[str, Any]:
    since = (now.astimezone(timezone.utc) - timedelta(hours=24)).isoformat()
    return {
        "runs_24h": _sql_count(conn, "select count(*) from scanner_observation_runs where created_at >= ?", (since,)),
        "rows_24h": _sql_count(conn, "select count(*) from scanner_observations where created_at >= ?", (since,)),
        "candidates_24h": _sql_count(
            conn,
            "select count(*) from scanner_observations where created_at >= ? and action = 'candidate'",
            (since,),
        ),
        "watch_24h": _sql_count(
            conn,
            "select count(*) from scanner_observations where created_at >= ? and action = 'watch'",
            (since,),
        ),
        "avoid_24h": _sql_count(
            conn,
            "select count(*) from scanner_observations where created_at >= ? and action = 'avoid'",
            (since,),
        ),
        "errors_24h": _sql_count(
            conn,
            "select count(*) from system_logs where created_at >= ? and level = 'ERROR'",
            (since,),
        ),
    }


def _quality_findings(quality: dict[str, Any]) -> list[str]:
    findings = []
    if quality.get("status") != "healthy":
        findings.append(f"数据质量不是 healthy：{quality.get('status') or '--'}")
    for asset, row in sorted((quality.get("recommendations") or {}).items()):
        score = float(row.get("score") or 0)
        if score < 90:
            findings.append(f"{asset} K 线质量分 {score:.1f}，需要检查缺口/异常")
    return findings


def _source_findings(health: dict[str, Any]) -> list[str]:
    findings = []
    if health.get("status") != "healthy":
        findings.append(f"自动化状态 {health.get('status') or '--'}，最近运行 {_fmt_age_minutes(health.get('age_minutes'))} 前")
    for row in health.get("source_summary") or []:
        status = row.get("latest_status")
        if status in {"error", "network_unavailable"}:
            findings.append(f"{row.get('source')} / {row.get('component')} 最近异常：{row.get('latest_message') or status}")
        elif status == "degraded":
            findings.append(f"{row.get('source')} / {row.get('component')} 降级：{row.get('latest_message') or status}")
    return findings[:6]


def _best_quality_groups(quality: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups = [row for row in quality.get("groups") or [] if int(row.get("resolved") or 0) >= 3]
    best = sorted(groups, key=lambda row: float(row.get("roi") if row.get("roi") is not None else -999), reverse=True)[:3]
    worst = sorted(groups, key=lambda row: float(row.get("roi") if row.get("roi") is not None else 999))[:3]
    return best, worst


def build_todos(
    *,
    activity: dict[str, Any],
    health: dict[str, Any],
    candidate_summary: dict[str, Any],
    paper_summary: dict[str, Any],
    calibration_summary: dict[str, Any],
    quality_report: dict[str, Any],
    source_findings: list[str],
    data_findings: list[str],
) -> list[dict[str, str]]:
    todos: list[dict[str, str]] = []
    resolved = int(candidate_summary.get("resolved") or 0)
    paper_resolved = int(paper_summary.get("resolved") or 0)
    if source_findings or data_findings or health.get("status") != "healthy":
        todos.append(
            {
                "priority": "P0",
                "title": "先修数据可信度",
                "why": "如果价格、K 线、盘口或自动化不稳定，模型复盘会被污染。",
                "action": "检查数据源异常、盘口过期、自动化错误；修复后再评价策略表现。",
            }
        )
    if resolved < 50:
        todos.append(
            {
                "priority": "P1",
                "title": "继续积累已结算候选到 50 条",
                "why": f"当前已结算 {resolved} 条，低于初步复盘门槛。",
                "action": "保持 hourly scanner，不因短期输赢调整阈值；日报继续跟踪 resolved 增量。",
            }
        )
    elif resolved < 100:
        todos.append(
            {
                "priority": "P1",
                "title": "推进到 100 条候选复盘样本",
                "why": f"当前已结算 {resolved} 条，可以看方向，但还不够分组决策。",
                "action": "按资产、方向、edge、盘口质量拆分，观察模型是否系统性高估。",
            }
        )
    if paper_resolved < 30:
        todos.append(
            {
                "priority": "P1",
                "title": "等待 paper trading 第一批有效结算",
                "why": f"当前严格规则下 paper resolved {paper_resolved} 条，尚不能评估实操 ROI。",
                "action": "不要扩大真实仓位；只记录 open exposure 和未来结算结果。",
            }
        )
    better = calibration_summary.get("better_calibration")
    if better == "market":
        todos.append(
            {
                "priority": "P1",
                "title": "复盘模型校准落后市场的原因",
                "why": "Brier 显示市场概率比模型更接近结果。",
                "action": "检查 vol、macro、短周期因子的权重；优先收紧高估概率桶。",
            }
        )
    elif better == "insufficient":
        todos.append(
            {
                "priority": "P2",
                "title": "暂不做模型参数大改",
                "why": "校准样本不足，容易把噪声当规律。",
                "action": "只做数据质量和解释性改进，等 resolved 样本超过 50 再调参。",
            }
        )
    if int(activity.get("candidates_24h") or 0) == 0:
        todos.append(
            {
                "priority": "P2",
                "title": "检查候选稀缺是否来自阈值过严",
                "why": "最近 24 小时没有新增 candidate，可能是市场无机会，也可能是过滤过严。",
                "action": "比较 candidate / watch / avoid 的比例，必要时只增加“研究机会”展示，不放松交易门槛。",
            }
        )
    if not todos:
        todos.append(
            {
                "priority": "P2",
                "title": "维持当前策略并观察分组稳定性",
                "why": "数据链路健康，样本仍在累积。",
                "action": "关注质量分析中 resolved >= 3 的分组，寻找稳定的正/负 ROI 模式。",
            }
        )
    return todos[:6]


def build_reflection(conn, *, limit: int, stake: float) -> dict[str, Any]:
    now = _local_now()
    health = automation_health(conn, max_age_minutes=150)
    observations = scanner_observation_summary(conn)
    activity = daily_activity(conn, now)
    data_quality = data_quality_report(conn)
    candidate_review = candidate_review_report(conn, limit=limit, stake=stake)
    paper = paper_trading_report(conn, limit=limit, stake=stake)
    calibration = calibration_attribution_report(conn, limit=limit, stake=stake)
    quality = candidate_quality_report(conn, limit=limit, stake=stake)
    shadow_runs = latest_shadow_training_runs(conn, limit=1)
    shadow_training = shadow_runs[0] if shadow_runs else None
    source_findings = _source_findings(health)
    data_findings = _quality_findings(data_quality)
    todos = build_todos(
        activity=activity,
        health=health,
        candidate_summary=candidate_review.get("summary") or {},
        paper_summary=paper.get("summary") or {},
        calibration_summary=calibration.get("summary") or {},
        quality_report=quality,
        source_findings=source_findings,
        data_findings=data_findings,
    )
    best_groups, worst_groups = _best_quality_groups(quality)
    candidate_summary = candidate_review.get("summary") or {}
    paper_summary = paper.get("summary") or {}
    calibration_summary = calibration.get("summary") or {}
    return {
        "generated_at": now.isoformat(),
        "activity": activity,
        "health": {
            "status": health.get("status"),
            "age_minutes": health.get("age_minutes"),
            "source_findings": source_findings,
        },
        "data_quality": {
            "status": data_quality.get("status"),
            "findings": data_findings,
        },
        "observations": observations,
        "candidate_review": candidate_summary,
        "paper_trading": paper_summary,
        "calibration": calibration_summary,
        "quality": quality.get("summary") or {},
        "shadow_training": shadow_training,
        "validation_progress": {
            "candidate_50": _progress(candidate_summary.get("resolved"), 50),
            "candidate_100": _progress(candidate_summary.get("resolved"), 100),
            "paper_30": _progress(paper_summary.get("resolved"), 30),
            "paper_50": _progress(paper_summary.get("resolved"), 50),
            "calibration_50": _progress(calibration_summary.get("resolved"), 50),
            "calibration_100": _progress(calibration_summary.get("resolved"), 100),
        },
        "best_groups": best_groups,
        "worst_groups": worst_groups,
        "todos": todos,
    }


def _progress_line(label: str, item: dict[str, Any]) -> str:
    return (
        f"- {label}：{item.get('current', 0)}/{item.get('target', 0)} "
        f"({_fmt_percent(item.get('pct'), 0)}) · 还差 {item.get('remaining', 0)}"
    )


def _status_label(value: Any) -> str:
    labels = {
        "healthy": "健康",
        "degraded": "降级",
        "blocked": "阻断",
        "stale": "过期",
        "missing": "缺失",
        "ok": "正常",
        "observe_only": "观察",
    }
    return labels.get(str(value or "").lower(), str(value or "--"))


def _daily_verdict(reflection: dict[str, Any]) -> str:
    health = reflection["health"]
    data_quality = reflection["data_quality"]
    activity = reflection["activity"]
    candidate = reflection["candidate_review"]
    shadow = reflection.get("shadow_training") or {}
    shadow_summary = shadow.get("summary") or {}
    shadow_improvement = shadow_summary.get("improvement") or {}
    findings = list(data_quality.get("findings") or []) + list(health.get("source_findings") or [])
    verdicts = []
    if health.get("status") in {"blocked", "missing"} or data_quality.get("status") == "blocked":
        verdicts.append("有阻断项，先修数据/自动化。")
    elif findings:
        verdicts.append("系统可运行，但存在需要跟踪的降级项。")
    else:
        verdicts.append("系统运行正常，可以继续积累样本。")
    if int(candidate.get("resolved") or 0) < 50:
        verdicts.append("候选复盘样本仍不足，暂不升级策略。")
    elif candidate.get("roi") is not None and float(candidate.get("roi") or 0) <= 0:
        verdicts.append("候选复盘收益未证明为正，继续保持观察纪律。")
    if shadow_improvement.get("brier_delta") is not None:
        delta = float(shadow_improvement.get("brier_delta") or 0)
        verdicts.append("Shadow ML 本次优于 GBM。" if delta > 0 else "Shadow ML 本次未优于 GBM。")
    if int(activity.get("errors_24h") or 0) > 0:
        verdicts.append(f"过去 24h 有 {activity.get('errors_24h')} 条错误日志，需要复核。")
    return " ".join(verdicts)


def render_report(reflection: dict[str, Any]) -> str:
    candidate = reflection["candidate_review"]
    paper = reflection["paper_trading"]
    calibration = reflection["calibration"]
    shadow = reflection.get("shadow_training") or {}
    shadow_summary = shadow.get("summary") or {}
    shadow_metrics = shadow_summary.get("metrics") or {}
    shadow_improvement = shadow_summary.get("improvement") or {}
    activity = reflection["activity"]
    observations = reflection["observations"]
    health = reflection["health"]
    progress = reflection.get("validation_progress") or {}
    generated = datetime.fromisoformat(reflection["generated_at"]).strftime("%Y-%m-%d %H:%M:%S %Z")
    findings = list(reflection["data_quality"].get("findings") or []) + list(health.get("source_findings") or [])
    lines = [
        "Polymtrade 每日系统执行简报",
        f"生成时间：{generated}",
        "",
        "今日结论",
        f"- {_daily_verdict(reflection)}",
        "",
        "1. 运行状态",
        f"- 自动化状态：{_status_label(health.get('status'))} · 最近运行：{_fmt_age_minutes(health.get('age_minutes'))}前",
        f"- 24h 扫描：run {activity['runs_24h']} · rows {activity['rows_24h']} · candidate {activity['candidates_24h']} · watch {activity['watch_24h']} · avoid {activity['avoid_24h']}",
        f"- 24h 错误：{activity['errors_24h']} 条",
        "",
        "2. 数据积累",
        f"- 累计观测：runs {observations.get('runs', 0)} · rows {observations.get('rows', 0)} · candidates {observations.get('candidates', 0)}",
        f"- 24h 增量：rows +{activity['rows_24h']} · candidates +{activity['candidates_24h']} · watch +{activity['watch_24h']} · avoid +{activity['avoid_24h']}",
        f"- 当前复盘窗口：{candidate.get('tracked', 0)} 条 · candidate/rows {observations.get('candidates', 0)}/{observations.get('rows', 0)}",
        "",
        "3. 验证进展",
        _progress_line("候选复盘初判", progress.get("candidate_50") or {}),
        _progress_line("候选复盘分组", progress.get("candidate_100") or {}),
        _progress_line("Paper trading 初判", progress.get("paper_30") or {}),
        _progress_line("模型校准初判", progress.get("calibration_50") or {}),
        "",
        "4. 策略与模型表现",
        f"- 候选复盘：tracked {candidate.get('tracked', 0)} · resolved {candidate.get('resolved', 0)} · win {_fmt_percent(candidate.get('win_rate'))} · PnL {_fmt_money(candidate.get('pnl'))} · ROI {_fmt_percent(candidate.get('roi'))}",
        f"- Paper trading：tracked {paper.get('tracked', 0)} · resolved {paper.get('resolved', 0)} · open {paper.get('open', 0)} · exposure {_fmt_money(paper.get('open_exposure'))} · ROI {_fmt_percent(paper.get('roi'))}",
        f"- 校准对比：samples {calibration.get('samples', 0)} · resolved {calibration.get('resolved', 0)} · model Brier {_fmt_number(calibration.get('model_brier'))} · market Brier {_fmt_number(calibration.get('market_brier'))} · better {calibration.get('better_calibration') or '--'}",
        f"- Shadow ML：samples {shadow_summary.get('samples', '--')} · validation {shadow_summary.get('validation_samples', '--')} · GBM Brier {_fmt_number(shadow_metrics.get('base_brier'))} · shadow Brier {_fmt_number(shadow_metrics.get('shadow_brier'))} · Δ {_fmt_number(shadow_improvement.get('brier_delta'))} · 状态 {_status_label(shadow_summary.get('decision') or 'observe_only')}",
        "",
        "5. 风险与异常",
    ]
    if findings:
        lines.extend(f"- {item}" for item in findings[:8])
    else:
        lines.append("- 暂无阻断级异常，继续观察。")
    if reflection.get("best_groups") or reflection.get("worst_groups"):
        lines.append("")
        lines.append("6. 分组线索")
        for row in reflection.get("best_groups") or []:
            lines.append(f"- 较好：{row.get('kind')}={row.get('name')} · resolved {row.get('resolved')} · ROI {_fmt_percent(row.get('roi'))}")
        for row in reflection.get("worst_groups") or []:
            lines.append(f"- 较差：{row.get('kind')}={row.get('name')} · resolved {row.get('resolved')} · ROI {_fmt_percent(row.get('roi'))}")
    lines.extend(["", "7. 明日 TODO"])
    for idx, todo in enumerate(reflection.get("todos") or [], 1):
        lines.append(f"{idx}. [{todo['priority']}] {todo['title']}")
        lines.append(f"   原因：{todo['why']}")
        lines.append(f"   动作：{todo['action']}")
    return "\n".join(lines)


def write_markdown_report(text: str, output_dir: str, generated_at: str) -> Path:
    dt = datetime.fromisoformat(generated_at)
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    report_path = path / f"{dt.strftime('%Y-%m-%d')}.md"
    report_path.write_text(text + "\n", encoding="utf-8")
    return report_path


def _notification_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(result.get("ok")),
        "channel": result.get("channel"),
        "status": result.get("status"),
        "receive_id_type": result.get("receive_id_type"),
    }


def main() -> int:
    args = parse_args()
    result: dict[str, Any] = {"ok": True, "sent": False, "report_path": None}
    try:
        with connect(args.db) as conn:
            reflection = build_reflection(conn, limit=args.limit, stake=args.stake)
            text = render_report(reflection)
            result["reflection"] = reflection
            if args.write_report:
                result["report_path"] = str(write_markdown_report(text, args.output_dir, reflection["generated_at"]))
            if args.send:
                try:
                    notification = send_feishu_report(text)
                    result["notification"] = _notification_summary(notification)
                    result["sent"] = bool(notification.get("ok"))
                except FeishuConfigError as exc:
                    result["ok"] = False
                    result["notification"] = {"ok": False, "error": "missing Feishu configuration", "detail": str(exc)}
            if not args.skip_spec_update:
                result["spec_update"] = update_spec_with_reflection(reflection, path=Path(args.spec_path))
            reflection_dt = datetime.fromisoformat(reflection["generated_at"])
            result["reflection_id"] = insert_daily_reflection(
                conn,
                reflection_date=reflection_dt.date().isoformat(),
                generated_at=reflection["generated_at"],
                summary={key: value for key, value in reflection.items() if key != "todos"},
                todos=reflection.get("todos") or [],
                report_path=result.get("report_path"),
                sent=bool(result.get("sent")),
            )
            level = "INFO" if result["ok"] else "WARN"
            message = "Daily loop reflection completed" if result["ok"] else "Daily loop reflection completed with warning"
            insert_log(conn, level, "reflection", message, json.dumps(result, ensure_ascii=False))
        print(json.dumps({k: v for k, v in result.items() if k != "reflection"}, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1
    except Exception as exc:  # noqa: BLE001 - cron output should expose failures
        result["ok"] = False
        result["error"] = str(exc)
        try:
            with connect(args.db) as conn:
                insert_log(conn, "ERROR", "reflection", f"Daily loop reflection failed: {exc}", json.dumps(result, ensure_ascii=False))
        except Exception:
            pass
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
