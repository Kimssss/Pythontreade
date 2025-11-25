#!/bin/bash

echo "🚀 한국투자증권 자동매매 시스템 실행"

# 가상환경 활성화 및 프로그램 실행
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    python trading_ui.py
else
    echo "❌ 가상환경을 찾을 수 없습니다."
    echo "먼저 다음 명령어들을 실행하세요:"
    echo "1. python3 -m venv .venv"
    echo "2. ./install.sh"
fi