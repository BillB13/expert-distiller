import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from interview_engine import InterviewState, TopicTracker


class TestTopicTracker(unittest.TestCase):

    def test_get_uncovered_dimensions(self):
        state = InterviewState.init("领域", "专家", 50, [])
        uncovered = TopicTracker.get_uncovered_dimensions(state)
        self.assertEqual(len(uncovered), 5)  # 初始全部未覆盖

    def test_get_recommended_dimension(self):
        state = InterviewState.init("领域", "专家", 50, [])
        rec = TopicTracker.get_recommended_dimension(state)
        self.assertIn(rec, TopicTracker.DIMENSION_MAP.keys())

    def test_mark_covered(self):
        state = InterviewState.init("领域", "专家", 50, [])
        TopicTracker.mark_covered(state, "typical_cases", 1)
        self.assertTrue(state.coverage["dimensions"]["typical_cases"]["covered"])
        self.assertEqual(state.coverage["dimensions"]["typical_cases"]["q_ids"], [1])

    def test_uncovered_after_marking(self):
        state = InterviewState.init("领域", "专家", 50, [])
        TopicTracker.mark_covered(state, "typical_cases", 1)
        TopicTracker.mark_covered(state, "core_principles", 2)
        uncovered = TopicTracker.get_uncovered_dimensions(state)
        self.assertEqual(len(uncovered), 3)
        self.assertNotIn("typical_cases", uncovered)
        self.assertNotIn("core_principles", uncovered)

    def test_dimension_label(self):
        self.assertEqual(TopicTracker.DIMENSION_MAP["core_principles"], "核心原则")
        self.assertEqual(TopicTracker.DIMENSION_MAP["decision_framework"], "决策框架")


if __name__ == '__main__':
    unittest.main()
