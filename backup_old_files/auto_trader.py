"""
자동매매 엔진

장 시간 동안 자동으로 매수/매도를 실행하는 메인 엔진
전략 선택 및 Ollama AI 분석 지원
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
from strategies.momentum_volume_strategy import MomentumVolumeStrategy
from strategies.volatility_breakout_strategy import VolatilityBreakoutStrategy
from strategies.crewai_strategy import CrewAIStrategy


# 전략 타입 상수
STRATEGY_MOMENTUM = 'momentum'
STRATEGY_VOLATILITY = 'volatility'
STRATEGY_COMBINED = 'combined'
STRATEGY_CREWAI = 'crewai'


class AutoTrader:
    """자동매매 엔진"""

    def __init__(self, api, strategy_type: str = STRATEGY_MOMENTUM, strategy_config: Dict = None, use_ollama: bool = False):
        """
        초기화

        Args:
            api: KisAPI 인스턴스
            strategy_type: 전략 타입 ('momentum', 'volatility', 'combined')
            strategy_config: 전략 설정
            use_ollama: Ollama AI 분석 사용 여부
        """
        self.api = api
        self.strategy_type = strategy_type
        self.use_ollama = use_ollama
        self.ollama_analyzer = None

        # 전략 초기화
        self._init_strategy(strategy_type, strategy_config)

        # Ollama 분석기 초기화 (선택적)
        if use_ollama:
            self._init_ollama()

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

    def _init_strategy(self, strategy_type: str, config: Dict = None):
        """전략 초기화"""
        if strategy_type == STRATEGY_VOLATILITY:
            self.strategy = VolatilityBreakoutStrategy(self.api, config)
            self.log(f"전략 초기화: 변동성 돌파 (K={self.strategy.config.get('k_value', 0.5)})")
        elif strategy_type == STRATEGY_CREWAI:
            # CrewAI 멀티 에이전트 전략
            self.strategy = CrewAIStrategy(self.api, config)
            self.log("전략 초기화: Ollama + CrewAI 멀티 에이전트")
        elif strategy_type == STRATEGY_COMBINED:
            # 복합 전략: 두 전략 모두 사용
            self.momentum_strategy = MomentumVolumeStrategy(self.api, config)
            self.volatility_strategy = VolatilityBreakoutStrategy(self.api, config)
            self.strategy = self.momentum_strategy  # 기본은 모멘텀
            self.log("전략 초기화: 복합 전략 (모멘텀 + 변동성 돌파)")
        else:
            # 기본: 모멘텀 전략
            self.strategy = MomentumVolumeStrategy(self.api, config)
            self.log("전략 초기화: 모멘텀 + 거래량")

    def _init_ollama(self):
        """Ollama 분석기 초기화"""
        try:
            from analyzers.ollama_analyzer import OllamaAnalyzer
            self.ollama_analyzer = OllamaAnalyzer()
            self.log("Ollama AI 분석기 초기화 완료")
        except Exception as e:
            self.log(f"Ollama 초기화 실패: {e}", "WARNING")
            self.ollama_analyzer = None

    def set_strategy(self, strategy_type: str, config: Dict = None):
        """전략 변경"""
        self.strategy_type = strategy_type
        self._init_strategy(strategy_type, config)

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

        strategy_name = {
            STRATEGY_MOMENTUM: '모멘텀+거래량',
            STRATEGY_VOLATILITY: '변동성 돌파',
            STRATEGY_COMBINED: '복합 전략'
        }.get(self.strategy_type, self.strategy_type)

        self.log(f"자동매매 시작 (전략: {strategy_name}, 체크 간격: {check_interval}초)")

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
                self.log(f"전략 실행 중... ({self.strategy_type})")

                if self.strategy_type == STRATEGY_COMBINED:
                    result = self._run_combined_strategy()
                else:
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

    def _run_combined_strategy(self) -> Dict:
        """복합 전략 실행"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'strategy': 'combined',
            'sells': [],
            'buys': [],
            'errors': []
        }

        now = datetime.now()
        current_time = (now.hour, now.minute)

        # 시간대별 전략 선택
        # 09:05 ~ 10:00: 변동성 돌파 (장 초반 돌파 매매)
        # 10:00 ~ 14:30: 모멘텀 (추세 추종)
        # 14:30 ~ 15:20: 변동성 돌파 청산 + 모멘텀 매도 검사

        if current_time < (10, 0):
            # 장 초반: 변동성 돌파
            self.log("복합 전략: 변동성 돌파 모드")
            vol_result = self.volatility_strategy.run_once()
            result['sells'].extend(vol_result.get('sells', []))
            result['buys'].extend(vol_result.get('buys', []))
            result['errors'].extend(vol_result.get('errors', []))

        elif current_time < (14, 30):
            # 장 중반: 모멘텀 전략
            self.log("복합 전략: 모멘텀 모드")
            mom_result = self.momentum_strategy.run_once()
            result['sells'].extend(mom_result.get('sells', []))
            result['buys'].extend(mom_result.get('buys', []))
            result['errors'].extend(mom_result.get('errors', []))

        else:
            # 장 마감 전: 청산
            self.log("복합 전략: 청산 모드")
            # 변동성 돌파 청산
            vol_result = self.volatility_strategy.run_once()
            result['sells'].extend(vol_result.get('sells', []))
            result['errors'].extend(vol_result.get('errors', []))

            # 모멘텀 매도 검사만
            mom_result = self.momentum_strategy.run_once()
            result['sells'].extend(mom_result.get('sells', []))
            result['errors'].extend(mom_result.get('errors', []))

        return result

    def run_once_now(self) -> Dict:
        """즉시 1회 실행"""
        self.log("전략 즉시 실행")

        if self.strategy_type == STRATEGY_COMBINED:
            return self._run_combined_strategy()
        return self.strategy.run_once()

    def get_status(self) -> Dict:
        """현재 상태 조회"""
        strategy_status = self.strategy.get_status()

        status = {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'is_market_open': self.is_market_open(),
            'check_interval': self.check_interval,
            'strategy_type': self.strategy_type,
            'use_ollama': self.use_ollama,
            'strategy_status': strategy_status,
            'recent_logs': self.logs[-20:]
        }

        # 복합 전략인 경우 추가 정보
        if self.strategy_type == STRATEGY_COMBINED:
            status['momentum_config'] = self.momentum_strategy.config
            status['volatility_config'] = self.volatility_strategy.config

        return status

    def get_config(self) -> Dict:
        """현재 설정 조회"""
        return self.strategy.config

    def update_config(self, new_config: Dict):
        """설정 업데이트"""
        self.strategy.config.update(new_config)
        self.log(f"설정 업데이트: {new_config}")

    def get_trade_history(self) -> list:
        """거래 내역 조회"""
        history = self.strategy.trade_history

        # 복합 전략인 경우 두 전략의 거래 내역 합치기
        if self.strategy_type == STRATEGY_COMBINED:
            history = (
                self.momentum_strategy.trade_history +
                self.volatility_strategy.trade_history
            )
            # 시간순 정렬
            history.sort(key=lambda x: x.get('timestamp', ''))

        return history


