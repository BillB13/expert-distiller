import unittest
import json
import tempfile
import os
from pathlib import Path

# 导入被测模块（需要在项目根目录运行）
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from interview_engine import InterviewState


class TestInterviewState(unittest.TestCase):

    def test_init_creates_default_state(self):
        state = InterviewState.init(
            domain="消费行业投资",
            expert_position="VC合伙人",
            target_count=50,
            focus_keywords=["消费品", "品牌"]
        )
        self.assertEqual(state.meta["domain"], "消费行业投资")
        self.assertEqual(state.meta["target_count"], 50)
        self.assertEqual(state.progress["current_phase"], "warmup")
        self.assertEqual(state.progress["completed_count"], 0)
        self.assertEqual(len(state.qa_pairs), 0)

    def test_estimated_duration(self):
        state = InterviewState.init(
            domain="消费行业投资",
            expert_position="VC合伙人",
            target_count=50,
            focus_keywords=[]
        )
        # 50条 * 平均1.5分钟 = 75分钟
        self.assertEqual(state.meta["estimated_duration_min"], 75)

    def test_add_qa_pair(self):
        state = InterviewState.init("领域", "专家", 10, [])
        state.add_qa_pair({
            "q_id": 1,
            "phase": "warmup",
            "type": "choice",
            "dimension": "core_principles",
            "question": "测试问题",
            "answer": "测试回答"
        })
        self.assertEqual(state.progress["completed_count"], 1)
        self.assertEqual(len(state.qa_pairs), 1)

    def test_save_and_load(self):
        state = InterviewState.init("领域", "专家", 10, ["关键词"])
        state.add_qa_pair({"q_id": 1, "phase": "warmup", "type": "choice",
                          "dimension": "core_principles", "question": "Q", "answer": "A"})

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            state.save(temp_path)
            loaded = InterviewState.load(temp_path)
            self.assertEqual(loaded.meta["domain"], "领域")
            self.assertEqual(len(loaded.qa_pairs), 1)
            self.assertEqual(loaded.progress["completed_count"], 1)
        finally:
            os.unlink(temp_path)

    def test_update_coverage(self):
        state = InterviewState.init("领域", "专家", 10, [])
        state.update_coverage("typical_cases", 1)
        self.assertTrue(state.coverage["dimensions"]["typical_cases"]["covered"])
        self.assertEqual(state.coverage["dimensions"]["typical_cases"]["q_ids"], [1])

    def test_to_prompt_context(self):
        state = InterviewState.init("消费行业", "专家", 50, ["品牌"])
        state.add_qa_pair({"q_id": 1, "phase": "warmup", "type": "choice",
                          "dimension": "typical_cases", "question": "Q1", "answer": "A1"})
        context = state.to_prompt_context()
        self.assertIn("消费行业", context)
        self.assertIn("warmup", context)
        self.assertIn("1/50", context)

    def test_add_qa_pair_does_not_mutate_input(self):
        state = InterviewState.init("领域", "专家", 10, [])
        qa = {"q_id": 1, "phase": "warmup", "type": "choice",
              "dimension": "core_principles", "question": "Q", "answer": "A"}
        state.add_qa_pair(qa)
        self.assertNotIn("timestamp", qa)

    def test_update_coverage_unknown_dimension_raises(self):
        state = InterviewState.init("领域", "专家", 10, [])
        with self.assertRaises(ValueError):
            state.update_coverage("nonexistent_dimension", 1)

    def test_init_zero_target_count(self):
        state = InterviewState.init("领域", "专家", 0, [])
        self.assertEqual(state.meta["estimated_duration_min"], 0)


if __name__ == '__main__':
    unittest.main()
