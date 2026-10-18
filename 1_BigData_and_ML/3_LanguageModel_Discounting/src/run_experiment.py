"""Reproducible unigram study on a local canonical Text8 file (not redistributed).

python src/run_experiment.py --corpus /path/to/text8 --output . --cache /tmp/lm-cache
"""
import argparse
import csv
import hashlib
import json
import platform
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from estimators import mle, absolute_discount, simple_good_turing, metrics

SIZES = [1_000, 10_000, 100_000, 1_000_000]
SEEDS = [17, 29, 43, 71, 101]
METHODS = {'MLE': mle, 'Simple Good–Turing': simple_good_turing, 'Absolute discounting': absolute_discount}


def batches(path):
    """Whitespace tokens with chunk-boundary carry; validate canonical Text8."""
    carry = b''
    with Path(path).open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            parts = (carry + chunk).split()
            carry = parts.pop() if parts else b''
            if any(not word.isalpha() or word.lower() != word for word in parts):
                raise ValueError('Expected lowercase alphabetic Text8 tokens')
            yield parts
    if carry:
        if not carry.isalpha() or carry.lower() != carry:
            raise ValueError('Invalid last token')
        yield [carry]


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as f:
        while chunk := f.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(corpus, cache):
    cache.mkdir(parents=True, exist_ok=True)
    digest = file_hash(corpus)
    if digest != '6e890197040d37d85beb962ae1f041ff1d9a9ca8d20c7d99c85027eebf51dca7':
        raise ValueError('Corpus checksum does not match canonical Text8; use fetch_corpus.py')
    manifest_path = cache / 'corpus.json'
    if manifest_path.exists():
        meta = json.loads(manifest_path.read_text())
        if meta['source_sha256'] == digest:
            meta.update(source_url='https://mattmahoney.net/dc/textdata.html', source_md5='3bea1919949baf155f99411df5fada7e')
            return np.load(cache / 'train_ids.npy', mmap_mode='r'), np.load(cache / 'reference_counts.npy'), meta
    total = sum(len(words) for words in batches(corpus))
    split = int(total * .8)
    train, test = Counter(), Counter()
    position = 0
    for words in batches(corpus):
        boundary = max(0, min(len(words), split - position))
        train.update(words[:boundary])
        test.update(words[boundary:])
        position += len(words)
    # Frequency order based on training pool only; deterministic lexical tie break.
    vocabulary = sorted(train, key=lambda w: (-train[w], w))
    ids = {word: i + 1 for i, word in enumerate(vocabulary)}
    pool = np.lib.format.open_memmap(cache / 'train_ids.npy', mode='w+', dtype='int32', shape=(split,))
    position = 0
    for words in batches(corpus):
        take = min(len(words), split - position)
        if take <= 0:
            break
        pool[position:position + take] = [ids[word] for word in words[:take]]
        position += take
    pool.flush()
    reference = np.zeros(len(vocabulary) + 1, dtype=np.int64)
    for word, count in test.items():
        reference[ids.get(word, 0)] += count
    np.save(cache / 'reference_counts.npy', reference)
    meta = {
        'source_name': 'text8', 'source_url': 'https://mattmahoney.net/dc/textdata.html',
        'source_md5': '3bea1919949baf155f99411df5fada7e', 'source_bytes': Path(corpus).stat().st_size,
        'source_sha256': digest, 'total_tokens': total,
        'training_pool_tokens': split, 'heldout_tokens': int(reference.sum()),
        'training_types': len(vocabulary), 'split': 'first 80% train; last 20% held-out reference',
        'tokenization': 'lowercase alphabetic whitespace tokens; validated input',
        'vocabulary': 'training-pool-only frequency order; lexical tie break; index 0 is UNK',
    }
    manifest_path.write_text(json.dumps(meta, indent=2))
    return pool, reference, meta


