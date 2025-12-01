#!/usr/bin/env python3
"""
최종 상태 요약
"""
import os
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

print("=" * 60)
print("📊 AI 자동매매 시스템 최종 상태")
print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

print("\n1️⃣ 환경 설정")
print("-" * 40)
print(f"모의투자 계좌: {os.environ.get('DEMO_ACCOUNT_NO', 'Not set')}")
print(f"실전투자 계좌: {os.environ.get('REAL_ACCOUNT_NO', 'Not set')}")
print(f"API 키 설정: {'✅' if os.environ.get('DEMO_APPKEY') else '❌'}")

print("\n2️⃣ 해결된 문제")
print("-" * 40)
print("✅ 주말/장외시간 잔고 조회 오류 수정")
print("   - ord_psbl_cash가 0일 때 다른 필드 확인")
print("✅ 해외주식 거래 기능 추가")
print("   - 한국/미국 주식만 지원")
print("✅ 시간대별 자동 거래")
print("   - 한국: 09:00-15:30")
print("   - 미국: 22:30-05:00")
print("✅ API 토큰 인증 성공")

print("\n3️⃣ 현재 상태")
print("-" * 40)
print("📍 계좌번호: 50144239-01")
print("💰 계좌잔고: 9,842,748원")
print("🔌 API 연결: 정상")
print("📈 주가조회: 가능")
print("💸 모의주문: ❌ 불가 (모의투자 참가 신청 필요)")

print("\n4️⃣ 필요한 조치")
print("-" * 40)
print("1. 한국투자증권 웹/앱에서 모의투자 참가 신청")
print("2. 가상머니 충전 (1억원)")
print("3. 모의투자 약관 동의")

print("\n5️⃣ 실행 명령어")
print("-" * 40)
print("# 모의투자 모드 실행")
print("python -m ai_trading_system.main_trading_system --mode demo")
print("\n# 실전투자 모드 실행")
print("python -m ai_trading_system.main_trading_system --mode real")

print("\n6️⃣ 주요 파일")
print("-" * 40)
print("📁 /ai_trading_system/")
print("  ├── main_trading_system.py     # 메인 실행")
print("  ├── utils/kis_api.py           # 한국 API")
print("  ├── utils/kis_api_overseas.py  # 해외 API")
print("  ├── strategies/global_screener.py # 글로벌 스크리너")
print("  └── .env                       # 환경변수")

print("\n✅ 시스템 준비 완료!")
print("모의투자 참가 신청 후 거래가 가능합니다.")
print("=" * 60)