#!/bin/bash
# AI Trading System 실행 스크립트

echo "Starting AI Trading System..."

# 환경 변수 로드
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# ai_trading_system 디렉토리로 이동
cd ai_trading_system

# 환경 변수 파일 로드
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

# Python 실행
python -m main_trading_system

echo "Trading system stopped."