def write_csv(path, rows):
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(corpus, output, cache):
    output = Path(output)
    result_dir = output / 'results'
    result_dir.mkdir(parents=True, exist_ok=True)
    pool, reference_counts, meta = prepare(corpus, Path(cache))
    if len(pool) < max(SIZES):
        raise ValueError('Training pool must support all requested sample sizes')
    rows, sample_rows = [], []
    modes = {'50k + UNK': min(50_000, len(reference_counts) - 1), 'Full training vocabulary + UNK': len(reference_counts) - 1}
    for seed in SEEDS:
        # The prefixes form nested samples for one seed, sampled without replacement.
        rng = np.random.default_rng(seed)
        positions = rng.choice(len(pool), size=max(SIZES), replace=False)
        tokens = np.asarray(pool[positions])
        for n in SIZES:
            sample = tokens[:n]
            sample_rows.append({'seed': seed, 'requested_tokens': n, 'actual_tokens': len(sample),
                                'sample_id_sha256': hashlib.sha256(sample.astype('<i4').tobytes()).hexdigest()})
            for mode, k in modes.items():
                mapped = np.where(sample <= k, sample, 0)
                counts = np.bincount(mapped, minlength=k + 1)
                reference = reference_counts[:k + 1].copy()
                reference[0] += reference_counts[k + 1:].sum()
                q = reference / reference.sum()
                assert counts.sum() == n and len(mapped) == n
                for method, estimator in METHODS.items():
                    p = estimator(counts)
                    values = metrics(q, p, counts)
                    assert 0 <= values['js_nats'] <= np.log(2) + 1e-12
                    assert 0 <= values['l1'] <= 2 + 1e-12
                    rows.append({'seed': seed, 'sample_tokens': n, 'support': mode, 'support_categories': k + 1,
                                 'estimator': method, **values})
                    if seed == SEEDS[0] and n == max(SIZES) and k == modes['Full training vocabulary + UNK']:
                        np.save(result_dir / ('example_' + {'MLE':'mle','Simple Good–Turing':'sgt','Absolute discounting':'ad'}[method] + '.npy'), p)
                        np.save(result_dir / 'example_reference.npy', q)
        print(f'Completed seed {seed}', flush=True)
    assert len({r['sample_id_sha256'] for r in sample_rows}) == len(sample_rows)
    write_csv(result_dir / 'runs.csv', rows)
    write_csv(result_dir / 'samples.csv', sample_rows)
    summary = []
    for mode in modes:
        for n in SIZES:
            for method in METHODS:
                group = [r for r in rows if r['support'] == mode and r['sample_tokens'] == n and r['estimator'] == method]
                result = {'support': mode, 'sample_tokens': n, 'estimator': method, 'repeats': len(group)}
                for key in ['l1', 'js_nats', 'unseen_mass_absolute_error', 'unseen_reference_mass', 'unseen_estimated_mass']:
                    values = [r[key] for r in group]
                    result[key + '_mean'] = float(np.mean(values))
                    result[key + '_sd'] = float(np.std(values, ddof=1))
                result['infinite_kl_runs'] = sum(np.isinf(r['kl_reference_to_estimate_nats']) for r in group)
                summary.append(result)
    write_csv(result_dir / 'summary.csv', summary)
    manifest = {**meta, 'run_date_utc': datetime.now(timezone.utc).isoformat(), 'sizes': SIZES, 'seeds': SEEDS,
                'sampling': 'nested random samples without replacement within seed; seed draws may overlap',
                'supports': modes, 'model_runs': len(rows), 'sample_draws': len(sample_rows),
                'metric_orientation': 'KL(reference || estimate); L1 and JS on identical normalized finite support',
                'zero_probability_policy': 'KL is infinity for unsupported reference events; no epsilon clipping',
                'unseen_allocation': 'uniform across unseen finite-support categories, including UNK',
                'uncertainty': 'sample SD over five draws; not confidence intervals or corpus-generalization uncertainty',
                'python': platform.python_version(), 'numpy': np.__version__}
    manifest['code_sha256'] = {p.name: file_hash(p) for p in Path(__file__).parent.glob('*.py')}
    (result_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    return summary


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--corpus', required=True)
    ap.add_argument('--output', default='.')
    ap.add_argument('--cache', default='.cache')
    args = ap.parse_args()
    run(args.corpus, args.output, args.cache)
