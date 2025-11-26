#!/usr/bin/env python3
"""
감성 분석 모듈
- 뉴스 텍스트 감성 분석
- 소셜 미디어 감성 추적
- 시장 심리 지수 계산
"""

import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
import time

# 감성 분석용 간단한 키워드 사전
POSITIVE_KEYWORDS = [
    '상승', '증가', '호재', '긍정', '성장', '확대', '개선', '강세', '급등', 
    '돌파', '회복', '반등', '상향', '호조', '수익', '이익', '매출증대'
]

NEGATIVE_KEYWORDS = [
    '하락', '감소', '악재', '부정', '위험', '우려', '하향', '약세', '급락',
    '손실', '적자', '위기', '하향조정', '매출감소', '실적부진'
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Newscrawler:
    """
    뉴스 크롤링 클래스
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def crawl_naver_news(self, stock_code: str, days: int = 7) -> List[Dict]:
        """
        네이버 증권 뉴스 크롤링
        """
        news_list = []
        
        try:
            # 네이버 증권 뉴스 URL
            url = f"https://finance.naver.com/item/news.naver?code={stock_code}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                logger.warning(f"뉴스 크롤링 실패: {stock_code}")
                return news_list
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 뉴스 리스트 추출
            news_items = soup.select('.newsList .news_item')
            
            for item in news_items[:20]:  # 최대 20개 뉴스
                try:
                    # 제목 추출
                    title_elem = item.select_one('.news_tit')
                    title = title_elem.text.strip() if title_elem else ''
                    
                    # 링크 추출
                    link = title_elem.get('href') if title_elem else ''
                    
                    # 요약 추출
                    summary_elem = item.select_one('.news_summary')
                    summary = summary_elem.text.strip() if summary_elem else ''
                    
                    # 날짜 추출
                    date_elem = item.select_one('.news_date')
                    date_str = date_elem.text.strip() if date_elem else ''
                    
                    if title:
                        news_list.append({
                            'title': title,
                            'summary': summary,
                            'link': link,
                            'date': date_str,
                            'source': '네이버증권'
                        })
                        
                except Exception as e:
                    logger.warning(f"개별 뉴스 파싱 오류: {e}")
                    continue
            
            logger.info(f"{stock_code} 뉴스 {len(news_list)}건 수집")
            
        except Exception as e:
            logger.error(f"뉴스 크롤링 오류 ({stock_code}): {e}")
        
        return news_list
    
    def crawl_economic_news(self, keywords: List[str] = None) -> List[Dict]:
        """
        일반 경제 뉴스 크롤링
        """
        if keywords is None:
            keywords = ['주식시장', '경제동향', '금리', '환율']
        
        news_list = []
        
        try:
            # 네이버 경제 뉴스
            url = "https://news.naver.com/main/list.naver?mode=LS2D&mid=shm&sid1=101&sid2=258"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                articles = soup.select('.newsflash_body .type06_headline li')
                
                for article in articles[:15]:
                    try:
                        title_elem = article.select_one('a')
                        title = title_elem.text.strip() if title_elem else ''
                        link = title_elem.get('href') if title_elem else ''
                        
                        if title and any(keyword in title for keyword in keywords):
                            news_list.append({
                                'title': title,
                                'summary': '',
                                'link': link,
                                'date': datetime.now().strftime('%Y.%m.%d'),
                                'source': '네이버뉴스'
                            })
                    except:
                        continue
            
        except Exception as e:
            logger.error(f"경제 뉴스 크롤링 오류: {e}")
        
        return news_list

class SentimentAnalyzer:
    """
    감성 분석 클래스
    """
    
    def __init__(self):
        self.positive_keywords = POSITIVE_KEYWORDS
        self.negative_keywords = NEGATIVE_KEYWORDS
        
    def analyze_text(self, text: str) -> Dict[str, float]:
        """
        텍스트 감성 분석
        """
        if not text:
            return {'positive': 0.5, 'negative': 0.5, 'neutral': 0.0, 'score': 0.0}
        
        text = text.lower()
        
        # 긍정/부정 키워드 카운트
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in text)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in text)
        
        total_count = positive_count + negative_count
        
        if total_count == 0:
            return {'positive': 0.5, 'negative': 0.5, 'neutral': 1.0, 'score': 0.0}
        
        positive_ratio = positive_count / total_count
        negative_ratio = negative_count / total_count
        
        # 감성 스코어 (-1: 매우 부정, +1: 매우 긍정)
        sentiment_score = (positive_count - negative_count) / max(total_count, 1)
        
        return {
            'positive': positive_ratio,
            'negative': negative_ratio,
            'neutral': 0.0 if total_count > 0 else 1.0,
            'score': sentiment_score,
            'positive_count': positive_count,
            'negative_count': negative_count
        }
    
    def analyze_news_list(self, news_list: List[Dict]) -> Dict[str, float]:
        """
        뉴스 목록 전체 감성 분석
        """
        if not news_list:
            return {'sentiment_score': 0.0, 'positive_ratio': 0.5, 'news_count': 0}
        
        scores = []
        positive_count = 0
        negative_count = 0
        
        for news in news_list:
            # 제목과 요약을 합쳐서 분석
            text = f"{news.get('title', '')} {news.get('summary', '')}"
            analysis = self.analyze_text(text)
            
            scores.append(analysis['score'])
            if analysis['score'] > 0.1:
                positive_count += 1
            elif analysis['score'] < -0.1:
                negative_count += 1
        
        # 전체 감성 스코어
        avg_sentiment = np.mean(scores) if scores else 0.0
        
        # 긍정적 뉴스 비율
        total_classified = positive_count + negative_count
        positive_ratio = positive_count / max(total_classified, 1) if total_classified > 0 else 0.5
        
        return {
            'sentiment_score': avg_sentiment,
            'positive_ratio': positive_ratio,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': len(news_list) - positive_count - negative_count,
            'news_count': len(news_list)
        }

class MarketSentimentTracker:
    """
    시장 감성 추적기
    """
    
    def __init__(self):
        self.news_crawler = Newscrawler()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.sentiment_history = {}
        
    def get_stock_sentiment(self, stock_code: str) -> Dict[str, float]:
        """
        개별 종목 감성 분석
        """
        logger.info(f"{stock_code} 감성 분석 시작")
        
        try:
            # 뉴스 수집
            news_list = self.news_crawler.crawl_naver_news(stock_code)
            
            # 감성 분석
            sentiment_result = self.sentiment_analyzer.analyze_news_list(news_list)
            
            # 추가 정보
            sentiment_result['stock_code'] = stock_code
            sentiment_result['timestamp'] = datetime.now()
            
            # 히스토리에 저장
            if stock_code not in self.sentiment_history:
                self.sentiment_history[stock_code] = []
            
            self.sentiment_history[stock_code].append(sentiment_result)
            
            # 최근 10개만 유지
            self.sentiment_history[stock_code] = self.sentiment_history[stock_code][-10:]
            
            logger.info(f"{stock_code} 감성 스코어: {sentiment_result['sentiment_score']:.3f}")
            
            return sentiment_result
            
        except Exception as e:
            logger.error(f"종목 감성 분석 오류 ({stock_code}): {e}")
            return {
                'sentiment_score': 0.0,
                'positive_ratio': 0.5,
                'news_count': 0,
                'stock_code': stock_code,
                'timestamp': datetime.now()
            }
    
    def get_market_sentiment(self) -> Dict[str, float]:
        """
        전체 시장 감성 분석
        """
        logger.info("전체 시장 감성 분석 시작")
        
        try:
            # 경제 뉴스 수집
            economic_news = self.news_crawler.crawl_economic_news()
            
            # 감성 분석
            market_sentiment = self.sentiment_analyzer.analyze_news_list(economic_news)
            
            market_sentiment['type'] = 'market'
            market_sentiment['timestamp'] = datetime.now()
            
            logger.info(f"시장 감성 스코어: {market_sentiment['sentiment_score']:.3f}")
            
            return market_sentiment
            
        except Exception as e:
            logger.error(f"시장 감성 분석 오류: {e}")
            return {
                'sentiment_score': 0.0,
                'positive_ratio': 0.5,
                'news_count': 0,
                'type': 'market',
                'timestamp': datetime.now()
            }
    
    def get_sentiment_trend(self, stock_code: str, days: int = 7) -> Dict[str, List]:
        """
        감성 트렌드 분석
        """
        if stock_code not in self.sentiment_history:
            return {'dates': [], 'scores': [], 'trend': 'neutral'}
        
        history = self.sentiment_history[stock_code]
        
        if len(history) < 2:
            return {'dates': [], 'scores': [], 'trend': 'neutral'}
        
        dates = [item['timestamp'] for item in history]
        scores = [item['sentiment_score'] for item in history]
        
        # 트렌드 계산
        recent_scores = scores[-3:] if len(scores) >= 3 else scores
        avg_recent = np.mean(recent_scores)
        
        if avg_recent > 0.2:
            trend = 'positive'
        elif avg_recent < -0.2:
            trend = 'negative'
        else:
            trend = 'neutral'
        
        return {
            'dates': dates,
            'scores': scores,
            'trend': trend,
            'avg_score': np.mean(scores),
            'trend_strength': abs(avg_recent)
        }
    
    def get_sentiment_signal(self, stock_code: str) -> Tuple[str, float]:
        """
        감성 기반 거래 신호
        """
        sentiment = self.get_stock_sentiment(stock_code)
        market_sentiment = self.get_market_sentiment()
        
        # 종목 감성과 시장 감성을 종합
        combined_score = (sentiment['sentiment_score'] * 0.7 + 
                         market_sentiment['sentiment_score'] * 0.3)
        
        # 신호 생성
        if combined_score > 0.3 and sentiment['positive_ratio'] > 0.6:
            signal = 'BUY'
            confidence = min(0.8, combined_score + 0.2)
        elif combined_score < -0.3 and sentiment['positive_ratio'] < 0.4:
            signal = 'SELL'
            confidence = min(0.8, abs(combined_score) + 0.2)
        else:
            signal = 'HOLD'
            confidence = 0.3
        
        return signal, confidence
    
    def generate_sentiment_report(self, stock_codes: List[str]) -> str:
        """
        감성 분석 리포트 생성
        """
        report = f"# 감성 분석 리포트 ({datetime.now().strftime('%Y-%m-%d %H:%M')})\n\n"
        
        # 시장 전체 감성
        market_sentiment = self.get_market_sentiment()
        report += f"## 시장 전체 감성\n"
        report += f"- 감성 스코어: {market_sentiment['sentiment_score']:.3f}\n"
        report += f"- 긍정 뉴스 비율: {market_sentiment['positive_ratio']:.1%}\n"
        report += f"- 분석 뉴스 수: {market_sentiment['news_count']}건\n\n"
        
        # 개별 종목 감성
        report += f"## 개별 종목 감성\n"
        for stock_code in stock_codes:
            sentiment = self.get_stock_sentiment(stock_code)
            signal, confidence = self.get_sentiment_signal(stock_code)
            
            report += f"### {stock_code}\n"
            report += f"- 감성 스코어: {sentiment['sentiment_score']:.3f}\n"
            report += f"- 거래 신호: {signal} (신뢰도: {confidence:.1%})\n"
            report += f"- 긍정 뉴스: {sentiment.get('positive_count', 0)}건\n"
            report += f"- 부정 뉴스: {sentiment.get('negative_count', 0)}건\n\n"
        
        return report

# 전역 감성 추적기 인스턴스
sentiment_tracker = MarketSentimentTracker()

def get_sentiment_tracker() -> MarketSentimentTracker:
    """감성 추적기 인스턴스 반환"""
    return sentiment_tracker

def main():
    """테스트용 메인 함수"""
    print("📊 감성 분석 시스템 테스트")
    print("=" * 40)
    
    tracker = get_sentiment_tracker()
    
    # 테스트 종목들
    test_stocks = ['005930', '000660', '035420']  # 삼성전자, SK하이닉스, NAVER
    
    print("\n🔍 종목별 감성 분석")
    for stock in test_stocks:
        sentiment = tracker.get_stock_sentiment(stock)
        signal, confidence = tracker.get_sentiment_signal(stock)
        
        print(f"\n{stock}:")
        print(f"  감성 스코어: {sentiment['sentiment_score']:.3f}")
        print(f"  거래 신호: {signal} (신뢰도: {confidence:.1%})")
        print(f"  분석 뉴스: {sentiment['news_count']}건")
    
    print("\n📈 시장 전체 감성")
    market_sentiment = tracker.get_market_sentiment()
    print(f"  감성 스코어: {market_sentiment['sentiment_score']:.3f}")
    print(f"  긍정 비율: {market_sentiment['positive_ratio']:.1%}")
    
    # 리포트 생성
    print("\n📋 감성 분석 리포트 생성 중...")
    report = tracker.generate_sentiment_report(test_stocks)
    
    # 파일로 저장
    with open('sentiment_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("✅ 리포트 저장 완료: sentiment_report.md")

if __name__ == "__main__":
    main()
