import unittest

from app import confidence_points, select_target_difficulty, sort_questions_by_target


class QuizLogicTestCase(unittest.TestCase):
    def test_confidence_points_scoring(self):
        self.assertEqual(confidence_points(True, "low"), 1)
        self.assertEqual(confidence_points(True, "medium"), 2)
        self.assertEqual(confidence_points(True, "high"), 3)
        self.assertEqual(confidence_points(False, "low"), 0)
        self.assertEqual(confidence_points(False, "medium"), -1)
        self.assertEqual(confidence_points(False, "high"), -2)

    def test_target_difficulty_selection(self):
        self.assertEqual(select_target_difficulty(None), "medium")
        self.assertEqual(select_target_difficulty(30), "easy")
        self.assertEqual(select_target_difficulty(72), "medium")
        self.assertEqual(select_target_difficulty(92), "hard")

    def test_adaptive_sorting_is_deterministic(self):
        sample_questions = [
            {"id": 3, "difficulty": "easy"},
            {"id": 1, "difficulty": "hard"},
            {"id": 4, "difficulty": "medium"},
            {"id": 2, "difficulty": "easy"},
        ]
        ordered, priority = sort_questions_by_target(sample_questions, "medium")
        self.assertEqual(priority, ["medium", "easy", "hard"])
        self.assertEqual([q["id"] for q in ordered], [4, 2, 3, 1])


if __name__ == "__main__":
    unittest.main()
