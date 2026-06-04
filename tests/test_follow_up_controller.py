import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from interview_engine import InterviewState, FollowUpController


class TestFollowUpController(unittest.TestCase):

    def test_can_follow_up_default(self):
        state = InterviewState.init("领域", "专家", 50, [])
        self.assertTrue(FollowUpController.can_follow_up(state))

    def test_can_follow_up_max_depth(self):
        state = InterviewState.init("领域", "专家", 50, [])
        state.context["current_follow_up_depth"] = 2
        self.assertFalse(FollowUpController.can_follow_up(state))

    def test_can_follow_up_max_total(self):
        state = InterviewState.init("领域", "专家", 10, [])
        state.progress["follow_up_count"] = 4  # 10 * 0.3 = 3, 超过上限
        self.assertFalse(FollowUpController.can_follow_up(state))

    def test_can_follow_up_fast_mode(self):
        state = InterviewState.init("领域", "专家", 50, [])
        state.progress["fast_mode"] = True
        self.assertFalse(FollowUpController.can_follow_up(state))

    def test_get_limit_reason_depth(self):
        state = InterviewState.init("领域", "专家", 50, [])
        state.context["current_follow_up_depth"] = 2
        reason = FollowUpController.get_follow_up_limit_reason(state)
        self.assertIn("连续追问", reason)

    def test_get_limit_reason_total(self):
        state = InterviewState.init("领域", "专家", 10, [])
        state.progress["follow_up_count"] = 4
        reason = FollowUpController.get_follow_up_limit_reason(state)
        self.assertIn("总追问数", reason)

    def test_increment_follow_up(self):
        state = InterviewState.init("领域", "专家", 50, [])
        FollowUpController.increment_follow_up(state)
        self.assertEqual(state.progress["follow_up_count"], 1)
        self.assertEqual(state.context["current_follow_up_depth"], 1)

    def test_reset_follow_up_depth(self):
        state = InterviewState.init("领域", "专家", 50, [])
        state.context["current_follow_up_depth"] = 2
        FollowUpController.reset_follow_up_depth(state)
        self.assertEqual(state.context["current_follow_up_depth"], 0)


if __name__ == '__main__':
    unittest.main()
