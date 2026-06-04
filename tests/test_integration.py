import unittest
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from interview_engine import InterviewState, PhaseController, TopicTracker
from interview_engine import FollowUpController, OutputFormatter


class TestIntegration(unittest.TestCase):
    """集成测试 - 模拟完整访谈流程"""

    def test_full_interview_flow(self):
        """模拟 5 个问题的完整流程"""
        # 1. 初始化
        state = InterviewState.init(
            domain="消费行业投资",
            expert_position="VC合伙人",
            target_count=10,
            focus_keywords=["品牌", "渠道"]
        )
        self.assertEqual(state.progress["current_phase"], "warmup")

        # 2. 模拟 5 轮问答
        questions = [
            {"q_id": 1, "type": "choice", "dimension": "core_principles",
             "phase": "warmup", "question": "品牌重要还是渠道重要？", "answer": "品牌"},
            {"q_id": 2, "type": "judge", "dimension": "core_principles",
             "phase": "foundation", "question": "消费品必须有品牌护城河吗？", "answer": "是的"},
            {"q_id": 3, "type": "open", "dimension": "decision_framework",
             "phase": "foundation", "question": "您怎么评估一个消费项目？", "answer": "看团队、看市场、看模式"},
            {"q_id": 4, "type": "case", "dimension": "typical_cases",
             "phase": "deep", "question": "分享一个成功案例", "answer": "我们投的XX品牌..."},
            {"q_id": 5, "type": "open", "dimension": "typical_cases",
             "phase": "deep", "question": "具体怎么判断的？", "answer": "看ROE和复购率"},
        ]

        for q in questions:
            state.add_qa_pair(q)
            TopicTracker.mark_covered(state, q["dimension"], q["q_id"])

        # 3. 验证阶段推进
        PhaseController.apply_phase_update(state)
        # 5/10 = 50%, warmup(10%) + foundation(30%) = 40%, 50% > 40% 所以进入 deep
        self.assertEqual(state.progress["current_phase"], "deep")

        # 4. 验证话题覆盖
        self.assertTrue(state.coverage["dimensions"]["core_principles"]["covered"])
        self.assertTrue(state.coverage["dimensions"]["decision_framework"]["covered"])
        self.assertTrue(state.coverage["dimensions"]["typical_cases"]["covered"])

        # 5. 验证输出
        jsonl = OutputFormatter.to_jsonl(state)
        lines = jsonl.strip().split("\n")
        self.assertEqual(len(lines), 5)

        snapshot = OutputFormatter.to_snapshot(state)
        self.assertEqual(snapshot["remaining_target"], 5)

    def test_follow_up_scenario(self):
        """测试追问场景"""
        state = InterviewState.init("领域", "专家", 10, [])

        # 第一轮：不需要追问
        self.assertTrue(FollowUpController.can_follow_up(state))

        # 模拟追问2次
        state.context["current_follow_up_depth"] = 2
        self.assertFalse(FollowUpController.can_follow_up(state))

        # 换话题后重置
        FollowUpController.reset_follow_up_depth(state)
        self.assertTrue(FollowUpController.can_follow_up(state))

    def test_fast_mode_scenario(self):
        """测试超时进入快速模式"""
        state = InterviewState.init("领域", "专家", 10, [])
        # 预估15分钟，超过18分钟进入快速模式
        state.progress["elapsed_min"] = 20
        self.assertTrue(PhaseController.is_fast_mode(state))
        # 设置 fast_mode 标志后，追问应该被禁止
        state.progress["fast_mode"] = True
        self.assertFalse(FollowUpController.can_follow_up(state))


if __name__ == '__main__':
    unittest.main()
