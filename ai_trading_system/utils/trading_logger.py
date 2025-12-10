"""
매매 전용 로깅 시스템
모든 매수/매도 활동을 상세히 기록
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class TradingLogger:
    """매매 전용 로거"""
    
    def __init__(self, log_dir: str = "trading_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 매매 로그 파일 설정
        self.trading_log_file = self.log_dir / f"trading_{datetime.now().strftime('%Y%m%d')}.log"
        
        # 로거 설정
        self.logger = logging.getLogger('trading_logger')
        self.logger.setLevel(logging.INFO)
        
        # 파일 핸들러 설정
        file_handler = logging.FileHandler(self.trading_log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 포맷터 설정
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # 핸들러가 중복되지 않도록 확인
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
        
        # 매매 통계
        self.trade_stats = {
            '총_거래수': 0,
            '매수_성공': 0,
            '매수_실패': 0,
            '매도_성공': 0,
            '매도_실패': 0,
            '총_수익': 0.0,
            '승률': 0.0
        }
    
    def log_buy_attempt(self, stock_code: str, stock_name: str, price: float, 
                       quantity: int, reason: str = ""):
        """매수 시도 로그"""
        log_entry = {
            '시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '종류': '매수_시도',
            '종목코드': stock_code,
            '종목명': stock_name,
            '가격': price,
            '수량': quantity,
            '금액': price * quantity,
            '사유': reason,
            'AI신호': reason
        }
        self.logger.info(f"📈 매수 시도: {json.dumps(log_entry, ensure_ascii=False, indent=2)}")
        return log_entry
    
    def log_buy_success(self, stock_code: str, stock_name: str, price: float, 
                       quantity: int, order_no: str = ""):
        """매수 성공 로그"""
        log_entry = {
            '시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '종류': '매수_성공',
            '종목코드': stock_code,
            '종목명': stock_name,
            '체결가': price,
            '체결수량': quantity,
            '체결금액': price * quantity,
            '주문번호': order_no
        }
        self.logger.info(f"✅ 매수 성공: {json.dumps(log_entry, ensure_ascii=False, indent=2)}")
        
        # 통계 업데이트
        self.trade_stats['총_거래수'] += 1
        self.trade_stats['매수_성공'] += 1
        
        return log_entry
    
    def log_buy_failure(self, stock_code: str, stock_name: str, reason: str):
        """매수 실패 로그"""
        log_entry = {
            '시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '종류': '매수_실패',
            '종목코드': stock_code,
            '종목명': stock_name,
            '실패사유': reason
        }
        self.logger.error(f"❌ 매수 실패: {json.dumps(log_entry, ensure_ascii=False, indent=2)}")
        
        # 통계 업데이트
        self.trade_stats['매수_실패'] += 1
        
        return log_entry
    
    def log_sell_attempt(self, stock_code: str, stock_name: str, price: float, 
                        quantity: int, buy_price: float = 0, reason: str = ""):
        """매도 시도 로그"""
        profit_rate = ((price - buy_price) / buy_price * 100) if buy_price > 0 else 0
        
        log_entry = {
            '시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '종류': '매도_시도',
            '종목코드': stock_code,
            '종목명': stock_name,
            '매도가격': price,
            '수량': quantity,
            '매수가': buy_price,
            '예상수익률': f"{profit_rate:.2f}%",
            '사유': reason
        }
        self.logger.info(f"📉 매도 시도: {json.dumps(log_entry, ensure_ascii=False, indent=2)}")
        return log_entry
    
    def log_sell_success(self, stock_code: str, stock_name: str, sell_price: float, 
                        quantity: int, buy_price: float = 0, order_no: str = ""):
        """매도 성공 로그"""
        profit = (sell_price - buy_price) * quantity if buy_price > 0 else 0
        profit_rate = ((sell_price - buy_price) / buy_price * 100) if buy_price > 0 else 0
        
        log_entry = {
            '시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '종류': '매도_성공',
            '종목코드': stock_code,
            '종목명': stock_name,
            '매도가': sell_price,
            '매수가': buy_price,
            '수량': quantity,
            '수익': profit,
            '수익률': f"{profit_rate:.2f}%",
            '주문번호': order_no
        }
        
        # 수익/손실에 따른 이모지
        emoji = "🎉" if profit > 0 else "😢"
        self.logger.info(f"{emoji} 매도 성공: {json.dumps(log_entry, ensure_ascii=False, indent=2)}")
        
        # 통계 업데이트
        self.trade_stats['총_거래수'] += 1
        self.trade_stats['매도_성공'] += 1
        self.trade_stats['총_수익'] += profit
        
        # 승률 계산
        total_trades = self.trade_stats['매도_성공']
        if total_trades > 0:
            if profit > 0:
                self.trade_stats['승률'] = (self.trade_stats.get('승_거래수', 0) + 1) / total_trades * 100
                self.trade_stats['승_거래수'] = self.trade_stats.get('승_거래수', 0) + 1
        
        return log_entry
    
    def log_sell_failure(self, stock_code: str, stock_name: str, reason: str):
        """매도 실패 로그"""
        log_entry = {
            '시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '종류': '매도_실패',
            '종목코드': stock_code,
            '종목명': stock_name,
            '실패사유': reason
        }
        self.logger.error(f"❌ 매도 실패: {json.dumps(log_entry, ensure_ascii=False, indent=2)}")
        
        # 통계 업데이트
        self.trade_stats['매도_실패'] += 1
        
        return log_entry
    
    def log_ai_signal(self, stock_code: str, stock_name: str, signal: str, 
                     confidence: float, indicators: Dict[str, Any]):
        """AI 신호 로그"""
        log_entry = {
            '시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '종류': 'AI_신호',
            '종목코드': stock_code,
            '종목명': stock_name,
            '신호': signal,  # 매수/매도/보유
            '신뢰도': f"{confidence:.2f}%",
            '지표': indicators
        }
        self.logger.info(f"🤖 AI 신호: {json.dumps(log_entry, ensure_ascii=False, indent=2)}")
        return log_entry
    
    def log_portfolio_status(self, total_assets: float, cash: float, 
                           stocks_value: float, daily_profit: float = 0):
        """포트폴리오 상태 로그"""
        log_entry = {
            '시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '종류': '포트폴리오_상태',
            '총자산': total_assets,
            '현금': cash,
            '주식평가액': stocks_value,
            '일일손익': daily_profit,
            '일일수익률': f"{(daily_profit / total_assets * 100):.2f}%" if total_assets > 0 else "0.00%"
        }
        self.logger.info(f"💼 포트폴리오: {json.dumps(log_entry, ensure_ascii=False, indent=2)}")
        return log_entry
    
    def log_error(self, error_type: str, error_msg: str, context: Dict[str, Any] = None):
        """에러 로그"""
        log_entry = {
            '시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '종류': 'ERROR',
            '에러타입': error_type,
            '에러메시지': error_msg,
            '컨텍스트': context or {}
        }
        self.logger.error(f"⚠️ ERROR: {json.dumps(log_entry, ensure_ascii=False, indent=2)}")
        return log_entry
    
    def get_daily_summary(self) -> Dict[str, Any]:
        """일일 거래 요약"""
        summary = {
            '날짜': datetime.now().strftime('%Y-%m-%d'),
            '총_거래수': self.trade_stats['총_거래수'],
            '매수_성공': self.trade_stats['매수_성공'],
            '매수_실패': self.trade_stats['매수_실패'],
            '매도_성공': self.trade_stats['매도_성공'],
            '매도_실패': self.trade_stats['매도_실패'],
            '총_수익': self.trade_stats['총_수익'],
            '승률': f"{self.trade_stats['승률']:.2f}%"
        }
        
        self.logger.info(f"📊 일일 요약: {json.dumps(summary, ensure_ascii=False, indent=2)}")
        return summary