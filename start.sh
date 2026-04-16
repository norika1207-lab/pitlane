#!/bin/bash
# PitLane 啟動腳本 — 使用 venv，不要用系統 python
cd /opt/racing
exec /opt/racing/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8002 --no-access-log
