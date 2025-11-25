#!/bin/bash

echo "🏦 한국투자증권 자동매매 시스템 설치 스크립트"
echo "=================================================="

# 가상환경 활성화
if [ -f ".venv/bin/activate" ]; then
    echo "🔄 가상환경 활성화..."
    source .venv/bin/activate
else
    echo "❌ 가상환경을 찾을 수 없습니다."
    echo "다음 명령어로 가상환경을 생성하세요:"
    echo "python3 -m venv .venv"
    exit 1
fi

# 패키지 설치
echo "📦 필요한 패키지 설치..."
pip install -r requirements.txt

# 환경 파일 확인
if [ ! -f ".env" ]; then
    echo "⚠️  .env 파일이 없습니다."
    echo "📝 .env.example을 참고하여 .env 파일을 생성해주세요."
    echo "cp .env.example .env"
    echo "그 후 .env 파일에 API 키 정보를 입력하세요."
else
    echo "✅ .env 파일이 존재합니다."
fi

echo "=================================================="
echo "✅ 설치 완료!"
echo "🚀 다음 명령어로 프로그램을 실행하세요:"
echo "source .venv/bin/activate && python trading_ui.py"
echo "=================================================="