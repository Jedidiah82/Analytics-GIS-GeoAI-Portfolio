"""Finite-vocabulary unigram estimators; no epsilon substitution in metrics.

SGT follows Gale & Sampson (1995), with uniform allocation of its unseen mass
over the specified unseen support. AD uses D=.75 with uniform unseen backoff.
These allocation assumptions are explicit experimental choices, not universal LMs.
"""
import numpy as np


def validate_counts(counts):
    counts = np.asarray(counts)
    if counts.ndim != 1 or not len(counts) or np.any(counts < 0):
        raise ValueError('Expected a nonnegative count vector')
    if not np.all(np.isfinite(counts)) or np.any(counts != np.floor(counts)):
        raise ValueError('Counts must be finite integers')
    if counts.sum() <= 0:
        raise ValueError('At least one token is required')
    return counts.astype(np.int64)


def validate_probability(p):
    if np.any(~np.isfinite(p)) or np.any(p < 0) or not np.isclose(p.sum(), 1, atol=1e-12):
        raise ValueError('Invalid probability distribution')
    return p


def mle(counts):
    c = validate_counts(counts)
    return validate_probability(c / c.sum())


def absolute_discount(counts, discount=.75):
    """Discount seen counts; allocate removed mass only to unseen support.

    When the finite vocabulary is fully observed, return MLE: no unseen support
    remains to receive the discount. No vocabulary is inferred from test counts.
    """
    c = validate_counts(counts)
    if not 0 < discount < 1:
        raise ValueError('discount must lie strictly between zero and one')
    seen = c > 0
    if seen.all():
        return mle(c)
    p = np.zeros(len(c))
    p[seen] = (c[seen] - discount) / c.sum()
    p[~seen] = discount * seen.sum() / c.sum() / (~seen).sum()
    return validate_probability(p)


def simple_good_turing(counts):
    """Log-linear frequency-of-frequency smoothing and 1.96-SD switch.

    Seen estimates are normalized to 1-N1/N; N1/N is allocated uniformly among
    unseen categories. Degenerate one-frequency inputs use proportional seen
    weights. Fully observed support receives no reserved unseen mass.
    """
    c = validate_counts(counts)
    seen = c > 0
    r, nr = np.unique(c[seen], return_counts=True)
    r = r.astype(float)
    nr = nr.astype(float)
    n = c.sum()
    p0 = float(nr[0] / n) if r[0] == 1 and not seen.all() else 0.
    if len(r) < 2:
        adjusted = r.copy()
    else:
        lower = np.r_[0., r[:-1]]
        upper = np.r_[r[1:], 2 * r[-1] - r[-2]]
        z = 2 * nr / (upper - lower)
        slope, _ = np.polyfit(np.log(r), np.log(z), 1)
        nr_lookup = dict(zip(r, nr))
        adjusted = []
        use_smooth = False
        for frequency, number in zip(r, nr):
            smoothed = (frequency + 1) * ((frequency + 1) / frequency) ** slope
            next_number = nr_lookup.get(frequency + 1)
            if next_number is None:
                use_smooth = True
            if not use_smooth:
                empirical = (frequency + 1) * next_number / number
                sd = (frequency + 1) * np.sqrt(next_number / number**2 * (1 + next_number / number))
                if abs(empirical - smoothed) <= 1.96 * sd:
                    use_smooth = True
            adjusted.append(smoothed if use_smooth else empirical)
        adjusted = np.asarray(adjusted)
    p = np.zeros(len(c))
    weights = adjusted[np.searchsorted(r, c[seen])]
    p[seen] = (1 - p0) * weights / weights.sum()
    if not seen.all():
        p[~seen] = p0 / (~seen).sum()
    return validate_probability(p)


def kl_divergence(reference, estimate):
    active = reference > 0
    if np.any(estimate[active] == 0):
        return float('inf')
    return float(np.sum(reference[active] * np.log(reference[active] / estimate[active])))


def metrics(reference, estimate, counts):
    reference = validate_probability(np.asarray(reference, dtype=float))
    estimate = validate_probability(np.asarray(estimate, dtype=float))
    midpoint = (reference + estimate) / 2
    unseen = counts == 0
    q_unseen = float(reference[unseen].sum())
    p_unseen = float(estimate[unseen].sum())
    return {
        'l1': float(np.abs(reference - estimate).sum()),
        'js_nats': .5 * (kl_divergence(reference, midpoint) + kl_divergence(estimate, midpoint)),
        'kl_reference_to_estimate_nats': kl_divergence(reference, estimate),
        'unseen_reference_mass': q_unseen,
        'unseen_estimated_mass': p_unseen,
        'unseen_mass_absolute_error': abs(q_unseen - p_unseen),
        'probability_sum': float(estimate.sum()),
    }
