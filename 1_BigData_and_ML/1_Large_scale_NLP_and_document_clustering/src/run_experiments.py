"""Leakage-aware headline classification and held-out topic clustering. See README."""
import argparse, hashlib, json, re, tarfile, time, warnings, platform
from pathlib import Path
import numpy as np
import pandas as pd
from gensim.models import Word2Vec
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.dummy import DummyClassifier
from sklearn.metrics import classification_report, confusion_matrix, f1_score, accuracy_score, adjusted_rand_score, normalized_mutual_info_score, silhouette_score
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans
from sklearn.datasets._twenty_newsgroups import strip_newsgroup_header, strip_newsgroup_footer, strip_newsgroup_quoting
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
SEEDS=[42,137,2026]
TOKEN=r'[a-z]+'
def tokens(s): return re.findall(TOKEN,s.lower())
def key(s): return ' '.join(tokens(s))
def clean_news(frame):
    x=frame[['headline','category']].dropna().copy()
    x['key']=x.headline.map(key)
    empty=int((x.key=='').sum());x=x[x.key!='']
    conflicts=x.groupby('key').category.nunique();bad=set(conflicts[conflicts>1].index)
    conflicting=int(x.key.isin(bad).sum());x=x[~x.key.isin(bad)]
    duplicates=int(x.duplicated('key').sum());x=x.drop_duplicates('key').reset_index(drop=True)
    return x,dict(source_rows=len(frame),empty_removed=empty,conflicting_rows_removed=conflicting,duplicate_rows_removed=duplicates,retained_rows=len(x),classes=x.category.nunique())
def average(model, docs):
    out=np.zeros((len(docs),model.vector_size),dtype=np.float32)
    missing=0
    for i,doc in enumerate(docs):
        words=[w for w in tokens(doc) if w in model.wv]
        if words: out[i]=model.wv[words].mean(axis=0)
        else: missing+=1
    return out,missing

def load_groups(path):
    rows=[]
    with tarfile.open(path,mode='r|gz') as arc:
        for member in arc:
            parts=member.name.split('/')
            if not member.isfile() or len(parts)!=3 or parts[0] not in ['20news-bydate-train','20news-bydate-test']:continue
            text=arc.extractfile(member).read().decode('latin1')
            text=strip_newsgroup_quoting(strip_newsgroup_footer(strip_newsgroup_header(text)))
            rows.append((parts[0].split('-')[-1],parts[1],key(text),member.name))
    return pd.DataFrame(rows,columns=['partition','label','text','id']).sort_values('id').reset_index(drop=True)

def classification_provenance(news_path, output):
    import ast
    tree=ast.parse(Path(__file__).read_text())
    main_node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    block=next(n for n in ast.walk(main_node) if isinstance(n,ast.For) and isinstance(n.iter,ast.Name) and n.iter.id=='SEEDS' and any(isinstance(c,ast.For) for c in n.body))
    return dict(news_sha256=hashlib.sha256(Path(news_path).read_bytes()).hexdigest(),classifier_ast_sha256=hashlib.sha256(ast.dump(block,include_attributes=False).encode()).hexdigest(),seeds=SEEDS,result_sha256={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in ['classification_runs.csv','classification_per_class.csv','classification_confusion.csv']})
