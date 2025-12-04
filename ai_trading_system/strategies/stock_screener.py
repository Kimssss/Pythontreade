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
            top_volume = self.kis_api.get_volume_rank(market="ALL")
            
            # API 응답 구조 디버깅
            logger.info(f"API 응답: {top_volume}")
            
            if not top_volume or top_volume.get('rt_cd') != '0':
                logger.error(f"거래량 상위 종목 조회 실패: {top_volume}")
                return []
            
            all_stocks = []
            output_data = top_volume.get('output', [])
            logger.info(f"거래량 순위 종목: {len(output_data)}개")
            
            # 1. 거래량 상위 종목 추가
            for item in output_data:
                # 시가총액 계산: 현재가 * 상장주수 (API에서 lstn_stcn 사용)
                price = float(item.get('stck_prpr', 0))
                shares = float(item.get('lstn_stcn', 0))
                market_cap = (price * shares) / 100000000 if price and shares else 0  # 억원 단위
                
                stock_info = {
                    'code': item.get('mksc_shrn_iscd'),
                    'name': item.get('hts_kor_isnm'),
                    'price': price,
                    'volume': int(item.get('acml_vol', 0)),
                    'change_rate': float(item.get('prdy_ctrt', 0)),
                    'market_cap': market_cap
                }
                logger.debug(f"Stock info: {stock_info}")
                
                # 데이터 검증: 코드와 이름이 있는지 확인
                if stock_info['code'] and stock_info['name'] and stock_info['price'] > 0:
                    all_stocks.append(stock_info)
                else:
                    logger.warning(f"비정상 데이터: {stock_info}")
                    continue
            
            # 2. 100개 종목 확보를 위해 추가 API 호출
            if len(all_stocks) < 100:
                logger.info(f"추가 종목 확보를 위한 API 호출 시작 (현재: {len(all_stocks)}개)")
                
                # 다른 조건으로 추가 종목 조회 (상승률, 시가총액 등)
                additional_calls = [
                    ("20173", "상승률"),   # 상승률 순위
                    ("20172", "시가총액"), # 시가총액 순위  
                    ("20174", "하락률"),   # 하락률 순위
                    ("20175", "변동률")    # 변동률 순위
                ]
                
                existing_codes = {stock['code'] for stock in all_stocks}
                
                for screen_code, description in additional_calls:
                    if len(all_stocks) >= 100:
                        break
                        
                    await asyncio.sleep(2)  # API 호출 간격
                    logger.info(f"{description} 순위 조회 중...")
                    
                    additional_stocks = self._get_stocks_by_screen_code(screen_code)
                    if additional_stocks:
                        new_count = 0
                        for item in additional_stocks.get('output', []):
                            if len(all_stocks) >= 100:
                                break
                                
                            stock_code = item.get('mksc_shrn_iscd')
                            if stock_code and stock_code not in existing_codes:
                                price = float(item.get('stck_prpr', 0))
                                shares = float(item.get('lstn_stcn', 0))
                                market_cap = (price * shares) / 100000000 if price and shares else 0
                                
                                stock_info = {
                                    'code': stock_code,
                                    'name': item.get('hts_kor_isnm'),
                                    'price': price,
                                    'volume': int(item.get('acml_vol', 0)),
                                    'change_rate': float(item.get('prdy_ctrt', 0)),
                                    'market_cap': market_cap
                                }
                                
                                if stock_info['code'] and stock_info['name'] and stock_info['price'] > 0:
                                    all_stocks.append(stock_info)
                                    existing_codes.add(stock_code)
                                    new_count += 1
                        
                        logger.info(f"{description} 순위에서 {new_count}개 추가, 총 {len(all_stocks)}개")
                    else:
                        logger.warning(f"{description} 순위 조회 실패")
            
            logger.info(f"최종 수집된 종목: {len(all_stocks)}개")
            return all_stocks
            
        except Exception as e:
            logger.error(f"Error getting market stocks: {e}")
            return []
    
    def _get_stocks_by_screen_code(self, screen_code: str):
        """화면 코드별 종목 조회"""
        try:
            if not self.kis_api.ensure_valid_token():
                return None
            
            url = f"{self.kis_api.base_url}/uapi/domestic-stock/v1/quotations/volume-rank"
            
            headers = {
                "content-type": "application/json; charset=utf-8",
                "authorization": f"Bearer {self.kis_api.access_token}",
                "appkey": self.kis_api.appkey,
                "appsecret": self.kis_api.appsecret,
                "tr_id": "FHPST01710000"
            }
            
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_COND_SCR_DIV_CODE": screen_code,
                "FID_INPUT_ISCD": "0000",
                "FID_DIV_CLS_CODE": "0",
                "FID_BLNG_CLS_CODE": "0",
                "FID_TRGT_CLS_CODE": "111111111",
                "FID_TRGT_EXLS_CLS_CODE": "000000",
                "FID_INPUT_PRICE_1": "",
                "FID_INPUT_PRICE_2": "",
                "FID_VOL_CNT": "",
                "FID_INPUT_DATE_1": ""
            }
            
            response = self.kis_api._make_api_request_with_retry(
                'GET', url, headers=headers, params=params, endpoint_name=f"screen_{screen_code}"
            )
            if response:
                return response.json()
            return None
            
        except Exception as e:
            logger.error(f"Error getting stocks by screen code {screen_code}: {e}")
            return None
    
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
        
        # 3. 재무 데이터 추가
        # TODO: 실제 재무 데이터 API 연동 필요
        # 현재는 기술적 지표만 사용하여 분석
        
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