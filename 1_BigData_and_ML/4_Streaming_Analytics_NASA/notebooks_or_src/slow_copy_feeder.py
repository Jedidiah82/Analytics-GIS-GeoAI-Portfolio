import argparse, os, shutil, time, random, glob

def dribble(src, dst, interval, pattern="*"):
    os.makedirs(dst, exist_ok=True)
    files = sorted(glob.glob(os.path.join(src, pattern)))
    if not files:
        print(f"No files found in {src}")
        return
    # Randomize order a bit so windows don’t align perfectly with file boundaries
    random.shuffle(files)

    print(f"Dribbling {len(files)} files from {src} -> {dst} every {interval}s")
    for i, f in enumerate(files, 1):
        base = os.path.basename(f)
        tmp  = os.path.join(dst, f".{base}.tmp")      # copy to temp name first
        final= os.path.join(dst, base)                # then rename atomically
        try:
            shutil.copy2(f, tmp)
            os.replace(tmp, final)
            print(f"[{i}/{len(files)}] -> {final}")
        except Exception as e:
            print(f"ERROR copying {f}: {e}")
        time.sleep(interval)
    print("Done.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--src", required=True, help="Backlog folder with input files")
    p.add_argument("--dst", required=True, help="Streaming 'stream_in' folder")
    p.add_argument("--interval", type=float, default=2.0, help="seconds between files")
    p.add_argument("--pattern", default="*", help="glob pattern, e.g. *.log or *")
    args = p.parse_args()
    dribble(args.src, args.dst, args.interval, args.pattern)
