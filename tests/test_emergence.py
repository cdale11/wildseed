import unittest

from wildseed.emergence import compare, evaluate, network_shift


class EmergenceTests(unittest.TestCase):
    def test_window_shift_uses_event_shares_and_handles_empty_windows(self):
        self.assertEqual(network_shift({'a>b': 2}, {'a>b': 4}), 0)
        self.assertEqual(network_shift({'a>b': 2}, {'b>c': 5}), 1)
        self.assertIsNone(network_shift({}, {'a>b': 1}))

    def test_comparison_keeps_novelty_as_unverified_observation(self):
        control = {'seed': 1, 'final_population': 2, 'novelty_count': 1,
                   'novelty_records': [{'kind': 'grazer', 'signature': [1, 0]}]}
        learned = {'seed': 1, 'final_population': 3, 'novelty_count': 1,
                   'novelty_records': [{'tick': 100, 'kind': 'grazer',
                                        'signature': [0, 1]}]}
        result = compare(control, learned)
        self.assertEqual(result['candidate_behaviors'][0]['control_distance'], 1)
        self.assertEqual(result['candidate_behaviors'][0]['status'], 'unverified_observation')
        with self.assertRaises(ValueError):
            compare(control, dict(learned, seed=2))

    def test_matched_runs_are_deterministic_and_initially_equal(self):
        control = evaluate(63, 20, 10, 12, 16, 16, 60, False)
        learned = evaluate(63, 20, 10, 12, 16, 16, 60, True)
        self.assertEqual(control, evaluate(63, 20, 10, 12, 16, 16, 60, False))
        self.assertEqual(len(control['windows']), 2)
        self.assertEqual(control['windows'][0]['end_tick'], 10)
        self.assertEqual(control['windows'][-1]['end_tick'], 20)
        self.assertEqual(compare(control, learned)['seed'], 63)


if __name__ == '__main__':
    unittest.main()
