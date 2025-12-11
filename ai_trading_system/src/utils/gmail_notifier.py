#!/usr/bin/env python3
"""
Gmail 알림 시스템
주요 이벤트 및 상태 알림
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

logger = logging.getLogger('gmail_notifier')

class GmailNotifier:
    """Gmail 알림 시스템"""
    
    def __init__(self, smtp_server="smtp.gmail.com", port=587):
        self.smtp_server = smtp_server
        self.port = port
        self.from_email = "your_gmail@gmail.com"  # 실제 Gmail 계정으로 변경 필요
        self.password = "your_app_password"  # Gmail 앱 비밀번호로 변경 필요
        self.to_email = "dsangwoo@gmail.com"
        
    def send_notification(self, subject: str, message: str) -> bool:
        """알림 전송
        
        Args:
            subject: 제목
            message: 메시지 내용
            
        Returns:
            성공 여부
        """
        try:
            # 이메일 구성
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            msg['Subject'] = f"[AI트레이딩] {subject}"
            
            # 메시지 내용
            body = f"""
AI 자동매매 시스템 알림

시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{message}

---
AI Trading System 자동 알림
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # SSL 컨텍스트 생성 및 전송
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls(context=context)
                server.login(self.from_email, self.password)
                server.sendmail(self.from_email, self.to_email, msg.as_string())
            
            logger.info(f"이메일 전송 완료: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"이메일 전송 실패: {e}")
            return False
    
    def notify_trading_start(self):
        """거래 시작 알림"""
        subject = "AI 트레이딩 모니터링을 시작합니다"
        message = """
🚀 AI 자동매매 시스템이 모니터링을 시작했습니다.

• 모의투자 모드로 실행 중
• 24시간 지속 모니터링
• 주요 이벤트 실시간 알림

시스템이 정상적으로 운영됩니다.
        """
        return self.send_notification(subject, message)
    
    def notify_error(self, error_msg: str, error_type: str = "일반"):
        """에러 알림"""
        subject = f"⚠️ 에러 발생: {error_type}"
        message = f"""
❌ AI 자동매매 시스템에서 에러가 발생했습니다.

에러 유형: {error_type}
에러 내용: {error_msg}

즉시 확인이 필요합니다.
        """
        return self.send_notification(subject, message)
    
    def notify_trade_executed(self, stock_code: str, action: str, quantity: int, price: int):
        """거래 실행 알림"""
        subject = f"💰 거래 실행: {action} {stock_code}"
        message = f"""
📈 주식 거래가 실행되었습니다.

종목: {stock_code}
거래: {action}
수량: {quantity:,}주
가격: {price:,}원

거래가 성공적으로 완료되었습니다.
        """
        return self.send_notification(subject, message)
    
    def notify_ai_learning_complete(self, stock_code: str, win_rate: float):
        """AI 학습 완료 알림"""
        subject = f"🧠 AI 학습 완료: {stock_code}"
        message = f"""
🤖 AI 모델 학습이 완료되었습니다.

학습 종목: {stock_code}
예상 승률: {win_rate:.1%}

새로운 예측 모델이 적용됩니다.
        """
        return self.send_notification(subject, message)
    
    def notify_market_status(self, market: str, status: str):
        """시장 상태 알림"""
        market_names = {
            'korean': '🇰🇷 한국장',
            'us': '🇺🇸 미국장'
        }
        
        subject = f"{market_names.get(market, market)} {status}"
        message = f"""
📊 시장 상태 업데이트

{market_names.get(market, market)}: {status}
시간: {datetime.now().strftime('%H:%M')}

시장 상황에 맞는 전략으로 운영 중입니다.
        """
        return self.send_notification(subject, message)
    
    def notify_hourly_status(self, portfolio_value: float, positions: int, trades_today: int):
        """시간별 상태 알림"""
        subject = "📊 시간별 상태 리포트"
        message = f"""
⏰ 매시간 상태 업데이트

• 포트폴리오 가치: {portfolio_value:,.0f}원
• 보유 종목 수: {positions}개
• 오늘 거래 횟수: {trades_today}회
• 시스템 상태: 정상 운영 중

지속적인 모니터링이 진행되고 있습니다.
        """
        return self.send_notification(subject, message)