#!/usr/bin/env python3
"""Gmail 알림 테스트"""
import sys
sys.path.insert(0, '.')

from ai_trading_system.utils.gmail_notifier import GmailNotifier

def test_gmail():
    print("Gmail 알림 테스트 시작...")
    
    # Gmail 알림 초기화
    notifier = GmailNotifier()
    
    # 1. 연결 테스트
    print("\n1. 이메일 연결 테스트...")
    if notifier.test_email_connection():
        print("✅ 테스트 이메일 전송 성공!")
    else:
        print("❌ 테스트 이메일 전송 실패")
        return False
    
    # 2. 모니터링 시작 알림 테스트
    print("\n2. 모니터링 시작 알림 테스트...")
    if notifier.notify_monitoring_start(duration_hours=24):
        print("✅ 모니터링 시작 알림 전송 성공!")
    else:
        print("❌ 모니터링 시작 알림 전송 실패")
    
    # 3. 에러 알림 테스트
    print("\n3. 에러 알림 테스트...")
    error_info = {
        'error_type': 'TestError',
        'error_msg': '이것은 테스트 에러입니다',
        'location': 'test_gmail.py',
        'details': 'Gmail 알림 시스템 테스트 중 발생한 가상의 에러입니다.'
    }
    if notifier.notify_error(error_info):
        print("✅ 에러 알림 전송 성공!")
    else:
        print("❌ 에러 알림 전송 실패")
    
    print("\n모든 테스트 완료!")
    print(f"📧 알림이 dsangwoo222@gmail.com으로 전송되었습니다.")
    return True

if __name__ == "__main__":
    test_gmail()