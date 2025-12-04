#!/usr/bin/env python3
"""
로그 메시지를 한글로 일괄 변경하는 스크립트
"""

import os
import re
from pathlib import Path

# 영어 -> 한글 매핑
TRANSLATIONS = {
    "API Request Failed": "API 요청 실패",
    "API Request Success": "API 요청 성공", 
    "Rate limit 대기": "API 호출 간격 대기",
    "Initializing": "초기화 중",
    "initialized successfully": "초기화 완료",
    "Getting access token": "액세스 토큰 발급 중",
    "Access token acquired": "액세스 토큰 발급 성공",
    "Failed to get": "가져오기 실패",
    "Successfully": "성공적으로",
    "Starting": "시작",
    "Completed": "완료",
    "Processing": "처리 중",
    "Found": "발견",
    "Error": "오류",
    "Warning": "경고",
    "Debug": "디버그",
    "Info": "정보",
    "Cash balance": "현금 잔고",
    "Portfolio value": "포트폴리오 가치",
    "Holdings": "보유 종목",
    "Trading mode": "거래 모드",
    "Market is closed": "시장이 닫혀 있음",
    "Order will be queued": "주문이 대기열에 추가됨",
    "Demo mode": "데모 모드",
    "Real mode": "실전 모드",
    "Stock screener": "주식 스크리너",
    "Volume rank": "거래량 순위",
    "Price rank": "가격 순위",
    "Market cap": "시가총액",
    "Technical analysis": "기술적 분석",
    "Risk management": "리스크 관리",
    "Ensemble system": "앙상블 시스템",
    "DQN agent": "DQN 에이전트",
    "Training": "훈련",
    "Prediction": "예측",
    "Signal": "신호",
    "Buy signal": "매수 신호",
    "Sell signal": "매도 신호",
    "Hold signal": "보유 신호",
    "Token expired": "토큰 만료",
    "Token cached": "토큰 캐시됨",
    "Loading": "로딩 중",
    "Saving": "저장 중",
    "Updated": "업데이트됨",
    "Fetching": "가져오는 중",
    "Analyzing": "분석 중",
    "Screening": "스크리닝 중"
}

def translate_file(file_path):
    """파일의 로그 메시지를 한글로 번역"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = 0
        
        # 각 번역 규칙 적용
        for english, korean in TRANSLATIONS.items():
            # logger.info, logger.error 등에서 사용되는 패턴 찾기
            patterns = [
                rf'(logger\.\w+\(["\'])({re.escape(english)})',
                rf'(print\(["\'])({re.escape(english)})',
                rf'(["\'])({re.escape(english)})(["\'])',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # 대소문자 구분 없이 교체
                    content = re.sub(pattern, rf'\1{korean}', content, flags=re.IGNORECASE)
                    changes_made += len(matches)
        
        # 내용이 변경된 경우에만 파일 저장
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {file_path}: {changes_made}개 번역 완료")
            return changes_made
        else:
            return 0
            
    except Exception as e:
        print(f"❌ {file_path}: 처리 실패 - {e}")
        return 0

def main():
    """메인 함수"""
    print("🔄 로그 메시지 한글화 작업 시작...")
    
    # AI 트레이딩 시스템 디렉토리의 모든 Python 파일 찾기
    ai_trading_dir = Path("ai_trading_system")
    python_files = list(ai_trading_dir.rglob("*.py"))
    
    # 루트 디렉토리의 Python 파일들도 포함
    root_files = ["run_ai_trading.py", "run_backtest.py", "fast_backtest.py"]
    for file_name in root_files:
        if Path(file_name).exists():
            python_files.append(Path(file_name))
    
    total_changes = 0
    processed_files = 0
    
    for file_path in python_files:
        if file_path.is_file():
            changes = translate_file(file_path)
            total_changes += changes
            if changes > 0:
                processed_files += 1
    
    print(f"\n🎯 작업 완료!")
    print(f"📁 처리된 파일: {processed_files}개")
    print(f"🔄 총 번역 횟수: {total_changes}개")
    
if __name__ == "__main__":
    main()