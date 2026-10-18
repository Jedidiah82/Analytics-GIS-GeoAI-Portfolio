# Sources and methods

- [News Category Dataset — original publisher](https://www.kaggle.com/datasets/rmisra/news-category-dataset). Local v3 JSON input; checksum recorded in the manifest. Respect the source's licensing and attribution conditions; no raw headlines are redistributed here.
- [20 Newsgroups original dataset](http://qwone.com/~jason/20Newsgroups/). Official by-date archive.
- [scikit-learn dataset documentation](https://scikit-learn.org/stable/datasets/real_world.html#the-20-newsgroups-text-dataset). By-date partitions and removal of headers, footers, and quoted text.
- [Gensim Word2Vec](https://radimrehurek.com/gensim/models/word2vec.html). CBOW settings and reproducibility constraints.
- [scikit-learn text clustering example](https://scikit-learn.org/stable/auto_examples/text/plot_document_clustering.html). Sparse features, LSA, and clustering evaluation.

The executable environment is pinned in requirements.txt, rather than inferred from the current online documentation version. In particular, the text-stripping helpers are private scikit-learn APIs and require the pinned release.
