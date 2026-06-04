import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from interview_engine import InterviewState, PhaseController


class TestPhaseController(unittest.TestCase):

    def _create_state_with_count(self, count: int, target: int = 50) -> InterviewState:
        state = InterviewState.init("领域", "专家", target, [])
        for i in range(count):
            state.add_qa_pair({
                "q_id": i + 1,
                "phase": "warmup",
                "type": "choice",
                "dimension": "core_principles",
                "question": f"Q{i+1}",
                "answer": f"A{i+1}"
            })
        return state

    def test_warmup_phase(self):
        state = self._create_state_with_count(3, 50)  # 3/50 = 6%
        self.assertEqual(PhaseController.get_current_phase(state), "warmup")

    def test_foundation_phase(self):
        state = self._create_state_with_count(8, 50)  # 8/50 = 16%, 超过10%
        self.assertEqual(PhaseController.get_current_phase(state), "foundation")

    def test_deep_phase(self):
        state = self._create_state_with_count(25, 50)  # 25/50 = 50%, 超过40%
        self.assertEqual(PhaseController.get_current_phase(state), "deep")

    def test_advanced_phase(self):
        state = self._create_state_with_count(45, 50)  # 45/50 = 90%, 超过80%
        self.assertEqual(PhaseController.get_current_phase(state), "advanced")

    def test_should_advance_true(self):
        state = self._create_state_with_count(6, 50)  # 6/50 = 12%, warmup 应该切换到 foundation
        self.assertTrue(PhaseController.should_advance(state))

    def test_should_advance_false(self):
        state = self._create_state_with_count(3, 50)  # 3/50 = 6%, 仍在 warmup
        self.assertFalse(PhaseController.should_advance(state))

    def test_estimated_remaining(self):
        state = self._create_state_with_count(10, 50)
        # 已完成10条，还剩40条 * 1.5分钟 = 60分钟
        self.assertEqual(PhaseController.get_estimated_remaining_min(state), 60)

    def test_fast_mode_false(self):
        state = self._create_state_with_count(10, 50)
        state.progress["elapsed_min"] = 10
        self.assertFalse(PhaseController.is_fast_mode(state))

    def test_fast_mode_true(self):
        state = self._create_state_with_count(40, 50)
        # 预估75分钟，elapsed > 75 * 1.2 = 90
        state.progress["elapsed_min"] = 95
        self.assertTrue(PhaseController.is_fast_mode(state))

    def test_apply_phase_update(self):
        state = self._create_state_with_count(12, 50)  # 应该到 foundation 阶段
        PhaseController.apply_phase_update(state)
        self.assertEqual(state.progress["current_phase"], "foundation")


if __name__ == '__main__':
    unittest.main()
