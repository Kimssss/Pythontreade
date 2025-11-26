"""
네이버 금융 뉴스 크롤러

종목별 뉴스 헤드라인 수집
- 네이버 금융에서 종목 뉴스 크롤링
- 뉴스 제목, 날짜, 언론사 추출
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import time
import re


class NaverNewsCrawler:
    """네이버 금융 뉴스 크롤러"""

    def __init__(self):
        self.base_url = "https://finance.naver.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_stock_news(self, stock_code: str, count: int = 10) -> List[Dict]:
        """
        종목 뉴스 조회

        Args:
            stock_code: 종목코드 (6자리)
            count: 가져올 뉴스 수

        Returns:
            뉴스 리스트 [{'title': 제목, 'date': 날짜, 'source': 언론사}, ...]
        """
        news_list = []

        try:
            # 네이버 금융 종목 뉴스 페이지
            url = f"{self.base_url}/item/news.naver?code={stock_code}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 뉴스 테이블 찾기
            news_table = soup.select('table.type5 tbody tr')

            for row in news_table[:count]:
                try:
                    # 제목
                    title_elem = row.select_one('td.title a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)

                    # 언론사
                    source_elem = row.select_one('td.info')
                    source = source_elem.get_text(strip=True) if source_elem else ''

                    # 날짜
                    date_elem = row.select_one('td.date')
                    date = date_elem.get_text(strip=True) if date_elem else ''

                    news_list.append({
                        'title': title,
                        'source': source,
                        'date': date,
                        'stock_code': stock_code
                    })

                except Exception:
                    continue

        except requests.RequestException as e:
            print(f"뉴스 크롤링 실패 ({stock_code}): {e}")

        return news_list

    def get_stock_discussions(self, stock_code: str, count: int = 5) -> List[Dict]:
        """
        종목 토론방 글 조회

        Args:
            stock_code: 종목코드
            count: 가져올 글 수

        Returns:
            토론 글 리스트
        """
        discussions = []

        try:
            url = f"{self.base_url}/item/board.naver?code={stock_code}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.select('table.type2 tbody tr')

            for row in rows[:count]:
                try:
                    title_elem = row.select_one('td.title a')
                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)

                    # 추천/비추천
                    votes = row.select('td.num')
                    good = int(votes[0].get_text(strip=True)) if len(votes) > 0 else 0
                    bad = int(votes[1].get_text(strip=True)) if len(votes) > 1 else 0

                    discussions.append({
                        'title': title,
                        'good': good,
                        'bad': bad,
                        'stock_code': stock_code
                    })

                except Exception:
                    continue

        except requests.RequestException as e:
            print(f"토론방 크롤링 실패 ({stock_code}): {e}")

        return discussions

    def analyze_sentiment_keywords(self, news_list: List[Dict]) -> Dict:
        """
        뉴스 키워드 기반 감성 분석

        Args:
            news_list: 뉴스 리스트

        Returns:
            감성 분석 결과
        """
        # 긍정 키워드
        positive_keywords = [
            '상승', '급등', '신고가', '호재', '수주', '계약', '흑자', '실적개선',
            '매출증가', '상향', '목표가', '추천', '기대', '성장', '돌파', '강세',
            '최고', '역대', '신사업', '투자', '확대', '증가', '개선', '호실적'
        ]

        # 부정 키워드
        negative_keywords = [
            '하락', '급락', '신저가', '악재', '적자', '감소', '하향', '매도',
            '우려', '위험', '손실', '부진', '축소', '철수', '소송', '약세',
            '최저', '위기', '폭락', '조정', '하회', '둔화', '감익', '적자전환'
        ]

        positive_count = 0
        negative_count = 0
        positive_news = []
        negative_news = []

        for news in news_list:
            title = news.get('title', '')

            is_positive = any(keyword in title for keyword in positive_keywords)
            is_negative = any(keyword in title for keyword in negative_keywords)

            if is_positive and not is_negative:
                positive_count += 1
                positive_news.append(title)
            elif is_negative and not is_positive:
                negative_count += 1
                negative_news.append(title)

        total = len(news_list)
        if total == 0:
            return {
                'score': 0,
                'positive_ratio': 0,
                'negative_ratio': 0,
                'neutral_ratio': 100,
                'positive_count': 0,
                'negative_count': 0,
                'total_count': 0,
                'positive_news': [],
                'negative_news': []
            }

        neutral_count = total - positive_count - negative_count

        # 감성 점수 계산 (-100 ~ +100)
        score = ((positive_count - negative_count) / total) * 100

        return {
            'score': round(score, 2),
            'positive_ratio': round(positive_count / total * 100, 1),
            'negative_ratio': round(negative_count / total * 100, 1),
            'neutral_ratio': round(neutral_count / total * 100, 1),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'total_count': total,
            'positive_news': positive_news[:3],
            'negative_news': negative_news[:3]
        }

    def get_stock_sentiment(self, stock_code: str, news_count: int = 10) -> Dict:
        """
        종목 감성 분석 (뉴스 + 키워드 분석)

        Args:
            stock_code: 종목코드
            news_count: 분석할 뉴스 수

        Returns:
            종합 감성 분석 결과
        """
        # 뉴스 수집
        news_list = self.get_stock_news(stock_code, news_count)

        if not news_list:
            return {
                'stock_code': stock_code,
                'news_count': 0,
                'sentiment': {
                    'score': 0,
                    'label': 'NEUTRAL',
                    'positive_ratio': 0,
                    'negative_ratio': 0
                },
                'news': [],
                'error': '뉴스를 찾을 수 없습니다'
            }

        # 감성 분석
        sentiment = self.analyze_sentiment_keywords(news_list)

        # 라벨 결정
        if sentiment['score'] >= 30:
            label = 'POSITIVE'
        elif sentiment['score'] <= -30:
            label = 'NEGATIVE'
        else:
            label = 'NEUTRAL'

        return {
            'stock_code': stock_code,
            'news_count': len(news_list),
            'sentiment': {
                'score': sentiment['score'],
                'label': label,
                'positive_ratio': sentiment['positive_ratio'],
                'negative_ratio': sentiment['negative_ratio'],
                'positive_count': sentiment['positive_count'],
                'negative_count': sentiment['negative_count']
            },
            'positive_news': sentiment['positive_news'],
            'negative_news': sentiment['negative_news'],
            'news': news_list[:5],  # 최근 5개 뉴스
            'timestamp': datetime.now().isoformat()
        }


# 테스트
if __name__ == "__main__":
    crawler = NaverNewsCrawler()

    # 삼성전자 뉴스 테스트
    result = crawler.get_stock_sentiment('005930')
    print(f"종목: {result['stock_code']}")
    print(f"뉴스 수: {result['news_count']}")
    print(f"감성 점수: {result['sentiment']['score']}")
    print(f"감성 라벨: {result['sentiment']['label']}")
    print(f"긍정 비율: {result['sentiment']['positive_ratio']}%")
    print(f"부정 비율: {result['sentiment']['negative_ratio']}%")
