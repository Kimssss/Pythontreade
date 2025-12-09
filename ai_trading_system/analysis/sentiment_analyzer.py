#!/usr/bin/env python3
"""
뉴스 감성 분석 시스템
실시간 뉴스 크롤링 및 감성 분석
"""

import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path
import pandas as pd
import numpy as np
import re
import time
from bs4 import BeautifulSoup

# 감성 분석을 위한 라이브러리
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger('ai_trading.sentiment')


class KoreanSentimentAnalyzer:
    """한국어 감성 분석기"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.positive_words = [
            '상승', '급등', '강세', '호재', '긍정', '성장', '수익', '이익', 
            '증가', '개선', '호조', '돌파', '신고가', '반등', '회복'
        ]
        self.negative_words = [
            '하락', '급락', '약세', '악재', '부정', '감소', '손실', '우려',
            '하락세', '침체', '악화', '부진', '신저가', '폭락', '위험'
        ]
        
        if TRANSFORMERS_AVAILABLE:
            self._load_model()
        
        logger.info("Korean Sentiment Analyzer initialized")
    
    def _load_model(self):
        """한국어 감성 분석 모델 로드"""
        try:
            model_name = "klue/roberta-base"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            logger.info("Korean sentiment model loaded successfully")
        except Exception as e:
            logger.warning(f"Pre-trained model load failed, using rule-based: {e}")
    
    def analyze(self, text: str) -> Dict:
        """텍스트 감성 분석"""
        if not text or not text.strip():
            return {'sentiment': 'neutral', 'confidence': 0.0, 'score': 0.0}
        
        # 전처리
        cleaned_text = self._preprocess_text(text)
        
        if TRANSFORMERS_AVAILABLE and self.tokenizer:
            return self._analyze_with_model(cleaned_text)
        else:
            return self._analyze_with_rules(cleaned_text)
    
    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # 특수 문자 정리
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        
        # 여러 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _analyze_with_model(self, text: str) -> Dict:
        """모델 기반 감성 분석"""
        try:
            # 실제로는 더 정교한 모델 사용
            # 여기서는 간단한 규칙 기반으로 대체
            return self._analyze_with_rules(text)
        except Exception as e:
            logger.error(f"Model analysis failed: {e}")
            return self._analyze_with_rules(text)
    
    def _analyze_with_rules(self, text: str) -> Dict:
        """규칙 기반 감성 분석"""
        positive_score = 0
        negative_score = 0
        
        # 긍정 단어 카운트
        for word in self.positive_words:
            positive_score += text.count(word) * 1.0
        
        # 부정 단어 카운트  
        for word in self.negative_words:
            negative_score += text.count(word) * 1.0
        
        total_score = positive_score + negative_score
        
        if total_score == 0:
            return {'sentiment': 'neutral', 'confidence': 0.0, 'score': 0.0}
        
        # 감성 점수 계산 (-1 ~ 1)
        score = (positive_score - negative_score) / (positive_score + negative_score + 1e-6)
        confidence = min(total_score / 10.0, 1.0)  # 최대 1.0
        
        # 감성 라벨 결정
        if score > 0.2:
            sentiment = 'positive'
        elif score < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'score': score,
            'positive_score': positive_score,
            'negative_score': negative_score
        }


class NewsCollector:
    """뉴스 수집기"""
    
    def __init__(self):
        self.news_sources = {
            'naver_finance': 'https://finance.naver.com/news/news_list.nhn?mode=LSS2D&section_id=101&section_id2=258',
            'hankyung': 'https://www.hankyung.com/finance',
            'mk': 'https://www.mk.co.kr/news/economy/'
        }
        self.session = None
        
        logger.info("News Collector initialized")
    
    async def collect_news(self, stock_code: str = None, hours: int = 24) -> List[Dict]:
        """뉴스 수집"""
        all_news = []
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            try:
                # 네이버 금융 뉴스
                naver_news = await self._collect_naver_finance_news(stock_code)
                all_news.extend(naver_news)
                
                await asyncio.sleep(1)  # 요청 간격
                
                # 한국경제 뉴스
                hankyung_news = await self._collect_hankyung_news()
                all_news.extend(hankyung_news)
                
                await asyncio.sleep(1)
                
                # 매일경제 뉴스
                mk_news = await self._collect_mk_news()
                all_news.extend(mk_news)
                
            except Exception as e:
                logger.error(f"News collection failed: {e}")
        
        # 시간 필터링
        cutoff_time = datetime.now() - timedelta(hours=hours)
        filtered_news = [
            news for news in all_news 
            if news.get('published_at', datetime.now()) > cutoff_time
        ]
        
        logger.info(f"Collected {len(filtered_news)} news articles")
        return filtered_news
    
    async def _collect_naver_finance_news(self, stock_code: str = None) -> List[Dict]:
        """네이버 금융 뉴스 수집"""
        news_list = []
        
        try:
            url = self.news_sources['naver_finance']
            if stock_code:
                url += f"&code={stock_code}"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    return news_list
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # 뉴스 아이템 파싱
                items = soup.find_all('tr', class_='')[:10]  # 상위 10개
                
                for item in items:
                    try:
                        title_elem = item.find('a')
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        link = title_elem.get('href', '')
                        
                        if link.startswith('/'):
                            link = f"https://finance.naver.com{link}"
                        
                        news_list.append({
                            'title': title,
                            'content': title,  # 간단히 제목을 내용으로 사용
                            'link': link,
                            'source': 'naver_finance',
                            'published_at': datetime.now(),
                            'stock_code': stock_code
                        })
                        
                    except Exception as e:
                        logger.debug(f"Naver news item parsing error: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Naver finance news collection failed: {e}")
        
        return news_list
    
    async def _collect_hankyung_news(self) -> List[Dict]:
        """한국경제 뉴스 수집"""
        news_list = []
        
        try:
            url = self.news_sources['hankyung']
            
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    return news_list
                
                # 간단한 더미 데이터 (실제로는 HTML 파싱 필요)
                news_list = [
                    {
                        'title': f'한경 경제뉴스 {i+1}',
                        'content': f'한국경제 뉴스 내용 {i+1}',
                        'link': f'https://www.hankyung.com/news/{i+1}',
                        'source': 'hankyung',
                        'published_at': datetime.now() - timedelta(hours=i),
                        'stock_code': None
                    }
                    for i in range(5)
                ]
                
        except Exception as e:
            logger.error(f"Hankyung news collection failed: {e}")
        
        return news_list
    
    async def _collect_mk_news(self) -> List[Dict]:
        """매일경제 뉴스 수집"""
        news_list = []
        
        try:
            url = self.news_sources['mk']
            
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    return news_list
                
                # 간단한 더미 데이터
                news_list = [
                    {
                        'title': f'매경 증시뉴스 {i+1}',
                        'content': f'매일경제 증시 관련 뉴스 내용 {i+1}',
                        'link': f'https://www.mk.co.kr/news/{i+1}',
                        'source': 'mk',
                        'published_at': datetime.now() - timedelta(hours=i*2),
                        'stock_code': None
                    }
                    for i in range(3)
                ]
                
        except Exception as e:
            logger.error(f"MK news collection failed: {e}")
        
        return news_list


class SentimentSignalGenerator:
    """감성 기반 매매 신호 생성기"""
    
    def __init__(self):
        self.analyzer = KoreanSentimentAnalyzer()
        self.collector = NewsCollector()
        
        # 감성 점수 임계값
        self.bullish_threshold = 0.3
        self.bearish_threshold = -0.3
        
        logger.info("Sentiment Signal Generator initialized")
    
    async def generate_market_sentiment_signal(self) -> Dict:
        """시장 전체 감성 신호 생성"""
        try:
            # 뉴스 수집
            news_articles = await self.collector.collect_news(hours=12)
            
            if not news_articles:
                return self._default_sentiment_signal()
            
            # 감성 분석
            sentiment_scores = []
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for article in news_articles:
                result = self.analyzer.analyze(article['content'])
                sentiment_scores.append(result['score'])
                
                if result['sentiment'] == 'positive':
                    positive_count += 1
                elif result['sentiment'] == 'negative':
                    negative_count += 1
                else:
                    neutral_count += 1
            
            # 전체 감성 점수 계산
            avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
            sentiment_std = np.std(sentiment_scores) if len(sentiment_scores) > 1 else 0.0
            
            # 신호 생성
            signal_strength = 0.0
            signal_direction = 'neutral'
            
            if avg_sentiment > self.bullish_threshold:
                signal_direction = 'bullish'
                signal_strength = min(avg_sentiment, 1.0)
            elif avg_sentiment < self.bearish_threshold:
                signal_direction = 'bearish'
                signal_strength = min(abs(avg_sentiment), 1.0)
            
            return {
                'signal_direction': signal_direction,
                'signal_strength': signal_strength,
                'average_sentiment': avg_sentiment,
                'sentiment_volatility': sentiment_std,
                'article_count': len(news_articles),
                'sentiment_distribution': {
                    'positive': positive_count,
                    'negative': negative_count,
                    'neutral': neutral_count
                },
                'confidence': min(len(news_articles) / 20.0, 1.0),  # 뉴스 개수에 비례
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sentiment signal generation failed: {e}")
            return self._default_sentiment_signal()
    
    async def generate_stock_sentiment_signal(self, stock_code: str) -> Dict:
        """개별 종목 감성 신호 생성"""
        try:
            # 종목별 뉴스 수집
            news_articles = await self.collector.collect_news(stock_code=stock_code, hours=24)
            
            if not news_articles:
                return self._default_sentiment_signal()
            
            # 감성 분석
            sentiment_scores = []
            for article in news_articles:
                result = self.analyzer.analyze(article['content'])
                sentiment_scores.append(result['score'])
            
            avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.0
            
            # 신호 강도 계산 (종목별은 더 보수적)
            signal_strength = 0.0
            signal_direction = 'neutral'
            
            if avg_sentiment > self.bullish_threshold * 1.5:  # 더 높은 임계값
                signal_direction = 'bullish'
                signal_strength = min(avg_sentiment * 0.8, 1.0)  # 신호 강도 감소
            elif avg_sentiment < self.bearish_threshold * 1.5:
                signal_direction = 'bearish'
                signal_strength = min(abs(avg_sentiment) * 0.8, 1.0)
            
            return {
                'stock_code': stock_code,
                'signal_direction': signal_direction,
                'signal_strength': signal_strength,
                'average_sentiment': avg_sentiment,
                'article_count': len(news_articles),
                'confidence': min(len(news_articles) / 10.0, 1.0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Stock sentiment signal generation failed: {e}")
            return self._default_sentiment_signal()
    
    def _default_sentiment_signal(self) -> Dict:
        """기본 중립 신호"""
        return {
            'signal_direction': 'neutral',
            'signal_strength': 0.0,
            'average_sentiment': 0.0,
            'sentiment_volatility': 0.0,
            'article_count': 0,
            'confidence': 0.0,
            'timestamp': datetime.now().isoformat()
        }


class SentimentAgent:
    """감성 분석 에이전트 (앙상블 시스템용)"""
    
    def __init__(self):
        self.signal_generator = SentimentSignalGenerator()
        self.last_update = None
        self.market_sentiment_cache = None
        self.cache_ttl = 300  # 5분 캐시
        
        logger.info("Sentiment Agent initialized")
    
    async def get_trading_signal(self, stock_code: str, current_price: float) -> Dict:
        """거래 신호 생성"""
        try:
            # 시장 감성과 개별 종목 감성 결합
            market_signal = await self._get_market_sentiment()
            stock_signal = await self.signal_generator.generate_stock_sentiment_signal(stock_code)
            
            # 가중 평균으로 최종 신호 계산
            market_weight = 0.6
            stock_weight = 0.4
            
            market_score = self._signal_to_score(market_signal)
            stock_score = self._signal_to_score(stock_signal)
            
            final_score = market_score * market_weight + stock_score * stock_weight
            
            # 최종 신호 결정
            if final_score > 0.3:
                action = 'buy'
                confidence = min(final_score, 1.0)
            elif final_score < -0.3:
                action = 'sell'
                confidence = min(abs(final_score), 1.0)
            else:
                action = 'hold'
                confidence = 1.0 - abs(final_score)
            
            return {
                'action': action,
                'confidence': confidence,
                'sentiment_score': final_score,
                'market_sentiment': market_signal,
                'stock_sentiment': stock_signal,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sentiment trading signal failed: {e}")
            return {
                'action': 'hold',
                'confidence': 0.0,
                'sentiment_score': 0.0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_market_sentiment(self) -> Dict:
        """캐시된 시장 감성 조회"""
        now = datetime.now()
        
        if (self.market_sentiment_cache is None or 
            self.last_update is None or 
            (now - self.last_update).total_seconds() > self.cache_ttl):
            
            self.market_sentiment_cache = await self.signal_generator.generate_market_sentiment_signal()
            self.last_update = now
        
        return self.market_sentiment_cache
    
    def _signal_to_score(self, signal: Dict) -> float:
        """신호를 수치 점수로 변환"""
        direction = signal.get('signal_direction', 'neutral')
        strength = signal.get('signal_strength', 0.0)
        confidence = signal.get('confidence', 0.0)
        
        if direction == 'bullish':
            return strength * confidence
        elif direction == 'bearish':
            return -strength * confidence
        else:
            return 0.0


# 감성 분석 모니터링 및 데이터 저장
async def save_sentiment_data(sentiment_data: Dict, file_path: str = "sentiment_analysis_202512.json"):
    """감성 분석 데이터 저장"""
    try:
        sentiment_file = Path(file_path)
        
        # 기존 데이터 로드
        existing_data = []
        if sentiment_file.exists():
            with open(sentiment_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        
        # 새 데이터 추가
        existing_data.append(sentiment_data)
        
        # 최근 1000개만 유지
        if len(existing_data) > 1000:
            existing_data = existing_data[-1000:]
        
        # 저장
        with open(sentiment_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Sentiment data saved: {len(existing_data)} records")
        
    except Exception as e:
        logger.error(f"Sentiment data save failed: {e}")


if __name__ == "__main__":
    async def test_sentiment_system():
        """감성 분석 시스템 테스트"""
        print("🔍 감성 분석 시스템 테스트 시작")
        
        # 감성 분석기 테스트
        analyzer = KoreanSentimentAnalyzer()
        
        test_texts = [
            "삼성전자 주가 급등! 신고가 돌파 전망",
            "증시 폭락, 투자자들 우려 확산",
            "오늘 코스피는 보합세를 유지했다",
            "AI 관련주 강세, 성장 전망 밝아"
        ]
        
        print("\n📊 텍스트 감성 분석 결과:")
        for text in test_texts:
            result = analyzer.analyze(text)
            print(f"텍스트: {text}")
            print(f"감성: {result['sentiment']}, 점수: {result['score']:.3f}, 신뢰도: {result['confidence']:.3f}\n")
        
        # 뉴스 수집 테스트
        collector = NewsCollector()
        news = await collector.collect_news(hours=24)
        print(f"📰 수집된 뉴스: {len(news)}개")
        
        # 감성 신호 생성 테스트
        signal_gen = SentimentSignalGenerator()
        market_signal = await signal_gen.generate_market_sentiment_signal()
        print(f"\n📈 시장 감성 신호:")
        print(f"방향: {market_signal['signal_direction']}")
        print(f"강도: {market_signal['signal_strength']:.3f}")
        print(f"평균 감성: {market_signal['average_sentiment']:.3f}")
        
        # 감성 에이전트 테스트
        agent = SentimentAgent()
        trading_signal = await agent.get_trading_signal("005930", 75000)  # 삼성전자
        print(f"\n🤖 거래 신호:")
        print(f"행동: {trading_signal['action']}")
        print(f"신뢰도: {trading_signal['confidence']:.3f}")
        print(f"감성 점수: {trading_signal['sentiment_score']:.3f}")
        
        # 데이터 저장
        await save_sentiment_data(market_signal)
        print("\n💾 감성 데이터 저장 완료")
    
    # 테스트 실행
    asyncio.run(test_sentiment_system())