def verify_classification_resume(news_path, output):
    recorded=json.loads((output/'classification_provenance.json').read_text())
    if recorded != classification_provenance(news_path,output):
        raise ValueError('Resume requires identical news input, classifier code, seeds, and classification outputs.')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--news',required=True);ap.add_argument('--groups',required=True);ap.add_argument('--output',required=True);ap.add_argument('--private',required=True);ap.add_argument('--resume-classification',action='store_true');a=ap.parse_args()
    out=Path(a.output);out.mkdir(parents=True,exist_ok=True);private=Path(a.private);private.mkdir(parents=True,exist_ok=True)
    start=time.time();news,quality=clean_news(pd.read_json(a.news,lines=True));labels=sorted(news.category.unique());metrics=[];perclass=[];cms=[];checks=[]
    if a.resume_classification:
        verify_classification_resume(a.news,out)
        metrics=pd.read_csv(out/'classification_runs.csv').to_dict('records');assert len(metrics)==9
        for seed in SEEDS:
            tr,te=train_test_split(np.arange(len(news)),test_size=.2,random_state=seed,stratify=news.category)
            assert not set(news.iloc[tr].key)&set(news.iloc[te].key)
            checks.append(dict(seed=seed,duplicate_overlap=0))
        print('Resuming verified classification exports; starting sequential archive load.',flush=True)
    else:
        for seed in SEEDS:
            tr,te=train_test_split(np.arange(len(news)),test_size=.2,random_state=seed,stratify=news.category)
            assert not set(news.iloc[tr].key)&set(news.iloc[te].key)
            train=news.iloc[tr];test=news.iloc[te];ytr=train.category.to_numpy();yte=test.category.to_numpy()
            vec=TfidfVectorizer(max_features=100000,ngram_range=(1,2),token_pattern=TOKEN,lowercase=True)
            xtr=vec.fit_transform(train.headline);xte=vec.transform(test.headline)
            w=Word2Vec(sentences=[tokens(t) for t in train.headline],vector_size=200,window=5,min_count=5,workers=1,sg=0,epochs=5,seed=seed,sorted_vocab=1)
            atr,_=average(w,train.headline.tolist());ate,missing=average(w,test.headline.tolist());scaler=StandardScaler();atr=scaler.fit_transform(atr);ate=scaler.transform(ate)
            for name,xx,xt in [('Majority',xtr,xte),('TF-IDF + LR',xtr,xte),('Word2Vec + LR',atr,ate)]:
                tick=time.time();model=DummyClassifier(strategy='most_frequent') if name=='Majority' else LogisticRegression(C=1,solver='lbfgs',max_iter=1000,tol=1e-4,random_state=seed)
                with warnings.catch_warnings():
                    warnings.simplefilter('error',ConvergenceWarning);model.fit(xx,ytr)
                pred=model.predict(xt);report=classification_report(yte,pred,labels=labels,output_dict=True,zero_division=0)
                metrics.append(dict(seed=seed,model=name,macro_f1=f1_score(yte,pred,average='macro'),accuracy=accuracy_score(yte,pred),train_rows=len(tr),test_rows=len(te),fit_predict_seconds=time.time()-tick))
                for label in labels:perclass.append(dict(seed=seed,model=name,label=label,**report[label]))
                cm=confusion_matrix(yte,pred,labels=labels)
                for i,label in enumerate(labels):
                    for j,p in enumerate(labels):cms.append(dict(seed=seed,model=name,true_label=label,predicted_label=p,count=int(cm[i,j])))
                np.savez_compressed(private/f'classifier-{seed}-{name.split()[0]}.npz',truth=yte,prediction=pred)
                print('classification',metrics[-1],flush=True)
            checks.append(dict(seed=seed,duplicate_overlap=0,train_vocabulary=len(vec.vocabulary_),embedding_vocabulary=len(w.wv),test_empty_embedding_rows=missing))
            pd.DataFrame(metrics).to_csv(out/'classification_runs.csv',index=False)
        pd.DataFrame(perclass).to_csv(out/'classification_per_class.csv',index=False);pd.DataFrame(cms).to_csv(out/'classification_confusion.csv',index=False)
    if not a.resume_classification:
        (out/'classification_provenance.json').write_text(json.dumps(classification_provenance(a.news,out),indent=2))
    groups=load_groups(a.groups);print('Archive loaded:',len(groups),'documents',flush=True);original=groups.groupby('partition').size().to_dict();groups=groups[groups.text!=''].copy()
    # Remove duplicate normalized documents inside each partition and all test overlap with train.
    groups=groups.drop_duplicates(['partition','text']);train=groups[groups.partition=='train'];test=groups[(groups.partition=='test')&~groups.text.isin(set(train.text))]
    vec=TfidfVectorizer(max_features=50000,min_df=2,max_df=.5,stop_words='english',token_pattern=TOKEN,sublinear_tf=True)
    xtr=vec.fit_transform(train.text);xte=vec.transform(test.text)
    # Exclude documents with no retained features, explicitly counted.
    keeptr=np.asarray(xtr.getnnz(axis=1)>0);keepte=np.asarray(xte.getnnz(axis=1)>0);train=train[keeptr];test=test[keepte];xtr=xtr[keeptr];xte=xte[keepte]
    print('Prepared cluster partitions:',len(train),len(test),flush=True);svd=TruncatedSVD(n_components=100,n_iter=7,random_state=42);ztr=normalize(svd.fit_transform(xtr));zte=normalize(svd.transform(xte));clustering=[];cluster_sizes=[];contingency=[]
    for representation,xx,xt,metric in [('TF-IDF',xtr,xte,'cosine'),('LSA-100',ztr,zte,'euclidean')]:
        for seed in SEEDS:
            for k in [10,15,20]:
                model=KMeans(n_clusters=k,n_init=10,max_iter=300,random_state=seed,algorithm='lloyd');lab=model.fit_predict(xx);pred=model.predict(xt)
                row=dict(representation=representation,seed=seed,k=k,train_silhouette=silhouette_score(xx,lab,metric=metric,sample_size=min(1500,len(lab)),random_state=99),test_silhouette=silhouette_score(xt,pred,metric=metric,sample_size=min(1500,len(pred)),random_state=99),test_ari=adjusted_rand_score(test.label,pred),test_nmi=normalized_mutual_info_score(test.label,pred),iterations=int(model.n_iter_),max_iter_reached=bool(model.n_iter_==300))
                clustering.append(row);print('clustering',row,flush=True)
                for c in range(k):cluster_sizes.append(dict(representation=representation,seed=seed,k=k,cluster=c,train_count=int((lab==c).sum()),test_count=int((pred==c).sum())))
                table=pd.crosstab(test.label,pred).reindex(index=sorted(test.label.unique()),columns=range(k),fill_value=0)
                for label in table.index:
                    for c in table.columns:contingency.append(dict(representation=representation,seed=seed,k=k,label=label,cluster=int(c),count=int(table.loc[label,c])))
                np.savez_compressed(private/f'cluster-{representation}-{seed}-{k}.npz',truth=test.label.to_numpy(),prediction=pred)
                pd.DataFrame(clustering).to_csv(out/'clustering_runs.csv',index=False)
    pd.DataFrame(cluster_sizes).to_csv(out/'cluster_sizes.csv',index=False);pd.DataFrame(contingency).to_csv(out/'cluster_topics.csv',index=False)
    selected={}
    frame=pd.DataFrame(clustering)
    for rep in frame.representation.unique():
        m=frame[frame.representation==rep].groupby('k').train_silhouette.mean();selected[rep]=int(m.idxmax())
    summary=dict(news_quality=quality,classification_checks=checks,clustering_quality=dict(original_partitions=original,nonempty_deduplicated_train=len(groups[groups.partition=='train']),retained_train=len(train),retained_test=len(test),train_test_overlap=0,train_only_feature_fit=True),selected_k_by_training_silhouette=selected,svd_explained_variance=float(svd.explained_variance_ratio_.sum()),seeds=SEEDS,elapsed_seconds=time.time()-start)
    (out/'summary.json').write_text(json.dumps(summary,indent=2))
    import sklearn,gensim,scipy
    manifest=dict(inputs={Path(p).name:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in [a.news,a.groups]},versions=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,sklearn=sklearn.__version__,gensim=gensim.__version__,scipy=scipy.__version__),seeds=SEEDS,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),threads=4,word2vec_workers=1,classification_resumed=bool(a.resume_classification),elapsed_seconds_scope='current invocation; classifier fit/predict timings are in classification_runs.csv')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2));print('SUCCESS',json.dumps(summary),flush=True)
if __name__=='__main__':
    with threadpool_limits(limits=4):main()
