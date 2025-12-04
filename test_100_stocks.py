#!/usr/bin/env python3
"""
100개 종목 확보 테스트
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / 'ai_trading_system'))

from ai_trading_system.strategies.stock_screener import StockScreener
from ai_trading_system.strategies.global_screener import GlobalStockScreener
from ai_trading_system.utils.kis_api import KisAPIEnhanced

async def test_100_stocks():
    print("🎯 국내 + 해외 100개 종목씩 확보 테스트")
    print("=" * 60)
    
    api = KisAPIEnhanced(
        appkey=os.getenv('KIS_DEMO_APPKEY'),
        appsecret=os.getenv('KIS_DEMO_APPSECRET'),
        account_no=os.getenv('KIS_DEMO_ACCOUNT'),
        is_real=False
    )
    
    # 1. 국내 주식 스크리너 테스트
    print("🇰🇷 1. 국내 주식 스크리닝...")
    domestic_screener = StockScreener(api)
    domestic_stocks = await domestic_screener.get_market_stocks()
    print(f"   ✅ 국내 종목: {len(domestic_stocks)}개 확보")
    
    if domestic_stocks:
        print("   📋 상위 5개 종목:")
        for i, stock in enumerate(domestic_stocks[:5]):
            name = stock.get('name', 'N/A')
            code = stock.get('code', 'N/A')
            price = stock.get('price', 'N/A')
            print(f"      {i+1}. {name} ({code}) - {price:,}원")
    
    # 2. 글로벌 스크리너 초기화 및 테스트
    print("\n🌍 2. 해외 주식 스크리닝...")
    try:
        api.initialize_overseas_api()
        global_screener = GlobalStockScreener(api)
        
        # 글로벌 스크리닝 실행
        global_results = await global_screener.screen_global_stocks(['NASDAQ', 'NYSE'])
        
        overseas_stocks = global_results.get('overseas', [])
        print(f"   ✅ 해외 종목: {len(overseas_stocks)}개 확보")
        
        if overseas_stocks:
            print("   📋 상위 5개 종목:")
            for i, stock in enumerate(overseas_stocks[:5]):
                name = stock.get('name', 'N/A')
                code = stock.get('code', 'N/A')
                price = stock.get('price', 'N/A')
                print(f"      {i+1}. {name} ({code}) - ${price}")
                
    except Exception as e:
        print(f"   ❌ 해외 주식 스크리닝 실패: {e}")
        overseas_stocks = []
    
    # 3. 결과 요약
    print("\n" + "=" * 60)
    print("📊 최종 결과:")
    print(f"   🇰🇷 국내 주식: {len(domestic_stocks)}개")
    print(f"   🌍 해외 주식: {len(overseas_stocks)}개") 
    print(f"   📈 총 분석 대상: {len(domestic_stocks) + len(overseas_stocks)}개")
    
    target_domestic = 100
    target_overseas = 100
    
    if len(domestic_stocks) >= target_domestic:
        print(f"   ✅ 국내 목표 달성: {target_domestic}개")
    else:
        print(f"   ⚠️  국내 목표 부족: {len(domestic_stocks)}/{target_domestic}개")
    
    if len(overseas_stocks) >= target_overseas:
        print(f"   ✅ 해외 목표 달성: {target_overseas}개")
    else:
        print(f"   ⚠️  해외 목표 부족: {len(overseas_stocks)}/{target_overseas}개")
    
    return len(domestic_stocks), len(overseas_stocks)

if __name__ == "__main__":
    domestic_count, overseas_count = asyncio.run(test_100_stocks())
    print(f"\n🎯 최종: 국내 {domestic_count}개 + 해외 {overseas_count}개 = 총 {domestic_count + overseas_count}개")