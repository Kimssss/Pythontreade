#!/usr/bin/env python3
"""
Enhanced Stock Screener V2 - 여러 API를 조합하여 100개 종목 확보
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import time

load_dotenv()
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / 'ai_trading_system'))

from ai_trading_system.utils.kis_api import KisAPIEnhanced

async def get_extended_stock_list(api):
    """확장된 종목 리스트 확보"""
    all_stocks = []
    existing_codes = set()
    
    # 다양한 스크린 코드로 종목 수집
    screen_configs = [
        ("20171", "거래량"),      # 거래량 순위
        ("20173", "상승률"),      # 상승률 순위  
        ("20174", "하락률"),      # 하락률 순위
        ("20175", "변동률"),      # 변동률 순위
        ("20181", "시가총액"),    # 시가총액 순위
        ("20182", "매출액"),      # 매출액 순위
        ("20183", "영업이익"),    # 영업이익 순위
        ("20184", "당기순이익"),  # 당기순이익 순위
    ]
    
    for screen_code, description in screen_configs:
        if len(all_stocks) >= 100:
            break
            
        print(f"   📊 {description} 순위 조회 중...")
        
        try:
            url = f"{api.base_url}/uapi/domestic-stock/v1/quotations/volume-rank"
            
            headers = {
                "content-type": "application/json; charset=utf-8",
                "authorization": f"Bearer {api.access_token}",
                "appkey": api.appkey,
                "appsecret": api.appsecret,
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
            
            response = api._make_api_request_with_retry(
                'GET', url, headers=headers, params=params, endpoint_name=f"screen_{screen_code}"
            )
            
            if response:
                result = response.json()
                if result.get('rt_cd') == '0':
                    new_stocks = 0
                    for item in result.get('output', []):
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
                                'market_cap': market_cap,
                                'source': description
                            }
                            
                            if stock_info['price'] > 0 and stock_info['name']:
                                all_stocks.append(stock_info)
                                existing_codes.add(stock_code)
                                new_stocks += 1
                                
                                if len(all_stocks) >= 100:
                                    break
                    
                    print(f"      ✅ {description}에서 {new_stocks}개 추가 (누적: {len(all_stocks)}개)")
                else:
                    print(f"      ❌ {description} API 응답 오류: {result.get('msg1', 'Unknown')}")
            else:
                print(f"      ❌ {description} API 호출 실패")
            
            # API 호출 간격
            await asyncio.sleep(1.5)
            
        except Exception as e:
            print(f"      ❌ {description} 처리 중 오류: {e}")
    
    return all_stocks

async def get_extended_us_stocks(api):
    """확장된 미국 주식 리스트"""
    us_stocks = []
    
    # 주요 미국 주식 종목들 (S&P 500 상위 종목들)
    major_us_stocks = [
        # Tech Giants
        {'code': 'AAPL', 'name': 'Apple Inc', 'exchange': 'NASD'},
        {'code': 'MSFT', 'name': 'Microsoft Corp', 'exchange': 'NASD'},
        {'code': 'GOOGL', 'name': 'Alphabet Inc', 'exchange': 'NASD'},
        {'code': 'AMZN', 'name': 'Amazon.com Inc', 'exchange': 'NASD'},
        {'code': 'TSLA', 'name': 'Tesla Inc', 'exchange': 'NASD'},
        {'code': 'NVDA', 'name': 'NVIDIA Corp', 'exchange': 'NASD'},
        {'code': 'META', 'name': 'Meta Platforms Inc', 'exchange': 'NASD'},
        {'code': 'NFLX', 'name': 'Netflix Inc', 'exchange': 'NASD'},
        
        # Traditional Giants
        {'code': 'BRK.B', 'name': 'Berkshire Hathaway', 'exchange': 'NYSE'},
        {'code': 'JPM', 'name': 'JPMorgan Chase & Co', 'exchange': 'NYSE'},
        {'code': 'V', 'name': 'Visa Inc', 'exchange': 'NYSE'},
        {'code': 'UNH', 'name': 'UnitedHealth Group', 'exchange': 'NYSE'},
        {'code': 'JNJ', 'name': 'Johnson & Johnson', 'exchange': 'NYSE'},
        {'code': 'WMT', 'name': 'Walmart Inc', 'exchange': 'NYSE'},
        {'code': 'PG', 'name': 'Procter & Gamble', 'exchange': 'NYSE'},
        {'code': 'MA', 'name': 'Mastercard Inc', 'exchange': 'NYSE'},
        
        # Energy & Industrial
        {'code': 'XOM', 'name': 'Exxon Mobil Corp', 'exchange': 'NYSE'},
        {'code': 'CVX', 'name': 'Chevron Corp', 'exchange': 'NYSE'},
        {'code': 'BAC', 'name': 'Bank of America', 'exchange': 'NYSE'},
        {'code': 'ABBV', 'name': 'AbbVie Inc', 'exchange': 'NYSE'},
        
        # More stocks to reach 100
        {'code': 'LLY', 'name': 'Eli Lilly and Co', 'exchange': 'NYSE'},
        {'code': 'AVGO', 'name': 'Broadcom Inc', 'exchange': 'NASD'},
        {'code': 'HD', 'name': 'Home Depot Inc', 'exchange': 'NYSE'},
        {'code': 'COST', 'name': 'Costco Wholesale', 'exchange': 'NASD'},
        {'code': 'ADBE', 'name': 'Adobe Inc', 'exchange': 'NASD'},
    ]
    
    print(f"   🇺🇸 주요 미국 주식 {len(major_us_stocks)}개 기본 확보")
    
    # 각 종목의 현재가 조회
    for i, stock in enumerate(major_us_stocks[:100]):  # 100개까지만
        try:
            # API 호출로 실제 가격 조회
            price_data = api.overseas.get_overseas_price(stock['exchange'], stock['code'])
            
            if price_data and price_data.get('output'):
                price_info = price_data['output']
                current_price = float(price_info.get('last', 0))
                
                if current_price > 0:
                    stock_info = {
                        'code': stock['code'],
                        'name': stock['name'],
                        'price': current_price,
                        'exchange': stock['exchange'],
                        'volume': int(price_info.get('tvol', 0)),
                        'change_rate': float(price_info.get('rate', 0)),
                        'market_cap': current_price * 1000000000  # 임시값
                    }
                    us_stocks.append(stock_info)
            
            if (i + 1) % 10 == 0:
                print(f"      진행률: {i + 1}/{len(major_us_stocks)}")
                await asyncio.sleep(2)  # API 제한 방지
                
        except Exception as e:
            print(f"      ❌ {stock['code']} 처리 실패: {e}")
    
    # 더 많은 종목이 필요하면 인기 ETF도 추가
    if len(us_stocks) < 100:
        etf_stocks = [
            {'code': 'SPY', 'name': 'SPDR S&P 500 ETF', 'exchange': 'NYSE'},
            {'code': 'QQQ', 'name': 'Invesco QQQ Trust', 'exchange': 'NASD'},
            {'code': 'VTI', 'name': 'Vanguard Total Stock Market ETF', 'exchange': 'NYSE'},
            {'code': 'IWM', 'name': 'iShares Russell 2000 ETF', 'exchange': 'NYSE'},
            {'code': 'EFA', 'name': 'iShares MSCI EAFE ETF', 'exchange': 'NYSE'},
        ]
        
        for etf in etf_stocks:
            if len(us_stocks) >= 100:
                break
            us_stocks.append({
                'code': etf['code'],
                'name': etf['name'], 
                'price': 100.0,  # 임시값
                'exchange': etf['exchange'],
                'volume': 1000000,
                'change_rate': 0.0,
                'market_cap': 10000000000
            })
    
    return us_stocks[:100]

async def main():
    print("🚀 Enhanced Stock Screener V2 - 100개 종목씩 확보")
    print("=" * 70)
    
    api = KisAPIEnhanced(
        appkey=os.getenv('KIS_DEMO_APPKEY'),
        appsecret=os.getenv('KIS_DEMO_APPSECRET'),
        account_no=os.getenv('KIS_DEMO_ACCOUNT'),
        is_real=False
    )
    
    # 1. 국내 주식 100개 확보
    print("🇰🇷 1. 국내 주식 100개 확보 중...")
    domestic_stocks = await get_extended_stock_list(api)
    print(f"   ✅ 최종 국내 종목: {len(domestic_stocks)}개")
    
    # 2. 해외 주식 초기화 및 확보
    print("\\n🌍 2. 해외 주식 100개 확보 중...")
    try:
        api.initialize_overseas_api()
        us_stocks = await get_extended_us_stocks(api)
        print(f"   ✅ 최종 해외 종목: {len(us_stocks)}개")
    except Exception as e:
        print(f"   ❌ 해외 주식 처리 실패: {e}")
        us_stocks = []
    
    # 3. 결과 요약
    print("\\n" + "=" * 70)
    print("📊 최종 결과:")
    print(f"   🇰🇷 국내 주식: {len(domestic_stocks)}개")
    print(f"   🌍 해외 주식: {len(us_stocks)}개")
    print(f"   📈 총 분석 대상: {len(domestic_stocks) + len(us_stocks)}개")
    
    if len(domestic_stocks) >= 100:
        print("   ✅ 국내 목표 달성!")
    else:
        print(f"   📊 국내 종목 출처별 분포:")
        sources = {}
        for stock in domestic_stocks:
            source = stock.get('source', '미분류')
            sources[source] = sources.get(source, 0) + 1
        for source, count in sources.items():
            print(f"      - {source}: {count}개")
    
    if len(us_stocks) >= 100:
        print("   ✅ 해외 목표 달성!")
    else:
        print(f"   ⚠️  해외 목표 부족: {len(us_stocks)}/100개")
    
    return len(domestic_stocks), len(us_stocks)

if __name__ == "__main__":
    domestic_count, overseas_count = asyncio.run(main())
    print(f"\\n🎯 완료: 국내 {domestic_count}개 + 해외 {overseas_count}개 = 총 {domestic_count + overseas_count}개")