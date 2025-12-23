@echo off
REM PopKit Development Startup Script
REM Always use this to start Claude Code for PopKit development

cd /d C:\Users\Josep\onedrive\documents\elshaddai\apps\popkit

claude --plugin-dir ./packages/popkit-core --plugin-dir ./packages/popkit-dev --plugin-dir ./packages/popkit-ops --plugin-dir ./packages/popkit-research
