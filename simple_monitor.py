#!/usr/bin/env python3
"""
간단한 AI 자동매매 모니터링 시스템 (필수 모듈만 사용)
프롬프트 요구사항에 따른 24시간 모니터링
"""

import asyncio
import logging
import json
import requests
import time
import threading
from datetime import datetime, timedelta
from collections import deque

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('simple_monitor')

# 모니터링 데이터 로거
monitoring_logger = logging.getLogger('monitoring')
monitoring_handler = logging.FileHandler('monitoring_data.log', encoding='utf-8')
monitoring_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
monitoring_logger.addHandler(monitoring_handler)
monitoring_logger.setLevel(logging.INFO)

class RateLimiter:
    """API 호출 제한 관리"""
    def __init__(self, max_calls=15, period=1.0):
        self.max_calls, self.period = max_calls, period
        self.calls, self.lock = deque(), threading.Lock()
    
    def wait(self):
        with self.lock:
            now = time.time()
            while self.calls and now - self.calls[0] >= self.period:
                self.calls.popleft()
            if len(self.calls) >= self.max_calls:
                time.sleep(self.period - (now - self.calls[0]))
            self.calls.append(time.time())

class KISBroker:
    """한국투자증권 API 브로커"""
    
    def __init__(self, paper_trading: bool = True):
        """초기화"""
        self.config = {
            "paper_app": "PSTP8BTWgg4loa76mISQPzb2tHvjxtrBUDID",
            "paper_sec": "rc+xPU2Ya43Z7MgdiLNknR3QWQMc9yBHj9j4WuK63/XiBvusTUcRVhi3vl8tQdup5yUbRBJJ5+AHv1o3dUgdMdX3Xw5AN09go98Z2+BMeBfF/kaDCw9jHDH1RWhjBi5grVjfBkFArbt3lrP+pFkSdeiJxEPUgx+4nZ9gog744kyo5LEq3hI=",
            "my_app": "PSCqWTEJAst52ZjLzjv78vCj0eEUix0TNOzS", 
            "my_sec": "I9iBCx+BK++QFgq6mb6KPJj/x7I0jB/8L9xl79NGoFLvVknEpIST/yWwKuyoe9rwUIwAYVDmwip1+/ety0NTTtFrTNwV6Gym5sVRRN1r3iEC+/UsMN0POLH3Ba3OhwG96EqCCk2aI1CfOKS9AHf9i1lnPucAGOxGzXOVL2FqTsEZaUchOTI=",
            "my_acct_stock": "50157423",
            "my_prod": "01"
        }
        
        self.paper_trading = paper_trading
        self.base_url = "https://openapivts.koreainvestment.com:29443" if paper_trading else "https://openapi.koreainvestment.com:9443"
        self.rate_limiter = RateLimiter(max_calls=15, period=1.0)
        
        self.access_token = None
        self.token_expires = None
        
        # 초기 토큰 발급
        self._get_access_token()
        logger.info(f"KIS 브로커 초기화 완료 - {'모의투자' if paper_trading else '실전투자'}")
    
    def _get_access_token(self):
        """액세스 토큰 발급"""
        url = f"{self.base_url}/oauth2/tokenP"
        key_prefix = "paper" if self.paper_trading else "my"
        
        body = {
            "grant_type": "client_credentials",
            "appkey": self.config[f"{key_prefix}_app"],
            "appsecret": self.config[f"{key_prefix}_sec"]
        }
        
        try:
            response = requests.post(url, headers={"content-type": "application/json"}, json=body)
            result = response.json()
            
            logger.info(f"토큰 응답 상태: {response.status_code}")
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.token_expires = datetime.now() + timedelta(hours=23)
                logger.info("✅ 액세스 토큰 발급 성공")
            elif result.get("error_code") == "EGW00133":
                logger.warning("⏰ API 요청 제한 - 1분 대기 후 재시도")
                time.sleep(60)
                return self._get_access_token()
            else:
                logger.error(f"❌ 토큰 발급 실패: {result}")
                raise Exception(f"토큰 발급 실패: {result}")
                
        except Exception as e:
            logger.error(f"토큰 발급 오류: {e}")
            raise
    
    def _get_headers(self, tr_id: str) -> dict:
        """API 헤더 생성"""
        if not self.access_token or datetime.now() >= self.token_expires:
            self._get_access_token()
        
        key_prefix = "paper" if self.paper_trading else "my"
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config[f"{key_prefix}_app"],
            "appsecret": self.config[f"{key_prefix}_sec"],
            "tr_id": tr_id,
            "custtype": "P"
        }
    
    def get_balance(self):
        """계좌 잔고 조회"""
        self.rate_limiter.wait()
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        tr_id = "VTTC8434R" if self.paper_trading else "TTTC8434R"
        
        headers = self._get_headers(tr_id)
        params = {
            "CANO": self.config["my_acct_stock"],
            "ACNT_PRDT_CD": self.config["my_prod"],
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            result = response.json()
            
            if result.get('rt_cd') == '0':
                return result
            else:
                logger.error(f"계좌 조회 실패: {result.get('msg1')}")
                return None
        except Exception as e:
            logger.error(f"계좌 조회 오류: {e}")
            return None

class SimpleMonitor:
    """간단한 모니터링 시스템"""
    
    def __init__(self, paper_trading: bool = True):
        """초기화"""
        logger.info("=== 간단한 AI 자동매매 모니터링 시스템 초기화 ===")
        
        self.broker = KISBroker(paper_trading)
        
        self.portfolio = {}
        self.cash_balance = 0
        self.total_value = 0
        self.is_running = False
        
        logger.info("간단한 모니터링 시스템 초기화 완료")
    
    def log_monitoring_data(self, event_type: str, data: dict):
        """모니터링 데이터 JSON 로그"""
        monitoring_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        monitoring_logger.info(json.dumps(monitoring_data, ensure_ascii=False))
    
    async def update_portfolio(self):
        """포트폴리오 상태 업데이트"""
        try:
            balance_info = self.broker.get_balance()
            
            if balance_info and balance_info.get('rt_cd') == '0':
                # 현금 잔고
                output2 = balance_info.get('output2', [{}])
                if output2:
                    self.cash_balance = float(output2[0].get('dnca_tot_amt', 0))
                    self.total_value = float(output2[0].get('tot_evlu_amt', 0))
                
                # 보유 종목
                output1 = balance_info.get('output1', [])
                self.portfolio = {}
                
                for holding in output1:
                    if int(holding.get('hldg_qty', 0)) > 0:
                        stock_code = holding['pdno']
                        self.portfolio[stock_code] = {
                            'name': holding['prdt_name'],
                            'quantity': int(holding['hldg_qty']),
                            'avg_price': float(holding['pchs_avg_pric']),
                            'current_price': float(holding['prpr']),
                            'eval_amount': float(holding['evlu_amt']),
                            'profit_rate': float(holding['evlu_pfls_rt'])
                        }
                
                logger.info("📊 포트폴리오 상태 업데이트 완료")
                logger.info(f"   💰 총 자산: {self.total_value:,.0f}원")
                logger.info(f"   💵 현금: {self.cash_balance:,.0f}원")
                logger.info(f"   📈 보유 종목: {len(self.portfolio)}개")
                
                for code, info in self.portfolio.items():
                    logger.info(f"   - {info['name']}: {info['quantity']}주, 수익률 {info['profit_rate']:.2f}%")
                
                # 모니터링 데이터 로깅
                self.log_monitoring_data("portfolio_update", {
                    "total_value": self.total_value,
                    "cash_balance": self.cash_balance,
                    "holdings_count": len(self.portfolio),
                    "portfolio": self.portfolio
                })
                
        except Exception as e:
            logger.error(f"포트폴리오 업데이트 오류: {e}")
            self.log_monitoring_data("error", {
                "error_type": "portfolio_update_failed",
                "error_message": str(e)
            })
    
    def is_market_open(self) -> bool:
        """장 개장 여부 확인"""
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour
        minute = now.minute
        
        # 평일 09:00 ~ 15:30
        if weekday < 5 and (9 <= hour < 15 or (hour == 15 and minute <= 30)):
            return True
        
        return False
    
    async def run(self):
        """메인 실행 루프"""
        logger.info("🚀 간단한 모니터링 시스템 시작")
        
        try:
            await self.update_portfolio()
            self.is_running = True
            
            while self.is_running:
                try:
                    current_time = datetime.now()
                    
                    if self.is_market_open():
                        logger.info(f"📊 장중 모니터링 - {current_time.strftime('%H:%M:%S')}")
                        
                        # 포트폴리오 업데이트
                        await self.update_portfolio()
                        
                        # 5분 대기
                        await asyncio.sleep(300)
                    else:
                        logger.info(f"😴 장외시간 대기 - {current_time.strftime('%H:%M:%S')}")
                        
                        # 간단한 상태 체크
                        await self.update_portfolio()
                        
                        # 30분 대기
                        await asyncio.sleep(1800)
                
                except KeyboardInterrupt:
                    logger.info("사용자 중지 요청")
                    break
                except Exception as e:
                    logger.error(f"메인 루프 오류: {e}")
                    self.log_monitoring_data("error", {
                        "error_type": "main_loop_error",
                        "error_message": str(e)
                    })
                    await asyncio.sleep(300)  # 5분 후 재시도
        
        finally:
            self.is_running = False
            logger.info("간단한 모니터링 시스템 종료")

def main():
    """메인 함수"""
    print(f"""
╔══════════════════════════════════════════════════╗
║           🤖 간단한 AI 자동매매 모니터링           ║
║                                                  ║
║  모드: 모의투자 (Demo)                            ║
║  시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    ║
║  프롬프트 요구사항에 따른 24시간 모니터링          ║
╚══════════════════════════════════════════════════╝
    """)
    
    try:
        # 모의투자 모드로 자동 초기화
        monitor = SimpleMonitor(paper_trading=True)
        
        print("✅ 시스템 초기화 완료")
        print("🚀 프롬프트 요구사항: 24시간 실제 데모 버전 모니터링 시작")
        print("📊 모니터링 중 오류 발생시 즉시 수정 후 재시작")
        print("📧 주요 이슈는 dsangwoo@gmail.com으로 알림 예정")
        print("⚠️  모니터링 중지: Ctrl+C")
        print("=" * 60)
        
        # 24시간 모니터링 시작
        asyncio.run(monitor.run())
        
    except KeyboardInterrupt:
        print("\n⏹️  사용자에 의해 모니터링이 중지되었습니다.")
    except Exception as e:
        print(f"\n❌ 모니터링 중 오류 발생: {e}")
        logger.error(f"모니터링 오류: {e}")
        print("프롬프트 요구사항에 따라 오류를 수정하고 재시작이 필요합니다.")

if __name__ == "__main__":
    main()