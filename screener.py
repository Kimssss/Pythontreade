"""
종목 스크리너 모듈
- 거래량 급등주 탐색
- 기술적 지표 기반 종목 선별
- 우량주 필터링
"""

import time
from typing import List, Dict, Optional
from kis_api import KisAPI
from strategy import TradingStrategy, TechnicalAnalysis


class StockScreener:
    """종목 스크리너 클래스"""

    # 기본 우량주 리스트 (시가총액 상위 + 거래량 충분)
    DEFAULT_WATCHLIST = [
        {"code": "005930", "name": "삼성전자"},
        {"code": "000660", "name": "SK하이닉스"},
        {"code": "373220", "name": "LG에너지솔루션"},
        {"code": "207940", "name": "삼성바이오로직스"},
        {"code": "005380", "name": "현대차"},
        {"code": "006400", "name": "삼성SDI"},
        {"code": "051910", "name": "LG화학"},
        {"code": "035420", "name": "NAVER"},
        {"code": "000270", "name": "기아"},
        {"code": "005490", "name": "POSCO홀딩스"},
        {"code": "035720", "name": "카카오"},
        {"code": "068270", "name": "셀트리온"},
        {"code": "028260", "name": "삼성물산"},
        {"code": "105560", "name": "KB금융"},
        {"code": "055550", "name": "신한지주"},
        {"code": "012330", "name": "현대모비스"},
        {"code": "066570", "name": "LG전자"},
        {"code": "003670", "name": "포스코퓨처엠"},
        {"code": "047050", "name": "포스코인터내셔널"},
        {"code": "096770", "name": "SK이노베이션"},
    ]

    def __init__(self, api: KisAPI, style: str = "neutral"):
        """
        Args:
            api: KisAPI 인스턴스
            style: 투자 성향
        """
        self.api = api
        self.strategy = TradingStrategy(style=style)
        self.ta = TechnicalAnalysis()

    def get_volume_surge_stocks(self, limit: int = 10) -> List[Dict]:
        """
        거래량 급등주 조회

        Args:
            limit: 조회 개수

        Returns:
            거래량 급등 종목 리스트
        """
        print("거래량 급등주를 조회합니다...")
        result = self.api.get_volume_rank()

        if not result or result.get('rt_cd') != '0':
            print("거래량 순위 조회 실패, 기본 종목 리스트 사용")
            return self.DEFAULT_WATCHLIST[:limit]

        stocks = []
        output = result.get('output', [])

        for item in output[:limit]:
            stocks.append({
                "code": item.get('mksc_shrn_iscd', ''),
                "name": item.get('hts_kor_isnm', ''),
                "price": int(item.get('stck_prpr', 0)),
                "change_rate": float(item.get('prdy_ctrt', 0)),
                "volume": int(item.get('acml_vol', 0)),
                "volume_rate": float(item.get('vol_inrt', 0))
            })

        return stocks

    def get_watchlist_with_analysis(self) -> List[Dict]:
        """
        기본 관심 종목 + 기술적 분석

        Returns:
            분석된 종목 리스트
        """
        print("관심 종목 분석 중...")
        analyzed_stocks = []

        for stock in self.DEFAULT_WATCHLIST:
            try:
                code = stock["code"]
                name = stock["name"]

                # 현재가 조회
                price_data = self.api.get_stock_price(code)
                if not price_data or price_data.get('rt_cd') != '0':
                    continue

                current_price = int(price_data['output'].get('stck_prpr', 0))
                change_rate = float(price_data['output'].get('prdy_ctrt', 0))

                # 일봉 데이터 조회
                daily_data = self.api.get_daily_price(code)
                if not daily_data or daily_data.get('rt_cd') != '0':
                    continue

                # 종가 리스트 추출
                prices = []
                for item in daily_data.get('output2', [])[:30]:
                    close = item.get('stck_clpr')
                    if close:
                        prices.append(int(close))

                if len(prices) < 20:
                    continue

                # 기술적 분석
                analysis = self.strategy.analyze(prices, current_price)

                analyzed_stocks.append({
                    "code": code,
                    "name": name,
                    "price": current_price,
                    "change_rate": change_rate,
                    "analysis": analysis,
                    "score": analysis["score"],
                    "recommendation": analysis["recommendation"]
                })

                print(f"  {name}({code}): {analysis['recommendation']} (점수: {analysis['score']})")

                # API 호출 제한 방지
                time.sleep(0.2)

            except Exception as e:
                print(f"  {stock['name']} 분석 실패: {e}")
                continue

        # 점수순 정렬
        analyzed_stocks.sort(key=lambda x: x["score"], reverse=True)
        return analyzed_stocks

    def screen_buy_candidates(self, max_candidates: int = 5) -> List[Dict]:
        """
        매수 후보 종목 스크리닝

        Args:
            max_candidates: 최대 후보 수

        Returns:
            매수 추천 종목 리스트
        """
        print("\n=== 매수 후보 스크리닝 시작 ===")

        # 1단계: 관심 종목 분석
        analyzed = self.get_watchlist_with_analysis()

        # 2단계: 매수 신호가 있는 종목 필터링
        buy_candidates = []
        for stock in analyzed:
            if self.strategy.should_buy(stock["analysis"]):
                buy_candidates.append(stock)

        print(f"\n매수 신호 종목: {len(buy_candidates)}개")

        # 3단계: 거래량 급등주 확인 (추가 점수)
        try:
            volume_stocks = self.get_volume_surge_stocks(20)
            volume_codes = {s["code"] for s in volume_stocks}

            for candidate in buy_candidates:
                if candidate["code"] in volume_codes:
                    candidate["score"] += 1
                    candidate["analysis"]["signals"].append("거래량 급등")
                    print(f"  {candidate['name']}: 거래량 급등 추가")
        except Exception as e:
            print(f"거래량 급등주 확인 실패: {e}")

        # 점수순 재정렬
        buy_candidates.sort(key=lambda x: x["score"], reverse=True)

        # 상위 N개 반환
        result = buy_candidates[:max_candidates]

        print(f"\n=== 최종 매수 후보 {len(result)}개 ===")
        for i, stock in enumerate(result, 1):
            print(f"{i}. {stock['name']}({stock['code']})")
            print(f"   현재가: {stock['price']:,}원 ({stock['change_rate']:+.2f}%)")
            print(f"   추천: {stock['recommendation']} (점수: {stock['score']})")
            print(f"   시그널: {', '.join(stock['analysis']['signals'][:3])}")

        return result

    def analyze_single_stock(self, stock_code: str) -> Optional[Dict]:
        """
        단일 종목 상세 분석

        Args:
            stock_code: 종목 코드

        Returns:
            분석 결과
        """
        try:
            # 현재가 조회
            price_data = self.api.get_stock_price(stock_code)
            if not price_data or price_data.get('rt_cd') != '0':
                return None

            output = price_data['output']
            current_price = int(output.get('stck_prpr', 0))
            stock_name = output.get('hts_kor_isnm', stock_code)

            # 일봉 데이터
            daily_data = self.api.get_daily_price(stock_code)
            if not daily_data or daily_data.get('rt_cd') != '0':
                return None

            prices = []
            for item in daily_data.get('output2', [])[:50]:
                close = item.get('stck_clpr')
                if close:
                    prices.append(int(close))

            if len(prices) < 20:
                return None

            # 분석
            analysis = self.strategy.analyze(prices, current_price)

            return {
                "code": stock_code,
                "name": stock_name,
                "price": current_price,
                "change_rate": float(output.get('prdy_ctrt', 0)),
                "analysis": analysis,
                "recommendation": analysis["recommendation"],
                "score": analysis["score"]
            }

        except Exception as e:
            print(f"종목 분석 실패: {e}")
            return None


if __name__ == "__main__":
    from config import Config

    # 테스트
    print("=== 종목 스크리너 테스트 ===\n")

    account_info = Config.get_account_info('demo')
    api = KisAPI(
        account_info['appkey'],
        account_info['appsecret'],
        account_info['account'],
        is_real=False
    )

    if api.get_access_token():
        screener = StockScreener(api, style="neutral")

        # 매수 후보 스크리닝
        candidates = screener.screen_buy_candidates(max_candidates=5)
    else:
        print("API 연결 실패")
