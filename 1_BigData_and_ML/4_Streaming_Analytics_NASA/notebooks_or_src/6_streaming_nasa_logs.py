"""Compatibility entry point for the corrected single-query implementation.

Supply --input-dir, --checkpoint and --output-dir; use run_replay.py for the
measured finite replay. Legacy hard-coded paths and complete mode are retired.
"""
import runpy

if __name__=='__main__':
    runpy.run_module('nasa_streaming_counts',run_name='__main__')
