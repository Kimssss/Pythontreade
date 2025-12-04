#!/usr/bin/env python3
"""
Enhanced Stock Screener Test - 100개 종목 확보
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / 'ai_trading_system'))

from ai_trading_system.utils.kis_api import KisAPIEnhanced

async def test_enhanced_screener():
    print("🔍 Enhanced Stock Screener Test")
    print("=" * 50)
    
    api = KisAPIEnhanced(
        appkey=os.getenv('KIS_DEMO_APPKEY'),
        appsecret=os.getenv('KIS_DEMO_APPSECRET'),
        account_no=os.getenv('KIS_DEMO_ACCOUNT'),
        is_real=False
    )
    
    all_stocks = []
    
    # 1. 거래량 상위 종목
    print("📊 1. 거래량 상위 종목 조회...")
    volume_stocks = api.get_volume_rank()
    if volume_stocks and volume_stocks.get('rt_cd') == '0':
        stocks = volume_stocks.get('output', [])
        all_stocks.extend(stocks)
        print(f"   ✅ 거래량 종목: {len(stocks)}개")
    else:
        print("   ❌ 거래량 종목 조회 실패")
    
    # 2. 시가총액 상위 종목
    await asyncio.sleep(2)
    print("💰 2. 시가총액 상위 종목 조회...")
    try:
        cap_stocks = api.get_market_cap_rank()
        if cap_stocks and cap_stocks.get('rt_cd') == '0':
            stocks = cap_stocks.get('output', [])
            existing_codes = {stock.get('mksc_shrn_iscd') for stock in all_stocks}
            new_stocks = [s for s in stocks if s.get('mksc_shrn_iscd') not in existing_codes]
            all_stocks.extend(new_stocks)
            print(f"   ✅ 시가총액 종목: {len(stocks)}개 (중복 제거 후 {len(new_stocks)}개 추가)")
        else:
            print(f"   ❌ 시가총액 종목 조회 실패: {cap_stocks}")
    except Exception as e:
        print(f"   ❌ 시가총액 API 오류: {e}")
    
    # 3. 상승률 상위 종목
    await asyncio.sleep(2)
    print("📈 3. 상승률 상위 종목 조회...")
    try:
        rising_stocks = api.get_rising_rank()
        if rising_stocks and rising_stocks.get('rt_cd') == '0':
            stocks = rising_stocks.get('output', [])
            existing_codes = {stock.get('mksc_shrn_iscd') for stock in all_stocks}
            new_stocks = [s for s in stocks if s.get('mksc_shrn_iscd') not in existing_codes]
            all_stocks.extend(new_stocks)
            print(f"   ✅ 상승률 종목: {len(stocks)}개 (중복 제거 후 {len(new_stocks)}개 추가)")
        else:
            print(f"   ❌ 상승률 종목 조회 실패: {rising_stocks}")
    except Exception as e:
        print(f"   ❌ 상승률 API 오류: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 최종 결과: 총 {len(all_stocks)}개 종목 확보")
    
    if all_stocks:
        print("\n📋 상위 10개 종목:")
        for i, stock in enumerate(all_stocks[:10]):
            code = stock.get('mksc_shrn_iscd', 'N/A')
            name = stock.get('hts_kor_isnm', 'N/A')
            price = stock.get('stck_prpr', 'N/A')
            print(f"   {i+1:2d}. {name} ({code}) - {price}원")
    
    return len(all_stocks)

if __name__ == "__main__":
    result = asyncio.run(test_enhanced_screener())
    print(f"\n✨ 테스트 완료: {result}개 종목")