class AutoTraderManager:
    """자동매매 관리자 (UI 연동용)"""

    def __init__(self, api):
        self.api = api
        self.trader: Optional[AutoTrader] = None

    def create_trader(
        self,
        strategy_type: str = STRATEGY_MOMENTUM,
        config: Dict = None,
        use_ollama: bool = False
    ) -> AutoTrader:
        """
        트레이더 생성

        Args:
            strategy_type: 전략 타입 ('momentum', 'volatility', 'combined')
            config: 전략 설정
            use_ollama: Ollama AI 분석 사용 여부
        """
        self.trader = AutoTrader(
            self.api,
            strategy_type=strategy_type,
            strategy_config=config,
            use_ollama=use_ollama
        )
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

    def set_strategy(self, strategy_type: str, config: Dict = None):
        """전략 변경"""
        if self.trader:
            was_running = self.trader.is_running
            if was_running:
                self.trader.stop()

            self.trader.set_strategy(strategy_type, config)

            if was_running:
                self.trader.start(self.trader.check_interval)
        else:
            self.create_trader(strategy_type, config)

    def get_status(self) -> Dict:
        """상태 조회"""
        if self.trader:
            return self.trader.get_status()
        return {'is_running': False, 'message': '트레이더가 초기화되지 않았습니다.'}

    def get_available_strategies(self) -> Dict:
        """사용 가능한 전략 목록"""
        return {
            STRATEGY_MOMENTUM: {
                'name': '모멘텀 + 거래량',
                'description': '거래량 급등 + 이동평균선 돌파 종목 매매',
                'holding_period': '1-3일'
            },
            STRATEGY_VOLATILITY: {
                'name': '변동성 돌파',
                'description': '래리 윌리엄스 전략, 당일 청산',
                'holding_period': '당일'
            },
            STRATEGY_COMBINED: {
                'name': '복합 전략',
                'description': '시간대별 전략 자동 전환',
                'holding_period': '혼합'
            },
            STRATEGY_CREWAI: {
                'name': 'Ollama + CrewAI 멀티 에이전트',
                'description': 'AI 기반 기술적 분석 + 뉴스 감성 분석 + 종합 판단',
                'holding_period': '1-3일',
                'features': ['거래량 상위 50종목 스캔', '보유 종목 필수 분석', '뉴스 감성 분석']
            }
        }
