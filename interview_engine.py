"""
自适应专家访谈引擎 - 核心状态管理与控制逻辑
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class InterviewState:
    """访谈状态管理类"""

    # 类常量
    AVG_MINUTES_PER_QUESTION = 1.5

    # 默认话题维度
    DEFAULT_DIMENSIONS = [
        "core_principles",
        "decision_framework",
        "typical_cases",
        "failures_lessons",
        "cognitive_boundary"
    ]

    # 阶段占比配置
    PHASE_CONFIG = {
        "warmup": {"ratio": 0.10, "label": "破冰期"},
        "foundation": {"ratio": 0.30, "label": "基础期"},
        "deep": {"ratio": 0.40, "label": "深入期"},
        "advanced": {"ratio": 0.20, "label": "升华期"}
    }

    def __init__(self, data: Dict[str, Any]):
        self.data = data

    @property
    def meta(self) -> Dict[str, Any]:
        return self.data["meta"]

    @property
    def progress(self) -> Dict[str, Any]:
        return self.data["progress"]

    @property
    def coverage(self) -> Dict[str, Any]:
        return self.data["coverage"]

    @property
    def qa_pairs(self) -> List[Dict[str, Any]]:
        return self.data["qa_pairs"]

    @property
    def context(self) -> Dict[str, Any]:
        return self.data["context"]

    @classmethod
    def init(cls, domain: str, expert_position: str, target_count: int,
             focus_keywords: List[str]) -> "InterviewState":
        """初始化一个新的访谈状态"""
        estimated_duration = target_count * cls.AVG_MINUTES_PER_QUESTION

        dimensions = {}
        for dim in cls.DEFAULT_DIMENSIONS:
            dimensions[dim] = {"covered": False, "q_ids": []}

        data = {
            "meta": {
                "domain": domain,
                "expert_position": expert_position,
                "target_count": target_count,
                "focus_keywords": focus_keywords,
                "created_at": datetime.now().isoformat(),
                "estimated_duration_min": int(estimated_duration)
            },
            "progress": {
                "current_phase": "warmup",
                "completed_count": 0,
                "target_count": target_count,
                "follow_up_count": 0,
                "elapsed_min": 0,
                "fast_mode": False
            },
            "coverage": {
                "dimensions": dimensions
            },
            "qa_pairs": [],
            "context": {
                "current_topic": None,
                "current_follow_up_depth": 0,
                "recent_topics": [],
                "rejected_dimensions": []
            }
        }
        return cls(data)

    def add_qa_pair(self, qa: Dict[str, Any]) -> None:
        """添加一条问答对"""
        qa_copy = qa.copy()
        qa_copy["timestamp"] = datetime.now().isoformat()
        self.data["qa_pairs"].append(qa_copy)
        self.data["progress"]["completed_count"] += 1
        # 自动更新话题覆盖
        dimension = qa_copy.get("dimension")
        if dimension and dimension in self.data["coverage"]["dimensions"]:
            self.update_coverage(dimension, qa_copy["q_id"])

    def update_coverage(self, dimension: str, q_id: int) -> None:
        """更新话题覆盖状态"""
        if dimension not in self.data["coverage"]["dimensions"]:
            raise ValueError(f"Unknown dimension: {dimension!r}")
        self.data["coverage"]["dimensions"][dimension]["covered"] = True
        if q_id not in self.data["coverage"]["dimensions"][dimension]["q_ids"]:
            self.data["coverage"]["dimensions"][dimension]["q_ids"].append(q_id)

    def to_prompt_context(self) -> str:
        """生成供 LLM 使用的状态摘要文本"""
        lines = [
            f"领域：{self.meta['domain']}",
            f"专家定位：{self.meta['expert_position']}",
            f"当前阶段：{self.progress['current_phase']}",
            f"进度：{self.progress['completed_count']}/{self.progress['target_count']}",
            f"已用时间：约 {self.progress['elapsed_min']} 分钟",
            f"预计总时长：约 {self.meta['estimated_duration_min']} 分钟",
            f"快速模式：{'是' if self.progress['fast_mode'] else '否'}",
            "",
            "话题覆盖情况：",
        ]
        for dim, info in self.coverage["dimensions"].items():
            status = "已覆盖" if info["covered"] else "未覆盖"
            q_ids = f" (Q{','.join(map(str, info['q_ids']))})" if info["q_ids"] else ""
            lines.append(f"  - {dim}: {status}{q_ids}")

        if self.meta["focus_keywords"]:
            lines.extend(["", f"聚焦关键词：{', '.join(self.meta['focus_keywords'])}"])

        return "\n".join(lines)

    def save(self, path: str) -> None:
        """保存状态到 JSON 文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "InterviewState":
        """从 JSON 文件加载状态"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(data)


class PhaseController:
    """阶段控制器 - 管理访谈四阶段切换"""

    PHASE_CONFIG = {
        "warmup": {"ratio": 0.10, "label": "破冰期"},
        "foundation": {"ratio": 0.30, "label": "基础期"},
        "deep": {"ratio": 0.40, "label": "深入期"},
        "advanced": {"ratio": 0.20, "label": "升华期"}
    }

    PHASE_ORDER = ["warmup", "foundation", "deep", "advanced"]

    @classmethod
    def get_current_phase(cls, state: InterviewState) -> str:
        """根据当前进度计算应该处于的阶段"""
        completed = state.progress["completed_count"]
        target = state.progress["target_count"]
        if target == 0:
            return "warmup"

        ratio = completed / target
        cumulative = 0.0
        for phase in cls.PHASE_ORDER:
            cumulative += cls.PHASE_CONFIG[phase]["ratio"]
            if ratio < cumulative:
                return phase
        return "advanced"

    @classmethod
    def should_advance(cls, state: InterviewState) -> bool:
        """判断是否需要推进到下一阶段"""
        current = state.progress["current_phase"]
        calculated = cls.get_current_phase(state)
        current_idx = cls.PHASE_ORDER.index(current)
        calculated_idx = cls.PHASE_ORDER.index(calculated)
        return calculated_idx > current_idx

    @classmethod
    def apply_phase_update(cls, state: InterviewState) -> None:
        """应用阶段更新"""
        new_phase = cls.get_current_phase(state)
        state.progress["current_phase"] = new_phase

    @classmethod
    def get_estimated_remaining_min(cls, state: InterviewState) -> int:
        """计算预计剩余时间（分钟）"""
        remaining = state.progress["target_count"] - state.progress["completed_count"]
        return int(remaining * InterviewState.AVG_MINUTES_PER_QUESTION)

    @classmethod
    def is_fast_mode(cls, state: InterviewState) -> bool:
        """判断是否应进入快速模式"""
        estimated_total = state.meta["estimated_duration_min"]
        elapsed = state.progress["elapsed_min"]
        return elapsed > estimated_total * 1.2


# 预留其他类的位置（后续任务实现）


class TopicTracker:
    """话题追踪器 - 管理话题维度覆盖"""

    DIMENSION_MAP = {
        "core_principles": "核心原则",
        "decision_framework": "决策框架",
        "typical_cases": "典型案例",
        "failures_lessons": "失败教训",
        "cognitive_boundary": "认知边界"
    }

    @classmethod
    def get_uncovered_dimensions(cls, state: InterviewState) -> List[str]:
        """获取未覆盖的话题维度列表"""
        uncovered = []
        for dim, info in state.coverage["dimensions"].items():
            if not info["covered"]:
                uncovered.append(dim)
        return uncovered

    @classmethod
    def get_recommended_dimension(cls, state: InterviewState) -> str:
        """推荐下一个应覆盖的话题维度"""
        uncovered = cls.get_uncovered_dimensions(state)
        if not uncovered:
            # 全部已覆盖，返回最近的话题
            return state.context["current_topic"] or "core_principles"
        return uncovered[0]

    @classmethod
    def mark_covered(cls, state: InterviewState, dimension: str, q_id: int) -> None:
        """标记某个维度已被覆盖"""
        state.update_coverage(dimension, q_id)

    @classmethod
    def get_coverage_summary(cls, state: InterviewState) -> str:
        """生成话题覆盖摘要文本"""
        lines = []
        for dim, info in state.coverage["dimensions"].items():
            label = cls.DIMENSION_MAP.get(dim, dim)
            status = "✓" if info["covered"] else "○"
            q_ids = f" (Q{','.join(map(str, info['q_ids']))})" if info["q_ids"] else ""
            lines.append(f"  {status} {label}{q_ids}")
        return "\n".join(lines)


class FollowUpController:
    """追问控制器 - 管理追问规则和限制"""

    MAX_CONSECUTIVE_FOLLOW_UPS = 2
    MAX_FOLLOW_UP_RATIO = 0.30

    @classmethod
    def can_follow_up(cls, state: InterviewState) -> bool:
        """判断是否可以进行追问"""
        if state.progress["fast_mode"]:
            return False
        if state.context["current_follow_up_depth"] >= cls.MAX_CONSECUTIVE_FOLLOW_UPS:
            return False
        target = state.progress["target_count"]
        max_follow_ups = max(1, int(target * cls.MAX_FOLLOW_UP_RATIO))
        if state.progress["follow_up_count"] >= max_follow_ups:
            return False
        return True

    @classmethod
    def get_follow_up_limit_reason(cls, state: InterviewState) -> Optional[str]:
        """获取追问限制的原因"""
        if state.progress["fast_mode"]:
            return "当前处于快速模式，禁止追问"
        if state.context["current_follow_up_depth"] >= cls.MAX_CONSECUTIVE_FOLLOW_UPS:
            return f"已达到连续追问上限 ({cls.MAX_CONSECUTIVE_FOLLOW_UPS}次)"
        target = state.progress["target_count"]
        max_follow_ups = max(1, int(target * cls.MAX_FOLLOW_UP_RATIO))
        if state.progress["follow_up_count"] >= max_follow_ups:
            return f"已达到总追问数上限 ({max_follow_ups}次)"
        return None

    @classmethod
    def increment_follow_up(cls, state: InterviewState) -> None:
        """增加追问计数"""
        state.progress["follow_up_count"] += 1
        state.context["current_follow_up_depth"] += 1

    @classmethod
    def reset_follow_up_depth(cls, state: InterviewState) -> None:
        """重置当前话题的追问深度（换话题时调用）"""
        state.context["current_follow_up_depth"] = 0

    @classmethod
    def should_skip_topic(cls, state: InterviewState, reject_count: int = 0) -> bool:
        """判断是否应该跳过当前话题"""
        if reject_count >= 2:
            return True
        return False


class OutputFormatter:
    """输出格式化 - 负责各种输出格式的生成"""

    PHASE_LABELS = {
        "warmup": "破冰期",
        "foundation": "基础期",
        "deep": "深入期",
        "advanced": "升华期"
    }

    @classmethod
    def to_jsonl(cls, state: InterviewState) -> str:
        """生成 JSON Lines 格式输出"""
        lines = []
        for qa in state.qa_pairs:
            obj = {
                "q_id": qa["q_id"],
                "phase": qa["phase"],
                "type": qa["type"],
                "dimension": qa.get("dimension", ""),
                "question": qa["question"],
                "answer": qa["answer"],
                "timestamp": qa.get("timestamp", "")
            }
            if "scenario" in qa:
                obj["scenario"] = qa["scenario"]
            lines.append(json.dumps(obj, ensure_ascii=False))
        return "\n".join(lines)

    @classmethod
    def to_snapshot(cls, state: InterviewState) -> Dict[str, Any]:
        """生成状态快照（用于中断恢复）"""
        covered_topics = [
            dim for dim, info in state.coverage["dimensions"].items()
            if info["covered"]
        ]
        return {
            "completed_q_ids": [qa["q_id"] for qa in state.qa_pairs],
            "current_phase": state.progress["current_phase"],
            "covered_topics": covered_topics,
            "remaining_target": state.progress["target_count"] - state.progress["completed_count"],
            "last_activity": datetime.now().isoformat()
        }

    @classmethod
    def format_status(cls, state: InterviewState) -> str:
        """格式化当前状态摘要"""
        phase = state.progress["current_phase"]
        phase_label = cls.PHASE_LABELS.get(phase, phase)
        completed = state.progress["completed_count"]
        target = state.progress["target_count"]
        remaining = target - completed
        remaining_min = PhaseController.get_estimated_remaining_min(state)

        lines = [
            f"📌 领域：{state.meta['domain']}",
            f"当前阶段：{phase_label} ({phase})",
            f"进度：{completed}/{target}（还剩 {remaining} 条）",
            f"预计剩余时间：约 {remaining_min} 分钟",
            f"追问次数：{state.progress['follow_up_count']}",
            "",
            "话题覆盖：",
        ]
        lines.append(TopicTracker.get_coverage_summary(state))
        return "\n".join(lines)

    @classmethod
    def format_opening(cls, state: InterviewState) -> str:
        """格式化访谈开场说明"""
        phase_breakdown = []
        for phase, config in PhaseController.PHASE_CONFIG.items():
            count = int(state.meta["target_count"] * config["ratio"])
            label = cls.PHASE_LABELS.get(phase, phase)
            phase_breakdown.append(f"  • {label}（{count}题）")

        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🎯 自适应专家访谈",
            "",
            f"📌 领域：{state.meta['domain']}",
            f"👤 专家定位：{state.meta['expert_position']}",
            f"📝 目标问答对：{state.meta['target_count']} 条",
            f"⏱️ 预计总时长：约 {state.meta['estimated_duration_min']} 分钟",
            "",
            "📊 问题难度阶梯：",
        ]
        lines.extend(phase_breakdown)
        lines.extend([
            "",
            "🚪 退出方式：",
            "  • 随时说\"暂停\"可保存当前进度",
            "  • 连续两次说\"跳过\"将自动换话题",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ])
        return "\n".join(lines)

    @classmethod
    def format_question_display(cls, q_id: int, total: int, phase: str,
                                 question_type: str, question: str,
                                 scenario: str = None) -> str:
        """格式化问题展示文本"""
        phase_label = cls.PHASE_LABELS.get(phase, phase)
        type_labels = {
            "choice": "选择题",
            "judge": "判断题",
            "open": "简答题",
            "case": "案例分析",
            "hypothetical": "假设情境"
        }
        type_label = type_labels.get(question_type, question_type)

        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📋 问题 [{q_id}/{total}] | 阶段：{phase_label}",
            "",
            f"【{type_label}】",
        ]
        if scenario:
            lines.extend([f"场景：{scenario}", ""])
        lines.extend([
            question,
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ])
        return "\n".join(lines)


def main(args=None):
    """CLI 入口"""
    import argparse

    parser = argparse.ArgumentParser(description="自适应专家访谈引擎")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # init 命令
    init_parser = subparsers.add_parser('init', help='初始化访谈')
    init_parser.add_argument('--domain', required=True, help='领域')
    init_parser.add_argument('--expert', required=True, help='专家定位')
    init_parser.add_argument('--target', type=int, required=True, help='目标问答对数量')
    init_parser.add_argument('--keywords', default='', help='聚焦关键词（逗号分隔）')
    init_parser.add_argument('--output', required=True, help='输出状态文件路径')

    # status 命令
    status_parser = subparsers.add_parser('status', help='查看当前状态')
    status_parser.add_argument('--state', required=True, help='状态文件路径')

    # update 命令
    update_parser = subparsers.add_parser('update', help='更新状态（添加问答对）')
    update_parser.add_argument('--state', required=True, help='状态文件路径')
    update_parser.add_argument('--q-id', type=int, required=True, help='问题ID')
    update_parser.add_argument('--question', required=True, help='问题文本')
    update_parser.add_argument('--answer', required=True, help='回答文本')
    update_parser.add_argument('--analysis', required=True,
                               help='LLM分析结果（JSON字符串）')

    # export 命令
    export_parser = subparsers.add_parser('export', help='导出结果')
    export_parser.add_argument('--state', required=True, help='状态文件路径')
    export_parser.add_argument('--format', default='jsonl', choices=['jsonl'],
                               help='输出格式')
    export_parser.add_argument('--output', required=True, help='输出文件路径')

    # snapshot 命令
    snapshot_parser = subparsers.add_parser('snapshot', help='导出状态快照')
    snapshot_parser.add_argument('--state', required=True, help='状态文件路径')
    snapshot_parser.add_argument('--output', required=True, help='快照输出路径')

    parsed = parser.parse_args(args)

    if parsed.command == 'init':
        keywords = [k.strip() for k in parsed.keywords.split(',') if k.strip()]
        state = InterviewState.init(
            domain=parsed.domain,
            expert_position=parsed.expert,
            target_count=parsed.target,
            focus_keywords=keywords
        )
        state.save(parsed.output)
        print(OutputFormatter.format_opening(state))
        print(f"\n✅ 状态已保存至：{parsed.output}")

    elif parsed.command == 'status':
        state = InterviewState.load(parsed.state)
        PhaseController.apply_phase_update(state)
        print(OutputFormatter.format_status(state))

    elif parsed.command == 'update':
        state = InterviewState.load(parsed.state)
        analysis = json.loads(parsed.analysis)

        qa = {
            "q_id": parsed.q_id,
            "phase": state.progress["current_phase"],
            "type": "open",
            "dimension": analysis.get("dimension", "core_principles"),
            "question": parsed.question,
            "answer": parsed.answer
        }

        if analysis.get("needs_follow_up"):
            qa["is_follow_up"] = True
            FollowUpController.increment_follow_up(state)
        else:
            FollowUpController.reset_follow_up_depth(state)

        dimension = analysis.get("dimension")
        if dimension:
            TopicTracker.mark_covered(state, dimension, parsed.q_id)
            state.context["current_topic"] = dimension

        state.add_qa_pair(qa)
        PhaseController.apply_phase_update(state)

        if PhaseController.is_fast_mode(state):
            state.progress["fast_mode"] = True

        state.save(parsed.state)

        print(f"✅ 已更新：问题 {parsed.q_id} 已记录")
        print(f"\n当前进度：{state.progress['completed_count']}/{state.progress['target_count']}")

        if state.progress["completed_count"] >= state.progress["target_count"]:
            print("\n🎉 已达到目标数量！访谈完成。")
            print(f"使用以下命令导出结果：")
            print(f"  python interview_engine.py export --state {parsed.state} --output result.jsonl")
        elif FollowUpController.can_follow_up(state) and analysis.get("needs_follow_up"):
            print(f"\n💡 建议追问：{analysis.get('follow_up_question', '')}")
        else:
            print(f"\n➡️ 建议生成下一个问题")
            if not FollowUpController.can_follow_up(state):
                reason = FollowUpController.get_follow_up_limit_reason(state)
                if reason:
                    print(f"   （追问限制：{reason}）")

    elif parsed.command == 'export':
        state = InterviewState.load(parsed.state)
        if parsed.format == 'jsonl':
            output = OutputFormatter.to_jsonl(state)
            with open(parsed.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"✅ 已导出 {len(state.qa_pairs)} 条问答对至：{parsed.output}")

    elif parsed.command == 'snapshot':
        state = InterviewState.load(parsed.state)
        snapshot = OutputFormatter.to_snapshot(state)
        with open(parsed.output, 'w', encoding='utf-8') as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        print(f"✅ 状态快照已保存至：{parsed.output}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
