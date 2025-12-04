#!/usr/bin/env python3
"""
글로벌 주식 스크리너 - 국내/해외 통합
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

logger = logging.getLogger('ai_trading')


class GlobalStockScreener:
    """글로벌 주식 스크리닝 클래스"""
    
    def __init__(self, kis_api):
        """
        Args:
            kis_api: KisAPIEnhanced 인스턴스
        """
        self.kis_api = kis_api
        # 해외주식 API 초기화
        self.kis_api.initialize_overseas_api()
        
        # 스크리닝 기준
        self.SCREENING_CRITERIA = {
            'domestic': {
                'min_volume': 100000,      # 최소 거래량
                'min_price': 1000,         # 최소 주가
                'max_price': 500000,       # 최대 주가
                'min_market_cap': 100,     # 최소 시가총액 (억원)
            },
            'overseas': {
                'min_volume': 100000,      # 최소 거래량
                'min_price': 5,            # 최소 주가 (USD)
                'max_price': 5000,         # 최대 주가 (USD)
                'min_market_cap': 1000,    # 최소 시가총액 (백만 달러)
            }
        }
    
    async def screen_global_stocks(self, markets: List[str] = ['KOSPI', 'KOSDAQ', 'NASDAQ', 'NYSE']) -> Dict:
        """글로벌 주식 스크리닝
        
        Args:
            markets: 스크리닝할 시장 리스트
            
        Returns:
            시장별 추천 종목 딕셔너리
        """
        results = {
            'domestic': [],
            'overseas': []
        }
        
        # 국내 주식 스크리닝
        domestic_markets = [m for m in markets if m in ['KOSPI', 'KOSDAQ']]
        if domestic_markets:
            logger.info(f"Screening domestic stocks: {domestic_markets}")
            domestic_stocks = await self._screen_domestic_stocks()
            results['domestic'] = domestic_stocks
        
        # 해외 주식 스크리닝  
        overseas_markets = [m for m in markets if m in ['NASDAQ', 'NYSE', 'AMEX']]
        if overseas_markets:
            logger.info(f"Screening overseas stocks: {overseas_markets}")
            overseas_stocks = await self._screen_overseas_stocks(overseas_markets)
            results['overseas'] = overseas_stocks
        
        return results
    
    async def _screen_domestic_stocks(self) -> List[Dict]:
        """국내 주식 스크리닝"""
        candidates = []
        
        try:
            # 거래량 상위 종목 조회
            top_volume = self.kis_api.get_volume_rank(market="ALL")
            if not top_volume:
                return []
            
            criteria = self.SCREENING_CRITERIA['domestic']
            
            for stock in top_volume[:50]:  # 상위 50개 검토
                try:
                    # 스크리닝 기준 체크
                    price = stock.get('price', 0)
                    volume = stock.get('volume', 0)
                    market_cap = stock.get('market_cap', 0) / 100000000  # 억원
                    
                    if (criteria['min_price'] <= price <= criteria['max_price'] and
                        volume >= criteria['min_volume'] and
                        market_cap >= criteria['min_market_cap']):
                        
                        # 기술적 분석 점수 계산
                        score = await self._calculate_technical_score_domestic(stock['code'])
                        
                        if score > 0.6:  # 60% 이상 점수
                            candidates.append({
                                'market': 'KR',
                                'exchange': stock.get('market_type', 'KOSPI'),
                                'code': stock['code'],
                                'name': stock['name'],
                                'price': price,
                                'change_rate': stock.get('change_rate', 0),
                                'volume': volume,
                                'market_cap': market_cap,
                                'score': score,
                                'currency': 'KRW'
                            })
                
                except Exception as e:
                    logger.error(f"Error screening {stock.get('code', 'UNKNOWN')}: {e}")
            
            # 점수 기준 정렬
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error in domestic screening: {e}")
        
        return candidates[:100]  # 상위 100개
    
    async def _screen_overseas_stocks(self, markets: List[str]) -> List[Dict]:
        """해외 주식 스크리닝 - API 호출 최소화"""
        candidates = []
        
        # 인기 종목 리스트 (API 호출 줄이기 위해 선별된 종목)
        popular_stocks = {
            'NASDAQ': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA'],
            'NYSE': ['JPM', 'JNJ', 'WMT', 'BAC', 'XOM', 'HD', 'PG', 'V']
        }
        
        try:
            import asyncio
            for market in markets:
                exchange_code = 'NASD' if market == 'NASDAQ' else 'NYSE'
                stocks = popular_stocks.get(market, [])
                
                # API 호출 간격을 위한 카운터
                api_call_count = 0
                
                for symbol in stocks:
                    try:
                        # API 호출 간격 조정 (500 에러 방지)
                        if api_call_count > 0:
                            await asyncio.sleep(5)  # 5초 대기로 증가
                        
                        # 현재가 조회
                        price_info = self.kis_api.overseas.get_overseas_price(exchange_code, symbol)
                        api_call_count += 1
                        
                        if not price_info:
                            continue
                        
                        criteria = self.SCREENING_CRITERIA['overseas']
                        
                        # 스크리닝 기준 체크
                        price = price_info['current_price']
                        volume = price_info['volume']
                        
                        if (criteria['min_price'] <= price <= criteria['max_price'] and
                            volume >= criteria['min_volume']):
                            
                            # 간소화된 점수 계산 (추가 API 호출 없이)
                            # 변화율과 거래량 기반 점수
                            change_rate = abs(price_info['change_rate'])
                            volume_score = min(volume / 1000000, 1.0)  # 거래량 정규화
                            price_momentum = change_rate / 100  # 변화율 정규화
                            score = (volume_score * 0.5) + (price_momentum * 0.5)
                            
                            if score > 0.3:  # 기준 완화
                                candidates.append({
                                    'market': 'US',
                                    'exchange': market,
                                    'code': symbol,
                                    'name': symbol,  # 실제로는 종목명 조회 필요
                                    'price': price,
                                    'change_rate': price_info['change_rate'],
                                    'volume': volume,
                                    'market_cap': 0,  # 시가총액 계산 필요
                                    'score': score,
                                    'currency': 'USD'
                                })
                    
                    except Exception as e:
                        logger.error(f"Error screening {symbol}: {e}")
            
            # 점수 기준 정렬
            candidates.sort(key=lambda x: x['score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error in overseas screening: {e}")
        
        return candidates[:100]
    
    async def _calculate_technical_score_domestic(self, stock_code: str) -> float:
        """국내 주식 기술적 분석 점수 계산"""
        try:
            # 일봉 데이터 조회
            daily_data = self.kis_api.get_daily_price(stock_code, count=60)
            if not daily_data or len(daily_data.get('output', [])) < 20:
                return 0.0
            
            # DataFrame 변환
            df_data = []
            for item in daily_data.get('output', []):
                df_data.append({
                    'date': item['stck_bsop_date'],
                    'close': float(item['stck_clpr']),
                    'volume': int(item['acml_vol']),
                    'high': float(item['stck_hgpr']),
                    'low': float(item['stck_lwpr'])
                })
            
            df = pd.DataFrame(df_data).sort_values('date')
            
            # 기술적 지표 계산
            score = 0.0
            weights = 0.0
            
            # 1. 이동평균선 분석 (40%)
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            current_price = df['close'].iloc[-1]
            
            if current_price > ma20 and ma5 > ma20:
                score += 0.4
            weights += 0.4
            
            # 2. RSI (30%)
            rsi = self._calculate_rsi(df['close'])
            if 30 < rsi < 70:
                score += 0.3 * (1 - abs(rsi - 50) / 50)
            weights += 0.3
            
            # 3. 거래량 분석 (30%)
            vol_avg = df['volume'].rolling(20).mean().iloc[-1]
            vol_recent = df['volume'].iloc[-5:].mean()
            if vol_recent > vol_avg * 1.2:
                score += 0.3
            weights += 0.3
            
            return score / weights if weights > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating technical score for {stock_code}: {e}")
            return 0.0
    
    async def _calculate_technical_score_overseas(self, exchange: str, symbol: str) -> float:
        """해외 주식 기술적 분석 점수 계산"""
        try:
            # 일봉 데이터 조회
            daily_data = self.kis_api.overseas.get_overseas_daily_price(exchange, symbol, count=60)
            if not daily_data or len(daily_data) < 20:
                return 0.0
            
            # DataFrame 변환
            df = pd.DataFrame(daily_data).sort_values('date')
            
            # 기술적 지표 계산 (국내와 동일한 로직)
            score = 0.0
            weights = 0.0
            
            # 1. 이동평균선 분석 (40%)
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            current_price = df['close'].iloc[-1]
            
            if current_price > ma20 and ma5 > ma20:
                score += 0.4
            weights += 0.4
            
            # 2. RSI (30%)
            rsi = self._calculate_rsi(df['close'])
            if 30 < rsi < 70:
                score += 0.3 * (1 - abs(rsi - 50) / 50)
            weights += 0.3
            
            # 3. 거래량 분석 (30%)
            vol_avg = df['volume'].rolling(20).mean().iloc[-1]
            vol_recent = df['volume'].iloc[-5:].mean()
            if vol_recent > vol_avg * 1.2:
                score += 0.3
            weights += 0.3
            
            return score / weights if weights > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating technical score for {symbol}: {e}")
            return 0.0
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1]