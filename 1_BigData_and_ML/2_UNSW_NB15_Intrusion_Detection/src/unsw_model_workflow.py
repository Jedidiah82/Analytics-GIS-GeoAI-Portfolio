"""Archived UNSW-NB15 workflow extracted from MachineLearning.ipynb.
Selected original cells (zero-based): 3-9, 11, 14-17. Not rerun for this update.
Run from a directory containing the headerless 49-column UNSW-NB15.csv.
Requires a compatible Spark/Java/Python environment, pandas, scikit-learn,
matplotlib, and seaborn. Exact historical dependency versions are not recovered.
This preserves original modelling choices, including category-derived binary
labels and full-data StringIndexer fitting; it is not a hardened training pipeline.
No dataset or student identifiers are distributed with this snapshot.
"""

# Original notebook cell 3
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("UNSW-NB15 Analysis") \
    .getOrCreate()

# Original notebook cell 4
# Adjust the path to your actual CSV file
df = spark.read.csv("UNSW-NB15.csv", header=False, inferSchema=True)

# Rename columns (if needed)
columns = [
    'srcip', 'sport', 'dstip', 'dsport', 'proto', 'state', 'dur', 'sbytes', 'dbytes', 'sttl', 'dttl',
    'sloss', 'dloss', 'service', 'Sload', 'Dload', 'Spkts', 'Dpkts', 'swin', 'dwin', 'stcpb', 'dtcpb',
    'smeansz', 'dmeansz', 'trans_depth', 'res_bdy_len', 'Sjit', 'Djit', 'Stime', 'Ltime', 'Sintpkt',
    'Dintpkt', 'tcprtt', 'synack', 'ackdat', 'is_sm_ips_ports', 'ct_state_ttl', 'ct_flw_http_mthd',
    'is_ftp_login', 'ct_ftp_cmd', 'ct_srv_src', 'ct_srv_dst', 'ct_dst_ltm', 'ct_src_ltm',
    'ct_src_dport_ltm', 'ct_dst_sport_ltm', 'ct_dst_src_ltm', 'attack_cat', 'label'
]
for i, col_name in enumerate(columns):
    df = df.withColumnRenamed(f"_c{i}", col_name)

# Original notebook cell 5
from pyspark.sql.functions import col, udf
from pyspark.sql.types import StringType

def fix_attack_cat(cat):
    if cat is None:
        return 'Unknown'
    cat = cat.strip().lower()
    mapping = {
        'backdoor': 'Backdoor',
        'backdoors': 'Backdoor',
        'dos': 'DoS',
        'exploits': 'Exploits',
        'fuzzers': 'Fuzzers',
        'analysis': 'Analysis',
        'generic': 'Generic',
        'reconnaissance': 'Reconnaissance',
        'shellcode': 'Shellcode',
        'worms': 'Worms',
        'normal': 'Normal'
    }
    return mapping.get(cat, cat.capitalize())

fix_attack_cat_udf = udf(fix_attack_cat, StringType())
df = df.withColumn("attack_cat_clean", fix_attack_cat_udf(col("attack_cat")))

# Original notebook cell 6
from pyspark.sql.functions import when
from pyspark.ml.feature import VectorAssembler

df_bin = df.withColumn("label", when(col("attack_cat_clean") == "Unknown", 0).otherwise(1))
feature_cols = ['sbytes', 'dbytes', 'sttl', 'dttl']
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
data = assembler.transform(df_bin).select("features", "label")

# Original notebook cell 7
train, test = data.randomSplit([0.7, 0.3], seed=42)

# Original notebook cell 8
from pyspark.ml.classification import LogisticRegression

lr = LogisticRegression(featuresCol="features", labelCol="label")
model = lr.fit(train)
predictions = model.transform(test)

# Original notebook cell 9
from pyspark.ml.evaluation import BinaryClassificationEvaluator

evaluator = BinaryClassificationEvaluator()
auc = evaluator.evaluate(predictions)
print(f"Binary Classifier AUC: {auc:.3f}")

import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, roc_auc_score

roc_data = predictions.select("label", "probability").toPandas()
roc_data['prob_attack'] = roc_data['probability'].apply(lambda x: float(x[1]))

y_true = roc_data['label']
y_score = roc_data['prob_attack']

fpr, tpr, thresholds = roc_curve(y_true, y_score)
auc = roc_auc_score(y_true, y_score)

plt.figure(figsize=(7, 5))
plt.plot(fpr, tpr, label=f"ROC Curve (AUC = {auc:.3f})")
plt.plot([0, 1], [0, 1], 'k--', label="Random Guess (AUC = 0.5)")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve for Binary Classifier")
plt.legend(loc="lower right")
plt.tight_layout()
plt.savefig("binary_classifier_roc_curve.png")
plt.show()

# Original notebook cell 11
import pandas as pd
import matplotlib.pyplot as plt

roc = predictions.select("probability", "label").toPandas()
roc['prob_1'] = roc['probability'].apply(lambda x: float(x[1]))
plt.hist(roc[roc['label'] == 1]['prob_1'], bins=30, alpha=0.5, label='Attack')
plt.hist(roc[roc['label'] == 0]['prob_1'], bins=30, alpha=0.5, label='Normal')
plt.legend()
plt.title("Predicted Probability Distribution")
plt.xlabel("Predicted Probability of Attack")
plt.ylabel("Frequency")

plt.savefig("predicted_probability_histogram.png")  # Save the figure
plt.show()

# Original notebook cell 14
from pyspark.ml.feature import StringIndexer

indexer = StringIndexer(inputCol="attack_cat_clean", outputCol="label_multi")
df_multi = indexer.fit(df).transform(df)
data_multi = assembler.transform(df_multi).select("features", "label_multi")
train_m, test_m = data_multi.randomSplit([0.7, 0.3], seed=42)

# Original notebook cell 15
from pyspark.ml.classification import RandomForestClassifier

rf = RandomForestClassifier(featuresCol="features", labelCol="label_multi", numTrees=20)
model_rf = rf.fit(train_m)
predictions_rf = model_rf.transform(test_m)

# Original notebook cell 16
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

evaluator_mc = MulticlassClassificationEvaluator(labelCol="label_multi", predictionCol="prediction", metricName="accuracy")
accuracy = evaluator_mc.evaluate(predictions_rf)
print(f"Multi-class Classifier Accuracy: {accuracy:.3f}")

# Original notebook cell 17
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

cm = predictions_rf.select("label_multi", "prediction").toPandas()
conf_mat = pd.crosstab(cm['label_multi'], cm['prediction'], rownames=['Actual'], colnames=['Predicted'])

plt.figure(figsize=(8, 6))
sns.heatmap(conf_mat, annot=True, fmt='d', cmap='Blues')
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.savefig("confusion_matrix.png")
plt.show()

