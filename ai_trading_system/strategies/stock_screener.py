"""
주식 스크리닝 및 팩터 분석 모듈
블로그 분석 기반 종목 선정 로직 구현
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import asyncio
import logging
from datetime import datetime, timedelta

try:
    from ..utils.kis_api import KisAPIEnhanced
    from ..config.settings import SCREENING_CONFIG, FACTOR_CONFIG
except ImportError:
    from utils.kis_api import KisAPIEnhanced
    from config.settings import SCREENING_CONFIG, FACTOR_CONFIG

logger = logging.getLogger('ai_trading.screener')


class StockScreener:
    """주식 스크리닝 클래스"""
    
    def __init__(self, kis_api: KisAPIEnhanced):
        self.kis_api = kis_api
        self.screening_config = SCREENING_CONFIG
        self.factor_config = FACTOR_CONFIG
        
    async def get_market_stocks(self) -> List[Dict]:
        """시장 전체 종목 조회"""
        try:
            # 거래량 상위 종목 조회
            top_volume = self.kis_api.get_top_volume_stocks(count=100)
            
            if not top_volume or top_volume.get('rt_cd') != '0':
                logger.error("Failed to get top volume stocks")
                return []
            
            stocks = []
            for item in top_volume.get('output', []):
                stock_info = {
                    'code': item.get('mksc_shrn_iscd'),
                    'name': item.get('hts_kor_isnm'),
                    'price': float(item.get('stck_prpr', 0)),
                    'volume': int(item.get('acml_vol', 0)),
                    'change_rate': float(item.get('prdy_ctrt', 0)),
                    'market_cap': float(item.get('stck_avls', 0)) / 100000000  # 억원 단위
                }
                stocks.append(stock_info)
                
            return stocks
            
        except Exception as e:
            logger.error(f"Error getting market stocks: {e}")
            return []
    
    def calculate_factor_scores(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """팩터 점수 계산"""
        result = stock_data.copy()
        
        # 가치 팩터 (낮을수록 좋음)
        if 'PER' in result.columns:
            result['value_score'] = result['PER'].rank(pct=True, ascending=True) * 0.3
        if 'PBR' in result.columns:
            result['value_score'] += result['PBR'].rank(pct=True, ascending=True) * 0.3
        if 'PCR' in result.columns:
            result['value_score'] += result['PCR'].rank(pct=True, ascending=True) * 0.2
        if 'PSR' in result.columns:
            result['value_score'] += result['PSR'].rank(pct=True, ascending=True) * 0.2
        
        # 품질 팩터 (높을수록 좋음)
        if 'ROE' in result.columns:
            result['quality_score'] = result['ROE'].rank(pct=True) * 0.3
        if 'ROA' in result.columns:
            result['quality_score'] += result['ROA'].rank(pct=True) * 0.3
        if 'DebtRatio' in result.columns:
            result['quality_score'] += result['DebtRatio'].rank(pct=True, ascending=True) * 0.2
        if 'InterestCoverage' in result.columns:
            result['quality_score'] += result['InterestCoverage'].rank(pct=True) * 0.2
        
        # 모멘텀 팩터
        if 'Returns_1M' in result.columns:
            result['momentum_score'] = result['Returns_1M'].rank(pct=True) * 0.4
        if 'Returns_3M' in result.columns:
            result['momentum_score'] += result['Returns_3M'].rank(pct=True) * 0.3
        if 'Returns_6M' in result.columns:
            result['momentum_score'] += result['Returns_6M'].rank(pct=True) * 0.3
        
        # 성장 팩터
        if 'EPS_Growth' in result.columns:
            result['growth_score'] = result['EPS_Growth'].rank(pct=True) * 0.4
        if 'Revenue_Growth' in result.columns:
            result['growth_score'] += result['Revenue_Growth'].rank(pct=True) * 0.4
        if 'FCF_Growth' in result.columns:
            result['growth_score'] += result['FCF_Growth'].rank(pct=True) * 0.2
        
        # 종합 점수 계산
        weights = self.factor_config['weights']
        result['total_score'] = 0
        
        if 'value_score' in result.columns:
            result['total_score'] += result['value_score'] * weights['value']
        if 'quality_score' in result.columns:
            result['total_score'] += result['quality_score'] * weights['quality']
        if 'momentum_score' in result.columns:
            result['total_score'] += result['momentum_score'] * weights['momentum']
        if 'growth_score' in result.columns:
            result['total_score'] += result['growth_score'] * weights['growth']
        
        return result
    
    async def screen_stocks(self, market_condition: str = 'normal') -> List[Dict]:
        """주식 스크리닝 실행
        
        Args:
            market_condition: 시장 상황 ('bull', 'bear', 'normal')
        
        Returns:
            스크리닝된 종목 리스트
        """
        # 1. 시장 전체 종목 조회
        stocks = await self.get_market_stocks()
        if not stocks:
            return []
        
        df = pd.DataFrame(stocks)
        
        # 2. 기본 필터링
        # 최소 시가총액
        if 'market_cap' in df.columns:
            df = df[df['market_cap'] >= self.screening_config['min_market_cap']]
        
        # 최소 거래량
        if 'volume' in df.columns:
            df = df[df['volume'] >= self.screening_config['min_volume']]
        
        # 3. 재무 데이터 추가 (실제 구현시 별도 API 필요)
        # 여기서는 시뮬레이션을 위한 더미 데이터 추가
        df = self._add_dummy_financial_data(df)
        
        # 4. 팩터 점수 계산
        df = self.calculate_factor_scores(df)
        
        # 5. 시장 상황별 가중치 조정
        df = self._adjust_scores_by_market(df, market_condition)
        
        # 6. 상위 종목 선택
        df = df.nlargest(self.screening_config['top_n_stocks'], 'total_score')
        
        # 7. 결과 포맷팅
        selected_stocks = []
        for _, row in df.iterrows():
            stock = {
                'code': row['code'],
                'name': row['name'],
                'price': row['price'],
                'volume': row['volume'],
                'change_rate': row['change_rate'],
                'total_score': row['total_score'],
                'value_score': row.get('value_score', 0),
                'quality_score': row.get('quality_score', 0),
                'momentum_score': row.get('momentum_score', 0),
                'growth_score': row.get('growth_score', 0),
                'recommendation': self._get_recommendation(row['total_score'])
            }
            selected_stocks.append(stock)
        
        logger.info(f"Screened {len(selected_stocks)} stocks")
        return selected_stocks
    
    def _add_dummy_financial_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """더미 재무 데이터 추가 (실제 구현시 실제 데이터 사용)"""
        np.random.seed(42)
        n = len(df)
        
        # 가치 지표
        df['PER'] = np.random.uniform(5, 30, n)
        df['PBR'] = np.random.uniform(0.5, 3, n)
        df['PCR'] = np.random.uniform(2, 20, n)
        df['PSR'] = np.random.uniform(0.3, 5, n)
        
        # 품질 지표
        df['ROE'] = np.random.uniform(5, 25, n)
        df['ROA'] = np.random.uniform(2, 15, n)
        df['DebtRatio'] = np.random.uniform(20, 80, n)
        df['InterestCoverage'] = np.random.uniform(1, 10, n)
        
        # 모멘텀 지표
        df['Returns_1M'] = np.random.uniform(-10, 20, n)
        df['Returns_3M'] = np.random.uniform(-15, 30, n)
        df['Returns_6M'] = np.random.uniform(-20, 50, n)
        
        # 성장 지표
        df['EPS_Growth'] = np.random.uniform(-10, 30, n)
        df['Revenue_Growth'] = np.random.uniform(-5, 25, n)
        df['FCF_Growth'] = np.random.uniform(-15, 35, n)
        
        return df
    
    def _adjust_scores_by_market(self, df: pd.DataFrame, market_condition: str) -> pd.DataFrame:
        """시장 상황별 점수 조정"""
        if market_condition == 'bull':
            # 상승장: 모멘텀과 성장 중시
            if 'momentum_score' in df.columns:
                df['total_score'] *= 1.2
            if 'growth_score' in df.columns:
                df['total_score'] *= 1.1
                
        elif market_condition == 'bear':
            # 하락장: 가치와 품질 중시
            if 'value_score' in df.columns:
                df['total_score'] *= 1.2
            if 'quality_score' in df.columns:
                df['total_score'] *= 1.3
                
        return df
    
    def _get_recommendation(self, score: float) -> str:
        """점수 기반 추천 등급"""
        if score >= 0.8:
            return "Strong Buy"
        elif score >= 0.6:
            return "Buy"
        elif score >= 0.4:
            return "Hold"
        elif score >= 0.2:
            return "Sell"
        else:
            return "Strong Sell"
    
    async def get_stock_details(self, stock_code: str) -> Dict:
        """개별 종목 상세 정보 조회"""
        try:
            # 현재가 정보
            price_info = self.kis_api.get_stock_price(stock_code)
            if not price_info or price_info.get('rt_cd') != '0':
                return None
            
            output = price_info.get('output', {})
            
            # 일봉 데이터
            daily_data = self.kis_api.get_daily_price(stock_code, count=30)
            
            # 호가 정보
            orderbook = self.kis_api.get_orderbook(stock_code)
            
            details = {
                'code': stock_code,
                'name': output.get('hts_kor_isnm', ''),
                'current_price': float(output.get('stck_prpr', 0)),
                'change_rate': float(output.get('prdy_ctrt', 0)),
                'volume': int(output.get('acml_vol', 0)),
                'high': float(output.get('stck_hgpr', 0)),
                'low': float(output.get('stck_lwpr', 0)),
                'open': float(output.get('stck_oprc', 0)),
                'market_cap': float(output.get('hts_avls', 0)) / 100000000,
                'per': float(output.get('per', 0)),
                'pbr': float(output.get('pbr', 0)),
                'daily_data': daily_data,
                'orderbook': orderbook
            }
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting stock details for {stock_code}: {e}")
            return None