import os, sys, json
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.streaming import StreamingQueryListener
from pyspark.sql.functions import regexp_extract, col, window, to_timestamp

# --- paths (edit only these if you like) ---
STREAM_DIR    = r"file:///C:/temp/nasa_stream/stream_in"
CHECKPOINT    = r"file:///C:/temp/spark/checkpoints/nasa_metrics"   # NEW path so we don't reuse old state
METRICS_FILE  = r"C:/temp/spark/query_metrics_nasa.jsonl"

# Ensure dirs exist
Path("C:/temp/spark/checkpoints").mkdir(parents=True, exist_ok=True)
Path("C:/temp/nasa_stream/stream_in".replace("file:///", "")).mkdir(parents=True, exist_ok=True)
Path(METRICS_FILE).parent.mkdir(parents=True, exist_ok=True)

# Make sure Spark uses this Python
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

def get_spark():
    return (
        SparkSession.builder
        .appName("NASA-Logs-Stream")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.local.dir", "C:/temp/spark")
        # keep Hadoop in pure-Java mode (safe even if hadoop.dll present)
        .config("spark.hadoop.io.native.lib.available", "false")
        .config("spark.driver.extraJavaOptions", "-Dhadoop.native.lib=false")
        .config("spark.executor.extraJavaOptions", "-Dhadoop.native.lib=false")
        .getOrCreate()
    )

class FileLogger(StreamingQueryListener):
    def __init__(self, logfile=METRICS_FILE):
        self.logfile = logfile
        # clear/create file safely
        with open(self.logfile, "w", encoding="utf-8") as f:
            f.write("")
    def onQueryStarted(self, event):
        print(f"[metrics] started: {event.id}")
    def onQueryTerminated(self, event):
        print(f"[metrics] terminated: {event.id}")
    def onQueryProgress(self, event):
        try:
            with open(self.logfile, "a", encoding="utf-8") as f:
                # FIXED: json is a STRING attribute in your PySpark version
                f.write(event.progress.json + "\n")
        except Exception as e:
            # don't kill the stream if logging fails for any reason
            print(f"[metrics] write failed: {e}")

# Build Spark + attach listener BEFORE starting query
spark = get_spark()
spark.streams.addListener(FileLogger(METRICS_FILE))

# sanity
hc = spark.sparkContext._jsc.hadoopConfiguration()
hc.set("io.native.lib.available", "false")
print("io.native.lib.available =", hc.get("io.native.lib.available"))
print("🔎 Stream dir:", STREAM_DIR)

# ---- Stream from files (one file per trigger)
lines = (
    spark.readStream
    .format("text")
    .option("maxFilesPerTrigger", 1)
    .load(STREAM_DIR)
)

# Parse NASA Log
raw = lines.select(
    regexp_extract("value", r'^(\S+)', 1).alias("host"),
    regexp_extract("value", r'\[(.*?)\]', 1).alias("timestamp_str"),
    regexp_extract("value", r'\"(\S+)\s+(\S+)\s*(\S*)\"', 2).alias("path"),
    regexp_extract("value", r'\" (\d{3}) ', 1).alias("status"),
    regexp_extract("value", r' (\d+)$', 1).alias("size")
)

logs = raw.withColumn(
    "ts", to_timestamp(col("timestamp_str"), "dd/MMM/yyyy:HH:mm:ss Z")
).dropna(subset=["ts"])

counts = (
    logs
    .withWatermark("ts", "2 minutes")
    .groupBy(window(col("ts"), "1 minute"), col("status"))
    .count()
    .orderBy(col("window").asc(), col("status").asc())
)

query = (
    counts.writeStream
    .outputMode("complete")
    .format("console")
    .option("truncate", "false")
    .option("checkpointLocation", CHECKPOINT)   # NEW checkpoint folder
    .start()
)

query.awaitTermination()
