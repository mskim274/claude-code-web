@echo off
chcp 65001 > nul
title 데이터 수집 모니터링

python monitor_collection.py
pause
