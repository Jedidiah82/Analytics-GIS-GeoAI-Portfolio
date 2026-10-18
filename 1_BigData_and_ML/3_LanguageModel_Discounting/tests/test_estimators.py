import sys
import unittest
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import numpy as np
from estimators import mle, absolute_discount, simple_good_turing, metrics, kl_divergence
from run_experiment import batches


class ProbabilityTests(unittest.TestCase):
    def test_normalization_and_nonnegativity(self):
        for counts in [[3, 1, 1, 0, 0], [1, 1, 1, 0], [10, 0, 0], [5, 3, 2], [100, 21, 9, 4, 2, 1, 0]]:
            for estimator in [mle, absolute_discount, simple_good_turing]:
                p = estimator(counts)
                self.assertAlmostEqual(float(p.sum()), 1, places=12)
                self.assertTrue(np.all(p >= 0))

    def test_discount_transfers_mass(self):
        p = absolute_discount([3, 1, 1, 0, 0])
        np.testing.assert_allclose(p, [.45, .05, .05, .225, .225])
        self.assertFalse(np.allclose(p, mle([3, 1, 1, 0, 0])))

    def test_good_turing_reserves_singleton_mass(self):
        p = simple_good_turing([3, 1, 1, 0, 0])
        self.assertAlmostEqual(float(p[-2:].sum()), 2 / 5)
        self.assertAlmostEqual(float(p[:3].sum()), 3 / 5)

    def test_good_turing_frequency_table(self):
        # Check the log-linear/switch path against an independent per-class sum.
        counts = np.array([1] * 10 + [2] * 5 + [3] * 2 + [5] + [0] * 4)
        p = simple_good_turing(counts)
        self.assertAlmostEqual(float(p[counts == 0].sum()), 10 / counts.sum())
        self.assertEqual(len(np.unique(p[counts == 1])), 1)

    def test_metric_identities_and_infinity(self):
        q = np.array([.6, .4, 0.])
        self.assertAlmostEqual(metrics(q, q, np.array([3, 2, 0]))['js_nats'], 0)
        self.assertTrue(np.isinf(kl_divergence(np.array([.5, .5]), np.array([1., 0.]))))
        m = metrics(np.array([1., 0.]), np.array([0., 1.]), np.array([0, 1]))
        self.assertAlmostEqual(m['js_nats'], np.log(2))
        self.assertAlmostEqual(m['l1'], 2)

    def test_reject_invalid_counts(self):
        for c in [[0, 0], [-1, 2], [1.5, 2], [float('nan'), 1]]:
            with self.assertRaises(ValueError):
                mle(c)

    def test_probability_permutation_invariance(self):
        counts = np.array([1, 10, 0, 3, 1, 0, 2])
        order = np.array([6, 1, 0, 2, 5, 3, 4])
        for estimator in [mle, absolute_discount, simple_good_turing]:
            np.testing.assert_allclose(estimator(counts[order]), estimator(counts)[order])

    def test_tokenization_across_chunk_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'text8'
            # Cross both the 1MiB chunk boundary and the final unterminated token.
            content = b' a ' + b'word ' * 250_000 + b'final'
            path.write_bytes(content)
            words = [word for group in batches(path) for word in group]
            self.assertEqual(len(words), 250_002)
            self.assertEqual(words[0], b'a')
            self.assertEqual(words[-1], b'final')
            path.write_bytes(b'<mediawiki> invalid input')
            with self.assertRaises(ValueError):
                list(batches(path))


if __name__ == '__main__':
    unittest.main()
