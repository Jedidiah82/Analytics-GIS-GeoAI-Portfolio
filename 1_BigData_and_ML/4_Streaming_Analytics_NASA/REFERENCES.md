# Sources and implementation references

- [NASA-HTTP, Internet Traffic Archive](https://ita.ee.lbl.gov/html/contrib/NASA-HTTP.html): source trace description, provenance, redistribution terms, and instruction to limit analysis to general traffic patterns. The traces were collected by Jim Dumoulin of Kennedy Space Center and contributed by Martin Arlitt and Carey Williamson. No host-level analysis or original request paths are published in this project.
- [Apache Spark 3.5 Structured Streaming guide](https://spark.apache.org/docs/3.5.6/structured-streaming-programming-guide.html): append/update/complete semantics, event-time watermarks, checkpoint recovery, and sink guarantees. The executed environment is pinned to PySpark 3.5.1; the linked maintenance-series guide documents the relevant semantics.

The archive description contains inconsistent prose about the measurement duration. This project uses the local files' parsed timestamps and line counts for its actual coverage, with SHA-256 hashes retained in the run manifest.

The original published workload study is Arlitt, M. and Williamson, C. (1996), *Web Server Workload Characterization: The Search for Invariants*, ACM SIGMETRICS. See the archive page for its historical publication context.
