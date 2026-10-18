"""Train-only PySpark baselines with explicit labels and temporal evaluation.

Input: original headerless 49-column UNSW-NB15 flow CSV (not the 45-column
official train/test subset). No addresses, ports, timestamps or labels enter X.
"""
from pathlib import Path
import argparse, hashlib, json, platform, time
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, average_precision_score,
    balanced_accuracy_score, confusion_matrix, f1_score, precision_recall_curve,
    precision_recall_fscore_support, roc_auc_score, roc_curve)

COLUMNS=['srcip','sport','dstip','dsport','proto','state','dur','sbytes','dbytes','sttl','dttl','sloss','dloss','service','Sload','Dload','Spkts','Dpkts','swin','dwin','stcpb','dtcpb','smeansz','dmeansz','trans_depth','res_bdy_len','Sjit','Djit','Stime','Ltime','Sintpkt','Dintpkt','tcprtt','synack','ackdat','is_sm_ips_ports','ct_state_ttl','ct_flw_http_mthd','is_ftp_login','ct_ftp_cmd','ct_srv_src','ct_srv_dst','ct_dst_ltm','ct_src_ltm','ct_src_dport_ltm','ct_dst_sport_ltm','ct_dst_src_ltm','attack_cat','label']
CLASSES=['Normal','Analysis','Backdoor','DoS','Exploits','Fuzzers','Generic','Reconnaissance','Shellcode','Worms']
FEATURES=['log_sbytes','log_dbytes','sttl','dttl']

def canonical_category(binary, category):
    """Reference contract, shared by tests and Spark label validation."""
    if binary not in (0,1):raise ValueError('Binary label must be 0 or 1')
    value='' if category is None else str(category).strip().lower()
    aliases={c.lower():c for c in CLASSES};aliases['backdoors']='Backdoor'
    if binary==0 and value in ('','normal'):return 'Normal'
    if binary==1 and value in aliases and aliases[value]!='Normal':return aliases[value]
    raise ValueError('Category disagrees with binary label or is unknown')

def metric_rows(actual,prediction,names):
    labels=np.arange(len(names))
    precision,recall,f1,support=precision_recall_fscore_support(actual,prediction,labels=labels,zero_division=0)
    return pd.DataFrame({'class':names,'precision':precision,'recall':recall,'f1':f1,'support':support})

def summarize(actual,prediction,names):
    rows=metric_rows(actual,prediction,names)
    cm=confusion_matrix(actual,prediction,labels=np.arange(len(names)))
    return {'accuracy':accuracy_score(actual,prediction),
            'macro_f1':float(rows.f1.mean()),
            'weighted_f1':f1_score(actual,prediction,labels=np.arange(len(names)),average='weighted',zero_division=0),
            'balanced_accuracy':float(rows.loc[rows.support>0,'recall'].mean()),
            'observations':len(actual)},rows,cm

def read_validated(spark,input_path):
    from pyspark.sql import functions as F
    raw=spark.read.option('header',False).option('inferSchema',False).option('mode','FAILFAST').csv(str(input_path))
    if len(raw.columns)!=49:raise ValueError('Expected headerless 49-column CSV; use original flow files')
    raw=raw.toDF(*COLUMNS)
    # Hash every original field, including timestamps, to audit exact-record overlap.
    selected=raw.select(*[F.col(c).cast('double').alias(c) for c in ['sbytes','dbytes','sttl','dttl','Stime','Ltime','label']],
        F.lower(F.trim(F.coalesce(F.col('attack_cat'),F.lit('')))).alias('category'),
        F.sha2(F.to_json(F.struct(*[F.col(c) for c in COLUMNS])),256).alias('record_hash'))
    invalid=F.lit(False)
    for c in ['sbytes','dbytes','sttl','dttl','Stime','Ltime','label']:
        invalid=invalid | F.col(c).isNull() | F.isnan(c) | (F.abs(F.col(c))==float('inf'))
    invalid=invalid | (~F.col('label').isin(0.,1.))
    for c in ['sbytes','dbytes']:invalid=invalid | (F.col(c)<0) | (F.col(c)!=F.floor(c))
    for c in ['sttl','dttl']:invalid=invalid | (~F.col(c).between(0,255)) | (F.col(c)!=F.floor(c))
    invalid=invalid | (F.col('Ltime')<F.col('Stime'))
    if selected.filter(invalid).limit(1).count():raise ValueError('Invalid numeric feature, timestamp, or binary label')
    aliases={c.lower():c for c in CLASSES};aliases['backdoors']='Backdoor'
    mapping=F.create_map(*[F.lit(x) for kv in aliases.items() for x in kv])
    selected=selected.withColumn('class_name',F.when((F.col('label')==0)&F.col('category').isin('','normal'),F.lit('Normal')).otherwise(mapping[F.col('category')]))
    mismatch=selected.filter(F.col('class_name').isNull() | ((F.col('label')==0)&(F.col('class_name')!='Normal')) | ((F.col('label')==1)&(F.col('class_name')=='Normal'))).limit(1).count()
    if mismatch:raise ValueError('Unknown category or binary/category disagreement')
    indices=F.create_map(*[F.lit(x) for i,c in enumerate(CLASSES) for x in (c,float(i))])
    return selected.withColumn('label_multi',indices[F.col('class_name')]).withColumn('log_sbytes',F.log1p('sbytes')).withColumn('log_dbytes',F.log1p('dbytes')).withColumn('day',F.date_format(F.from_unixtime('Stime'),'yyyy-MM-dd'))

