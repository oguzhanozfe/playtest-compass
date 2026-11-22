import unittest
from project import analyze


def row(player, outcome, time=None, task="Dock"):
    return {"player": player, "task": task, "outcome": outcome, "active_seconds": time}


class PlaytestTests(unittest.TestCase):
    def test_independent_rate_uses_observed_players(self):
        result = analyze({"observations": [row("a", "assisted", 10), row("b", "independent", 20),
                                          row("c", "abandoned", 200), row("b", "independent", 3, "Land")]})
        self.assertEqual(result["metrics"]["Players"], 3)
        r = result["rows"][0]
        self.assertEqual((r["Independent (%)"], r["Median completion (s)"]), (33.33, 15))
        self.assertEqual(r["Median before abandoning (s)"], 200)

    def test_missing_time_preserves_outcome(self):
        r = analyze({"observations": [row("a", "independent")]})["rows"][0]
        self.assertEqual(r["Independent"], 1)
        self.assertIsNone(r["Median completion (s)"])

    def test_repeat_and_invalid_duration_fail(self):
        for obs in ([row("a", "assisted"), row("a", "independent")], [row("b", "assisted", -1)]):
            with self.subTest(obs=obs), self.assertRaises(ValueError):
                analyze({"observations": obs})

    def test_unobserved_tasks_not_imputed(self):
        self.assertEqual(analyze({"observations": []})["rows"], [])
