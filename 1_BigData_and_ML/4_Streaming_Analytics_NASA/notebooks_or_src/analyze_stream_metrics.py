import json, argparse
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

def load_progress_jsonl(path: Path) -> pd.DataFrame:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                j = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Defensive extraction (Spark progress schema is stable but nested)
            b = j.get("batchId")
            ts = j.get("timestamp")  # string ISO time
            num_in = j.get("numInputRows")
            inp_rps = j.get("inputRowsPerSecond")
            proc_rps = j.get("processedRowsPerSecond")

            # durations (ms) live under "durationMs" dict
            dur = j.get("durationMs") or {}
            add_batch = dur.get("addBatch")
            get_offsets = dur.get("getOffset")
            trigger = dur.get("triggerExecution")
            wal = dur.get("walCommit")

            # eventTime (if your query has event-time)
            ev = j.get("eventTime") or {}
            ev_max = ev.get("max")
            ev_min = ev.get("min")
            ev_avg = ev.get("avg")
            ev_watermark = ev.get("watermark")

            # state ops (optional; present for stateful queries)
            state_rows = None
            for op in j.get("stateOperators", []):
                # first operator’s numRowsTotal might be useful
                if isinstance(op, dict) and "numRowsTotal" in op:
                    state_rows = op["numRowsTotal"]
                    break

            rows.append(dict(
                batchId=b, timestamp=ts, numInputRows=num_in,
                inputRowsPerSecond=inp_rps, processedRowsPerSecond=proc_rps,
                dur_addBatch_ms=add_batch, dur_getOffset_ms=get_offsets,
                dur_trigger_ms=trigger, dur_walCommit_ms=wal,
                eventTime_max=ev_max, eventTime_min=ev_min,
                eventTime_avg=ev_avg, eventTime_watermark=ev_watermark,
                stateRowsTotal=state_rows
            ))
    df = pd.DataFrame(rows).sort_values("batchId").reset_index(drop=True)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df

def save_csv(df: pd.DataFrame, out_csv: Path):
    df.to_csv(out_csv, index=False)
    print(f"[saved] {out_csv}")

def make_plots(df: pd.DataFrame, out_dir: Path, prefix: str):
    out_dir.mkdir(parents=True, exist_ok=True)

    def _plot(series, title, ylabel, fname):
        plt.figure()
        plt.plot(df["batchId"], series)
        plt.title(title)
        plt.xlabel("batchId")
        plt.ylabel(ylabel)
        plt.tight_layout()
        p = out_dir / f"{prefix}_{fname}.png"
        plt.savefig(p, dpi=140)
        plt.close()
        print(f"[plot] {p}")

    if "inputRowsPerSecond" in df:
        _plot(df["inputRowsPerSecond"], "Input Rows / sec", "rows/sec", "input_rps")
    if "processedRowsPerSecond" in df:
        _plot(df["processedRowsPerSecond"], "Processed Rows / sec", "rows/sec", "processed_rps")
    if "dur_trigger_ms" in df:
        _plot(df["dur_trigger_ms"], "Trigger Duration", "ms", "trigger_ms")
    if "numInputRows" in df:
        _plot(df["numInputRows"], "Input Rows per Batch", "rows", "input_rows")

    # rolling averages (helps smooth spikes)
    if "processedRowsPerSecond" in df:
        roll = df["processedRowsPerSecond"].rolling(10, min_periods=3).mean()
        _plot(roll, "Processed Rows / sec (rolling mean, w=10)", "rows/sec", "processed_rps_roll10")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", required=True, help="Path to Spark progress JSONL")
    ap.add_argument("--name", required=True, help="Short name for outputs, e.g. socket or nasa")
    ap.add_argument("--outdir", default="C:/temp/spark/analysis", help="Where to save CSV/plots")
    args = ap.parse_args()

    path = Path(args.jsonl)
    outdir = Path(args.outdir)
    out_csv = outdir / f"{args.name}_metrics.csv"

    df = load_progress_jsonl(path)
    if df.empty:
        print(f"[warn] No rows parsed from {path}")
        return

    # basic derived metrics
    if {"numInputRows", "dur_trigger_ms"}.issubset(df.columns):
        # throughput per batch (rows/ms -> rows/sec)
        df["batch_throughput_rows_per_sec"] = (
            df["numInputRows"] / df["dur_trigger_ms"].astype(float) * 1000.0
        )

    save_csv(df, out_csv)
    make_plots(df, outdir, args.name)

if __name__ == "__main__":
    main()
