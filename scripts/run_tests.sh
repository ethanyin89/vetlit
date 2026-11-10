#!/usr/bin/env bash
# Build + all tests + link check. Any failure exits non-zero (no output piping that could mask it).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 build.py >/dev/null
VETLIT_LIVE=1 python3 build_preview.py >/dev/null
python3 build_preview.py >/dev/null
python3 tests/test_merge.py
VETLIT_LIVE=1 python3 tests/test_superseded.py
VETLIT_LIVE=1 python3 tests/test_reporting_inconsistency.py
python3 tests/test_firstscreen.py
python3 tests/test_dedupe.py
VETLIT_LIVE=1 python3 tests/test_new_guidelines.py
python3 tests/test_sync_survival.py
VETLIT_LIVE=1 python3 tests/test_hyperthyroid_batch.py
VETLIT_LIVE=1 python3 tests/test_same_cohort.py
VETLIT_LIVE=1 python3 tests/test_dogAD_batch.py
VETLIT_LIVE=1 python3 tests/test_review_rob.py
VETLIT_LIVE=1 python3 tests/test_reader_pages.py
VETLIT_LIVE=1 python3 tests/test_downgrades.py
python3 tests/test_topic_fix.py
python3 scripts/check_links.py
echo ALL OK
