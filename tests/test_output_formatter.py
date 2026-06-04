import unittest
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from interview_engine import InterviewState, OutputFormatter


class TestOutputFormatter(unittest.TestCase):

    def _create_sample_state(self) -> InterviewState:
        state = InterviewState.init("消费行业投资", "VC合伙人", 50, ["品牌"])
        state.add_qa_pair({
            "q_id": 1,
            "phase": "warmup",
            "type": "choice",
            "dimension": "core_principles",
            "question": "消费投资最核心的原则是什么？",
            "answer": "品牌护城河"
        })
        state.add_qa_pair({
            "q_id": 2,
            "phase": "foundation",
            "type": "open",
            "dimension": "decision_framework",
            "question": "您的分析流程？",
            "answer": "先看团队，再看市场"
        })
        return state

    def test_to_jsonl(self):
        state = self._create_sample_state()
        jsonl = OutputFormatter.to_jsonl(state)
        lines = jsonl.strip().split("\n")
        self.assertEqual(len(lines), 2)
        obj = json.loads(lines[0])
        self.assertEqual(obj["q_id"], 1)
        self.assertEqual(obj["type"], "choice")
        self.assertIn("question", obj)
        self.assertIn("answer", obj)

    def test_to_snapshot(self):
        state = self._create_sample_state()
        snapshot = OutputFormatter.to_snapshot(state)
        self.assertEqual(snapshot["completed_q_ids"], [1, 2])
        self.assertEqual(snapshot["current_phase"], "warmup")
        self.assertEqual(snapshot["remaining_target"], 48)
        self.assertIn("core_principles", snapshot["covered_topics"])

    def test_format_status(self):
        state = self._create_sample_state()
        status = OutputFormatter.format_status(state)
        self.assertIn("消费行业投资", status)
        self.assertIn("2/50", status)
        self.assertIn("warmup", status)

    def test_format_opening(self):
        state = InterviewState.init("消费行业投资", "VC合伙人", 50, ["品牌"])
        opening = OutputFormatter.format_opening(state)
        self.assertIn("消费行业投资", opening)
        self.assertIn("50", opening)
        self.assertIn("75", opening)


if __name__ == '__main__':
    unittest.main()
