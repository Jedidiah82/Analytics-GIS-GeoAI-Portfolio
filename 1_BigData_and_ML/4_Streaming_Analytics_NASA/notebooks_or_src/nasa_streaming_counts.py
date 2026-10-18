import os, sys, json
from pyspark.sql import SparkSession
from pyspark.sql.functions import regexp_extract, col, window, to_timestamp
from pyspark.sql.streaming import StreamingQueryListener

# --- paths/config you can tweak ---
STREAM_DIR   = "file:///C:/temp/nasa_stream/stream_in"
CHK_ROOT     = "file:///C:/temp/spark/checkpoints"
CHK_CONSOLE  = f"{CHK_ROOT}/nasa_console"
CHK_FOREACH  = f"{CHK_ROOT}/nasa_foreach"
PARQUET_OUT  = "file:///C:/temp/spark/out/nasa_counts"
METRICS_FILE = "C:/temp/spark/query_metrics_nasa.jsonl"

# make sure pyspark uses this Python
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

# --- listener to log metrics ---
class FileLogger(StreamingQueryListener):
    def __init__(self, logfile=METRICS_FILE):
        self.logfile = logfile
        with open(self.logfile, "w") as f:
            f.write("")

    def onQueryProgress(self, event):
        with open(self.logfile, "a") as f:
            f.write(json.dumps(event.progress.jsonValue()) + "\n")

    def onQueryStarted(self, event):
        print(f"[metrics] started: {event.id}")

    def onQueryTerminated(self, event):
        print(f"[metrics] terminated: {event.id}")

# Spark session
spark = (
    SparkSession.builder
    .appName("NASA-Logs-Stream")
    .config("spark.sql.shuffle.partitions", "4")
    .config("spark.local.dir", "C:/temp/spark")
    .config("spark.hadoop.io.native.lib.available", "false")
    .config("spark.driver.extraJavaOptions", "-Dhadoop.native.lib=false")
    .config("spark.executor.extraJavaOptions", "-Dhadoop.native.lib=false")
    .getOrCreate()
)

# attach listener
spark.streams.addListener(FileLogger(METRICS_FILE))

# sanity check
hc = spark.sparkContext._jsc.hadoopConfiguration()
hc.set("io.native.lib.available", "false")
print("io.native.lib.available =", hc.get("io.native.lib.available"))
print("🔎 Streaming from:", STREAM_DIR)

# ===== source =====
lines = (
    spark.readStream
    .format("text")
    .option("maxFilesPerTrigger", 1)
    .option("pathGlobFilter", "*.log")
    .load(STREAM_DIR)
)

# ===== parse NASA log lines =====
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
    .count()  # -> [window(struct<start,end>), status, count]
)

# ===== sink 1: console =====
query_console = (
    counts.writeStream
    .outputMode("update")
    .format("console")
    .option("truncate", "false")
    .option("checkpointLocation", CHK_CONSOLE)
    .start()
)

# ===== sink 2: parquet via foreachBatch (for later analysis) =====
def save_batch(df, batch_id: int):
    (
        df
        .withColumn("window_start", col("window").start)
        .withColumn("window_end",   col("window").end)
        .drop("window")
        .withColumnRenamed("count", "requests")
        .coalesce(1)  # convenience for small demo
        .write
        .mode("append")              # compatible with watermark
        .partitionBy("status")
        .parquet(PARQUET_OUT)
    )

query_parquet = (
    counts.writeStream
    .outputMode("append")
    .foreachBatch(save_batch)
    .option("checkpointLocation", CHK_FOREACH)
    .start()
)

query_console.awaitTermination()
query_parquet.awaitTermination()
