@echo off
set PYTHONPATH=src
python -m uvicorn oss_check.web.main:app --reload