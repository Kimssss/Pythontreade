"""
자동매매 엔진

장 시간 동안 자동으로 매수/매도를 실행하는 메인 엔진
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
from strategies.momentum_volume_strategy import MomentumVolumeStrategy


class AutoTrader:
    """자동매매 엔진"""

    def __init__(self, api, strategy_config: Dict = None):
        """
        초기화

        Args:
            api: KisAPI 인스턴스
            strategy_config: 전략 설정
        """
        self.api = api
        self.strategy = MomentumVolumeStrategy(api, strategy_config)

        # 실행 설정
        self.is_running = False
        self.is_paused = False
        self.check_interval = 60  # 기본 60초 간격

        # 장 시간 설정 (한국 시간 기준)
        self.market_open = (9, 5)    # 09:05 (장 시작 5분 후)
        self.market_close = (15, 20)  # 15:20 (장 마감 10분 전)

        # 콜백
        self.on_trade_callback: Optional[Callable] = None
        self.on_status_callback: Optional[Callable] = None

        # 로그
        self.logs = []

    def log(self, message: str, level: str = "INFO"):
        """로그 기록"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_entry)
        print(log_entry)

        # 최대 1000개 로그 유지
        if len(self.logs) > 1000:
            self.logs = self.logs[-500:]

    def is_market_open(self) -> bool:
        """장 시간 확인"""
        now = datetime.now()

        # 주말 체크
        if now.weekday() >= 5:
            return False

        # 시간 체크
        current_time = (now.hour, now.minute)
        return self.market_open <= current_time <= self.market_close

    def get_time_to_market_open(self) -> Optional[timedelta]:
        """장 시작까지 남은 시간"""
        now = datetime.now()

        # 주말이면 월요일까지
        if now.weekday() >= 5:
            days_until_monday = 7 - now.weekday()
            next_open = now.replace(
                hour=self.market_open[0],
                minute=self.market_open[1],
                second=0,
                microsecond=0
            ) + timedelta(days=days_until_monday)
            return next_open - now

        # 장 시작 전
        market_open_time = now.replace(
            hour=self.market_open[0],
            minute=self.market_open[1],
            second=0,
            microsecond=0
        )

        if now < market_open_time:
            return market_open_time - now

        # 장 마감 후 - 다음날
        if now.hour >= self.market_close[0] and now.minute > self.market_close[1]:
            next_open = market_open_time + timedelta(days=1)
            return next_open - now

        return None

    def start(self, check_interval: int = 60):
        """
        자동매매 시작

        Args:
            check_interval: 체크 간격 (초)
        """
        if self.is_running:
            self.log("이미 실행 중입니다.", "WARNING")
            return

        self.check_interval = check_interval
        self.is_running = True
        self.is_paused = False

        self.log(f"자동매매 시작 (체크 간격: {check_interval}초)")

        # 별도 스레드에서 실행
        self.trade_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.trade_thread.start()

    def stop(self):
        """자동매매 중지"""
        if not self.is_running:
            return

        self.is_running = False
        self.log("자동매매 중지")

    def pause(self):
        """일시 정지"""
        self.is_paused = True
        self.log("자동매매 일시 정지")

    def resume(self):
        """재개"""
        self.is_paused = False
        self.log("자동매매 재개")

    def _run_loop(self):
        """메인 실행 루프"""
        while self.is_running:
            try:
                # 일시 정지 상태
                if self.is_paused:
                    time.sleep(1)
                    continue

                # 장 시간 체크
                if not self.is_market_open():
                    time_to_open = self.get_time_to_market_open()
                    if time_to_open:
                        hours, remainder = divmod(time_to_open.seconds, 3600)
                        minutes = remainder // 60
                        self.log(f"장 외 시간. 장 시작까지 약 {hours}시간 {minutes}분 남음")
                    time.sleep(60)  # 1분마다 확인
                    continue

                # 전략 실행
                self.log("전략 실행 중...")
                result = self.strategy.run_once()

                # 콜백 호출
                if self.on_trade_callback:
                    self.on_trade_callback(result)

                # 거래 결과 로깅
                if result['buys']:
                    for buy in result['buys']:
                        self.log(f"매수: {buy}", "TRADE")

                if result['sells']:
                    for sell in result['sells']:
                        self.log(f"매도: {sell}", "TRADE")

                if result['errors']:
                    for error in result['errors']:
                        self.log(f"오류: {error}", "ERROR")

                # 대기
                time.sleep(self.check_interval)

            except Exception as e:
                self.log(f"오류 발생: {e}", "ERROR")
                time.sleep(10)

    def run_once_now(self) -> Dict:
        """즉시 1회 실행"""
        self.log("전략 즉시 실행")
        return self.strategy.run_once()

    def get_status(self) -> Dict:
        """현재 상태 조회"""
        strategy_status = self.strategy.get_status()

        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'is_market_open': self.is_market_open(),
            'check_interval': self.check_interval,
            'strategy_status': strategy_status,
            'recent_logs': self.logs[-20:]
        }

    def get_config(self) -> Dict:
        """현재 설정 조회"""
        return self.strategy.config

    def update_config(self, new_config: Dict):
        """설정 업데이트"""
        self.strategy.config.update(new_config)
        self.log(f"설정 업데이트: {new_config}")

    def get_trade_history(self) -> list:
        """거래 내역 조회"""
        return self.strategy.trade_history


class AutoTraderManager:
    """자동매매 관리자 (UI 연동용)"""

    def __init__(self, api):
        self.api = api
        self.trader: Optional[AutoTrader] = None

    def create_trader(self, config: Dict = None) -> AutoTrader:
        """트레이더 생성"""
        self.trader = AutoTrader(self.api, config)
        return self.trader

    def get_trader(self) -> Optional[AutoTrader]:
        """현재 트레이더 반환"""
        return self.trader

    def start_trading(self, interval: int = 60):
        """매매 시작"""
        if not self.trader:
            self.create_trader()
        self.trader.start(interval)

    def stop_trading(self):
        """매매 중지"""
        if self.trader:
            self.trader.stop()

    def get_status(self) -> Dict:
        """상태 조회"""
        if self.trader:
            return self.trader.get_status()
        return {'is_running': False, 'message': '트레이더가 초기화되지 않았습니다.'}
