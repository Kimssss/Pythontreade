"""
Gmail 알림 시스템
dsangwoo@gmail.com으로 주요 이벤트 알림
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import datetime as dt
import logging
from typing import Dict, Any
import os

logger = logging.getLogger('gmail_notifier')

class GmailNotifier:
    """Gmail 알림 전송 클래스"""
    
    def __init__(self):
        """Gmail SMTP 설정"""
        self.sender_email = "dsangwoo@gmail.com"
        self.sender_password = os.environ.get('GMAIL_APP_PASSWORD', 'ungj mgnu djyk araf')
        self.recipient_email = "dsangwoo@gmail.com"
        
        # Gmail SMTP 설정
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
        logger.info(f"Gmail 알림 시스템 초기화: {self.sender_email} → {self.recipient_email}")
        
        # 포트폴리오 알림 설정
        self.portfolio_notify_interval = 3600  # 1시간마다 (초 단위)
        self.last_portfolio_notify = 0
        
    def send_email(self, subject: str, body: str, is_urgent: bool = False) -> bool:
        """이메일 전송"""
        try:
            # 긴급 표시
            if is_urgent:
                subject = f"🚨 [긴급] {subject}"
            else:
                subject = f"📊 [AI트레이딩] {subject}"
            
            # 메시지 구성
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            
            # 본문 추가
            msg.attach(MIMEText(body, 'plain'))
            
            # SMTP 서버 연결 및 전송
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, self.recipient_email, text)
            server.quit()
            
            logger.info(f"이메일 전송 성공: {subject}")
            print(f"📧 이메일 전송 완료: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"이메일 전송 실패: {e}")
            print(f"❌ 이메일 전송 실패: {e}")
            return False
    
    def notify_trade_execution(self, trade_info: Dict[str, Any]):
        """매매 체결 알림"""
        if trade_info['type'] == '매수':
            subject = f"매수 체결: {trade_info['stock_name']} ({trade_info['stock_code']})"
            body = f"""
AI 트레이딩 매수 체결 알림

종목: {trade_info['stock_name']} ({trade_info['stock_code']})
체결가: {trade_info['price']:,}원
수량: {trade_info['quantity']}주
체결금액: {trade_info['total_amount']:,}원
AI 신뢰도: {trade_info.get('confidence', 0):.1f}%
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

AI 트레이딩 시스템 자동 알림
"""
        else:  # 매도
            profit = trade_info.get('profit', 0)
            profit_rate = trade_info.get('profit_rate', 0)
            
            subject = f"매도 체결: {trade_info['stock_name']} (수익률 {profit_rate:.1f}%)"
            body = f"""
AI 트레이딩 매도 체결 알림

종목: {trade_info['stock_name']} ({trade_info['stock_code']})
매도가: {trade_info['sell_price']:,}원
매수가: {trade_info.get('buy_price', 0):,}원
수량: {trade_info['quantity']}주
수익: {profit:,}원
수익률: {profit_rate:.1f}%
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

AI 트레이딩 시스템 자동 알림
"""
        
        # 중요 거래인 경우 긴급 알림
        is_urgent = abs(trade_info.get('total_amount', 0)) > 1000000
        
        return self.send_email(subject, body, is_urgent)
    
    def notify_error(self, error_info: Dict[str, Any]):
        """에러 발생 알림"""
        subject = f"시스템 에러: {error_info['error_type']}"
        
        body = f"""
AI 트레이딩 시스템 에러 알림

에러 타입: {error_info['error_type']}
에러 메시지: {error_info['error_msg']}
발생 위치: {error_info.get('location', 'Unknown')}
발생 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

상세 정보:
{error_info.get('details', 'N/A')[:500]}...

시스템이 자동으로 복구를 시도하고 있습니다.
"""
        
        return self.send_email(subject, body, is_urgent=True)
    
    def notify_daily_summary(self, summary: Dict[str, Any]):
        """일일 거래 요약 알림"""
        subject = f"일일 거래 요약 ({datetime.now().strftime('%Y-%m-%d')})"
        
        body = f"""
오늘의 AI 트레이딩 성과

📊 거래 요약
- 총 거래: {summary.get('total_trades', 0)}건
- 매수: {summary.get('buy_trades', 0)}건 (성공: {summary.get('buy_success', 0)})
- 매도: {summary.get('sell_trades', 0)}건 (성공: {summary.get('sell_success', 0)})

💰 수익 현황
- 일일 수익: {summary.get('daily_profit', 0):,}원
- 일일 수익률: {summary.get('daily_return', 0):.2f}%
- 승률: {summary.get('win_rate', 0):.1f}%

📈 포트폴리오
- 총 자산: {summary.get('total_assets', 0):,}원
- 현금: {summary.get('cash', 0):,}원
- 주식평가액: {summary.get('stock_value', 0):,}원

🤖 AI 성능
- DQN 정확도: {summary.get('dqn_accuracy', 0):.1f}%
- 평균 신뢰도: {summary.get('avg_confidence', 0):.1f}%

