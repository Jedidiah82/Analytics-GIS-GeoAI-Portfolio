import os, sys
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import RegexTokenizer, StopWordsRemover, HashingTF, IDF
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator

DATA_PATH = "data/20newsgroups/20ng.csv"

def run_kmeans(k=20):
    spark = (SparkSession.builder
             .appName(f"CN7030-Clustering-k{k}")
             .config("spark.sql.shuffle.partitions", "8")
             .config("spark.driver.memory", "16g")          # more heap for the driver
             .config("spark.kryoserializer.buffer", "64m")
             .config("spark.kryoserializer.buffer.max", "512m")
             .getOrCreate())

    # If you still see Windows temp-dir cleanup warnings, you can set this in PowerShell:
    #   $env:SPARK_LOCAL_DIRS = "C:\temp\spark"
    # and create that folder once.

    # Load data
    df = (spark.read.csv(DATA_PATH, header=True)
          .select("text", "label")
          .na.drop())

    # Pipeline: tokenize → stopwords → TF → IDF → KMeans
    tok  = RegexTokenizer(inputCol="text", outputCol="tokens", pattern="\\W+")
    stop = StopWordsRemover(inputCol="tokens", outputCol="clean")

    # Reduce dimensionality and ignore very rare terms to save memory
    tf   = HashingTF(inputCol="clean", outputCol="tf", numFeatures=1<<16)  # 65,536 dims
    idf  = IDF(inputCol="tf", outputCol="feat", minDocFreq=5)

    km   = (KMeans(featuresCol="feat", predictionCol="cluster", k=k, seed=42)
            .setInitMode("k-means||")
            .setInitSteps(2)
            .setMaxIter(20))

    pipe = Pipeline(stages=[tok, stop, tf, idf, km])

    # Fit & evaluate
    model = pipe.fit(df)
    pred  = model.transform(df)

    sil = ClusteringEvaluator(featuresCol="feat", predictionCol="cluster").evaluate(pred)
    print(f"k={k} silhouette={sil}")

    spark.stop()

if __name__ == "__main__":
    for k in [10, 15, 20]:
        run_kmeans(k)



