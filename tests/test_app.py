"""실행: py -m unittest discover tests  (data/lotto.db를 읽기 전용으로 사용)"""

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

from lotto.check import rank_of
from lotto.generate import (
    VALID_RULES,
    Constraints,
    GenerationError,
    generate_combination,
    load_snapshot,
    snapshot_from_draws,
)
from lotto.web import app


class RankTest(unittest.TestCase):
    WIN = {1, 2, 3, 4, 5, 6}
    BONUS = 7

    def test_ranks(self):
        self.assertEqual(rank_of([1, 2, 3, 4, 5, 6], self.WIN, self.BONUS), 1)
        self.assertEqual(rank_of([1, 2, 3, 4, 5, 7], self.WIN, self.BONUS), 2)
        self.assertEqual(rank_of([1, 2, 3, 4, 5, 8], self.WIN, self.BONUS), 3)
        self.assertEqual(rank_of([1, 2, 3, 4, 7, 8], self.WIN, self.BONUS), 4)
        self.assertEqual(rank_of([1, 2, 3, 7, 8, 9], self.WIN, self.BONUS), 5)
        self.assertIsNone(rank_of([1, 2, 7, 8, 9, 10], self.WIN, self.BONUS))


class GenerateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = load_snapshot()

    def test_every_rule_returns_six_unique_numbers(self):
        rng = random.Random(0)
        for rule in VALID_RULES:
            numbers = generate_combination(rule, self.snapshot, rng=rng)["numbers"]
            self.assertEqual(len(set(numbers)), 6, rule)
            self.assertTrue(all(1 <= n <= 45 for n in numbers), rule)

    def test_constraints_are_respected(self):
        rng = random.Random(1)
        c = Constraints(include={7, 13}, exclude={1, 2, 3, 40}, odd_count=3, sum_min=100, sum_max=160)
        c.validate()
        for rule in VALID_RULES:
            for _ in range(5):
                numbers = generate_combination(rule, self.snapshot, c, rng)["numbers"]
                self.assertTrue({7, 13} <= set(numbers), rule)
                self.assertFalse({1, 2, 3, 40} & set(numbers), rule)
                self.assertEqual(sum(n % 2 for n in numbers), 3, rule)
                self.assertTrue(100 <= sum(numbers) <= 160, rule)

    def test_invalid_constraints(self):
        with self.assertRaises(GenerationError):
            Constraints(include={5}, exclude={5}).validate()
        with self.assertRaises(GenerationError):
            Constraints(include={1, 3, 5}, odd_count=2).validate()
        with self.assertRaises(GenerationError):
            Constraints(include={1, 2, 3, 4, 5, 6}).validate()

    def test_snapshot_uses_only_given_draws(self):
        draws = [[1, 2, 3, 4, 5, 6]] * 3 + [[40, 41, 42, 43, 44, 45]]
        snap = snapshot_from_draws(draws, window=1)
        self.assertEqual({r["number"] for r in snap.alltime[:6]}, {1, 2, 3, 4, 5, 6})
        self.assertEqual({r["number"] for r in snap.recent[:6]}, {40, 41, 42, 43, 44, 45})
        self.assertEqual(snap.prev_draw, {40, 41, 42, 43, 44, 45})


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_index_and_static(self):
        self.assertIn("로또 번호 생성기", self.client.get("/").text)
        self.assertEqual(self.client.get("/static/app.js").status_code, 200)

    def test_generate_with_constraints(self):
        res = self.client.get("/api/generate?rule=fixed&count=3&include=10&exclude=20,21&odd=3")
        self.assertEqual(res.status_code, 200)
        for combo in res.json()["combinations"]:
            self.assertIn(10, combo["numbers"])

    def test_generate_rejects_bad_constraints(self):
        self.assertEqual(self.client.get("/api/generate?include=5&exclude=5").status_code, 422)
        self.assertEqual(self.client.get("/api/generate?include=a").status_code, 400)

    def test_check_latest(self):
        latest = self.client.get("/api/draws/latest").json()
        res = self.client.post("/api/check", json={"tickets": [latest["numbers"]]})
        self.assertEqual(res.json()["results"][0]["rank"], 1)
        bad = self.client.post("/api/check", json={"tickets": [[1, 1, 2, 3, 4, 5]]})
        self.assertEqual(bad.status_code, 400)

    def test_stats(self):
        data = self.client.get("/api/stats?window=100").json()
        self.assertEqual(data["total_draws"], 100)
        self.assertEqual(sum(n["count"] for n in data["numbers"]), 600)
        self.assertEqual(sum(o["count"] for o in data["odd_even"]), 100)
        self.assertEqual(sum(s["count"] for s in data["sums"]), 100)

    def test_backtest(self):
        data = self.client.get("/api/backtest?rounds=10&tickets=2&seed=3").json()
        self.assertEqual(len(data["results"]), len(VALID_RULES) + 1)
        for r in data["results"]:
            self.assertEqual(r["tickets"], 20)


if __name__ == "__main__":
    unittest.main()