생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.send_email(subject, body)
    
    def notify_monitoring_start(self, duration_hours: int = 24):
        """모니터링 시작 알림"""
        subject = "AI 트레이딩 모니터링을 시작합니다"
        
        body = f"""
AI 트레이딩 시스템 모니터링 시작 알림

시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
예정 기간: {duration_hours}시간
종료 예정: {(datetime.now() + dt.timedelta(hours=duration_hours)).strftime('%Y-%m-%d %H:%M:%S')}

모니터링 항목:
- 시스템 상태 점검
- API 호출 모니터링
- 매매 신호 생성 및 실행
- 포트폴리오 추적
- 오류 감지 및 자동 수정

중요 이벤트 발생 시 실시간으로 알림드리겠습니다.
"""
        
        return self.send_email(subject, body)
    
    def notify_monitoring_status(self, status: str, details: str = ""):
        """모니터링 상태 알림"""
        subject = f"모니터링 상태: {status}"
        
        body = f"""
AI 트레이딩 시스템 모니터링 알림

상태: {status}
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{details}

AI 트레이딩 시스템 자동 알림
"""
        
        return self.send_email(subject, body)
    
    def notify_error_fixed(self, error_type: str, fix_description: str = ""):
        """오류 수정 후 재시작 알림"""
        subject = f"오류 수정 완료: {error_type}"
        
        body = f"""
AI 트레이딩 시스템 오류 수정 알림

발견된 오류: {error_type}
수정 내용: {fix_description if fix_description else "자동 수정 완료"}
조치 사항: 시스템 재시작 및 모니터링 재개
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

시스템이 정상적으로 재시작되었습니다.
30분간 추가 모니터링을 진행합니다.
"""
        
        return self.send_email(subject, body, is_urgent=True)
    
    def notify_api_failure(self, api_type: str, error_msg: str, retry_count: int = 0):
        """API 실패 알림"""
        subject = f"API 오류: {api_type}"
        
        body = f"""
AI 트레이딩 시스템 API 오류 알림

API 종류: {api_type}
오류 메시지: {error_msg}
재시도 횟수: {retry_count}회
발생 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

조치 사항:
- API Rate Limit 조정 중
- 재시도 간격 증가
- 모니터링 계속 진행

추가 오류 발생 시 알림드리겠습니다.
"""
        
        return self.send_email(subject, body, is_urgent=True)
    
    def notify_trade_failure(self, trade_type: str, stock_name: str, reason: str):
        """매매 실패 알림"""
        subject = f"{trade_type} 실패: {stock_name}"
        
        body = f"""
AI 트레이딩 매매 실패 알림

종류: {trade_type}
종목: {stock_name}
실패 사유: {reason}
발생 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

시스템이 자동으로 재시도합니다.
"""
        
        return self.send_email(subject, body)
    
    def notify_portfolio_status(self, portfolio_info: Dict[str, Any]):
        """포트폴리오 현황 정기 알림"""
        subject = f"포트폴리오 현황 ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        
        # 보유 종목 정보 생성
        holdings_text = ""
        if portfolio_info.get('holdings'):
            holdings_text = "\n📊 보유 종목:\n"
            for stock in portfolio_info['holdings']:
                profit_rate = stock.get('profit_rate', 0)
                emoji = "📈" if profit_rate > 0 else "📉" if profit_rate < 0 else "➖"
                holdings_text += f"- {stock['name']} ({stock['code']}): {stock['quantity']}주 "
                holdings_text += f"@ {stock['current_price']:,}원 {emoji} {profit_rate:+.1f}%\n"
        else:
            holdings_text = "\n현재 보유 종목이 없습니다.\n"
        
        body = f"""
AI 트레이딩 포트폴리오 정기 보고

💰 계좌 현황
- 총 자산: {portfolio_info.get('total_assets', 0):,}원
- 현금: {portfolio_info.get('cash', 0):,}원  
- 주식평가액: {portfolio_info.get('stock_value', 0):,}원
- 일일 수익: {portfolio_info.get('daily_profit', 0):+,}원
- 일일 수익률: {portfolio_info.get('daily_return', 0):+.2f}%

{holdings_text}

📈 AI 성능
- Win Rate: {portfolio_info.get('win_rate', 0):.1f}%
- 오늘 거래: {portfolio_info.get('trades_today', 0)}건
- DQN 학습: {portfolio_info.get('dqn_updates', 0)}회

시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.send_email(subject, body)
    
    def should_notify_portfolio(self) -> bool:
        """포트폴리오 알림을 보낼 시간인지 확인"""
        current_time = datetime.now().timestamp()
        if current_time - self.last_portfolio_notify >= self.portfolio_notify_interval:
            self.last_portfolio_notify = current_time
            return True
        return False
    
    def test_email_connection(self):
        """이메일 연결 테스트"""
        subject = "AI 트레이딩 시스템 이메일 알림 테스트"
        body = f"""
이메일 알림 시스템이 정상적으로 설정되었습니다.

발신자: {self.sender_email}
수신자: {self.recipient_email}
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

주요 알림 항목:
- 매매 체결 알림
- 시스템 에러 알림
- 일일 거래 요약
- 모니터링 상태

이제부터 중요한 이벤트가 발생하면 이메일로 알림을 받으실 수 있습니다.
"""
        
        return self.send_email(subject, body)