def split_data(data,name,cutoff,seed):
    from pyspark.sql import functions as F
    if name=='capture_holdout':
        # Training flows must finish before the cutoff; no crossing-flow leakage.
        return data.filter(F.col('Ltime')<cutoff),data.filter(F.col('Stime')>=cutoff)
    # Deterministic group split keeps exact duplicate records together.
    bucket=F.pmod(F.xxhash64(F.col('record_hash'),F.lit(seed)),F.lit(10000))
    return data.filter(bucket<7000),data.filter(bucket>=7000)

def export_curves(y,score,split,results):
    fpr,tpr,_=roc_curve(y,score);precision,recall,_=precision_recall_curve(y,score)
    # Curves contain aggregates only; bound plot exports without changing scores.
    for name,x,z in [('roc',fpr,tpr),('pr',recall,precision)]:
        index=np.unique(np.linspace(0,len(x)-1,min(1200,len(x)),dtype=int))
        pd.DataFrame({'x':x[index],'y':z[index]}).to_csv(results/f'{split}_{name}.csv',index=False)

def run(input_path,output,private_output,master='local[4]',seed=42):
    import pyspark, sklearn
    from pyspark.sql import SparkSession, functions as F
    from pyspark.ml.feature import VectorAssembler
    from pyspark.ml.classification import LogisticRegression,RandomForestClassifier
    from pyspark.ml.functions import vector_to_array
    output=Path(output);results=output/'results';results.mkdir(parents=True,exist_ok=True)
    private=Path(private_output);private.mkdir(parents=True,exist_ok=True)
    spark=SparkSession.builder.master(master).appName('UNSW-NB15 corrected evaluation').config('spark.ui.enabled','false').config('spark.sql.session.timeZone','UTC').config('spark.sql.shuffle.partitions','16').config('spark.driver.bindAddress','127.0.0.1').config('spark.driver.host','127.0.0.1').getOrCreate()
    spark.sparkContext.setLogLevel('ERROR');start=time.perf_counter()
    data=read_validated(spark,input_path).cache();total=data.count()
    print('Validated',total,'flows',flush=True)
    composition=data.groupBy('day','class_name').count().toPandas();composition.to_csv(results/'data_composition.csv',index=False)
    duplicate_extra=total-data.select('record_hash').distinct().count()
    cutoff=1422748800 # 2015-02-01 00:00:00 UTC; fixed calendar boundary
    metrics=[];per_class=[];splits=[];timings=[];coefs=[];importances=[]
    for split in ['group_random_70_30','capture_holdout']:
        train,test=split_data(data,split,cutoff,seed);train=train.cache();test=test.cache()
        ntrain,ntest=train.count(),test.count()
        if not ntrain or not ntest:raise ValueError('Both partitions must be nonempty')
        if train.select('record_hash').join(test.select('record_hash'),'record_hash','inner').limit(1).count():raise AssertionError('Exact record crossed split')
        train_counts=train.groupBy('class_name').count().toPandas().set_index('class_name')['count'].to_dict()
        test_counts=test.groupBy('class_name').count().toPandas().set_index('class_name')['count'].to_dict()
        if set(train_counts)!=set(CLASSES):raise ValueError('Training partition lacks a required class')
        for c in CLASSES:splits.append({'split':split,'class':c,'train':train_counts.get(c,0),'test':test_counts.get(c,0)})
        assembler=VectorAssembler(inputCols=FEATURES,outputCol='features',handleInvalid='error')
        tr=assembler.transform(train).select('features','label','label_multi').cache()
        te=assembler.transform(test).select('features','label','label_multi').cache()
        print(split,'train',ntrain,'test',ntest,flush=True)
        majority=max(CLASSES,key=lambda c:train_counts[c]);majority_index=CLASSES.index(majority)
        for model_name in ['Majority baseline','Logistic Regression','Random Forest']:
            t=time.perf_counter()
            if model_name=='Logistic Regression':
                model=LogisticRegression(featuresCol='features',labelCol='label',maxIter=100,regParam=.01,elasticNetParam=0.,tol=1e-7,standardization=True).fit(tr)
                frame=model.transform(te).select('label','prediction',vector_to_array('probability')[1].alias('score')).toPandas()
                actual=frame.label.to_numpy(dtype=int);pred=frame.prediction.to_numpy(dtype=int);score=frame.score.to_numpy()
                row,detail,cm=summarize(actual,pred,['Normal','Attack']);row.update(roc_auc=roc_auc_score(actual,score),average_precision=average_precision_score(actual,score),attack_prevalence=float(actual.mean()),threshold=.5)
                export_curves(actual,score,split,results)
                for feature,coef in zip(FEATURES,model.coefficients):coefs.append({'split':split,'feature':feature,'coefficient':float(coef)})
                task='binary';np.savez_compressed(private/f'{split}_lr.npz',actual=actual,prediction=pred,score=score)
            else:
                if model_name=='Random Forest':
                    model=RandomForestClassifier(featuresCol='features',labelCol='label_multi',numTrees=60,maxDepth=12,maxBins=64,minInstancesPerNode=5,seed=seed,featureSubsetStrategy='auto').fit(tr)
                    frame=model.transform(te).select('label_multi','prediction').toPandas()
                    actual=frame.label_multi.to_numpy(dtype=int);pred=frame.prediction.to_numpy(dtype=int)
                    for feature,importance in zip(FEATURES,model.featureImportances):importances.append({'split':split,'feature':feature,'importance':float(importance)})
                    np.savez_compressed(private/f'{split}_rf.npz',actual=actual,prediction=pred)
                else:
                    actual=te.select('label_multi').toPandas().label_multi.to_numpy(dtype=int);pred=np.full_like(actual,majority_index)
                row,detail,cm=summarize(actual,pred,CLASSES);task='multiclass'
            row.update(split=split,model=model_name,task=task);metrics.append(row)
            detail['split']=split;detail['model']=model_name;per_class.append(detail)
            pd.DataFrame(cm,index=['Normal','Attack'] if task=='binary' else CLASSES,columns=['Normal','Attack'] if task=='binary' else CLASSES).rename_axis('actual').to_csv(results/f'{split}_{"lr" if task=="binary" else "rf" if model_name=="Random Forest" else "majority"}_confusion.csv')
            timings.append({'split':split,'model':model_name,'fit_predict_export_seconds':time.perf_counter()-t})
            print(split,model_name,json.dumps(row),flush=True)
        tr.unpersist();te.unpersist();train.unpersist();test.unpersist()
    pd.DataFrame(metrics).to_csv(results/'model_metrics.csv',index=False)
    pd.concat(per_class).to_csv(results/'per_class_metrics.csv',index=False)
    pd.DataFrame(splits).to_csv(results/'split_support.csv',index=False)
    pd.DataFrame(timings).to_csv(results/'runtime.csv',index=False)
    pd.DataFrame(coefs).to_csv(results/'lr_coefficients.csv',index=False)
    pd.DataFrame(importances).to_csv(results/'rf_importance.csv',index=False)
    source_hash=hashlib.sha256(Path(input_path).read_bytes()).hexdigest()
    manifest={'run_date':time.strftime('%Y-%m-%d'),'input_sha256':source_hash,'rows':total,'exact_duplicate_extra_rows':duplicate_extra,'schema':'Headerless 49-column original flow CSV','features':FEATURES,'binary_label':'Original 0=Normal, 1=Attack; category agreement validated','class_order':CLASSES,'split_seed':seed,'capture_boundary_utc':'2015-02-01T00:00:00Z','group_random':'Hash of full original record plus seed, 70/30; identical records remain together','primary_evaluation':'January capture training / February capture testing; not official benchmark partition','selection':'Fixed hyperparameters; no holdout tuning or model selection','lr':{'maxIter':100,'regParam':.01,'standardization':True,'threshold':.5},'rf':{'numTrees':60,'maxDepth':12,'maxBins':64,'minInstancesPerNode':5,'seed':seed},'execution':{'master':master,'single_machine':True,'seconds':time.perf_counter()-start},'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'scikit_learn':sklearn.__version__,'pyspark':pyspark.__version__},'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (output/'src').glob('*.py')}}
    (results/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    spark.stop();print('Completed all model evaluations.',flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--output',default='.');ap.add_argument('--private-output',required=True);ap.add_argument('--master',default='local[4]');args=ap.parse_args()
    run(args.input,args.output,args.private_output,args.master)
