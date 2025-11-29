#!/usr/bin/env python3
"""
호가창 조회 API 테스트 스크립트
"""

from kis_api import KisAPI
from config import Config
import json

def test_orderbook_api():
    """호가창 조회 API 테스트"""
    print("=" * 60)
    print("📊 호가창 조회 API 테스트")
    print("=" * 60)
    
    # 모의투자 계정으로 테스트
    try:
        demo_account = Config.get_account_info('demo')
        api = KisAPI(
            demo_account['appkey'],
            demo_account['appsecret'],
            demo_account['account'],
            is_real=False
        )
        
        print("✅ KisAPI 객체 생성 완료")
        
        # 토큰 발급
        if api.get_access_token():
            print("✅ 토큰 발급 성공")
        else:
            print("❌ 토큰 발급 실패")
            return
        
        # 삼성전자 호가창 조회 테스트
        stock_code = "005930"  # 삼성전자
        print(f"\n📈 {stock_code} 호가창 조회 테스트")
        
        orderbook = api.get_orderbook(stock_code)
        
        if orderbook:
            print(f"📡 HTTP 상태: 성공")
            print(f"📝 응답 코드: {orderbook.get('rt_cd')}")
            print(f"📝 응답 메시지: {orderbook.get('msg1')}")
            
            if orderbook.get('rt_cd') == '0':
                print("✅ 호가창 조회 성공!")
                
                output = orderbook.get('output1', {})
                print(f"\n📊 호가창 정보:")
                print(f"  현재가: {output.get('stck_prpr', 'N/A')}")
                print(f"  매도 1호가: {output.get('askp1', 'N/A')} (잔량: {output.get('askp_rsqn1', 'N/A')})")
                print(f"  매수 1호가: {output.get('bidp1', 'N/A')} (잔량: {output.get('bidp_rsqn1', 'N/A')})")
                print(f"  매도 2호가: {output.get('askp2', 'N/A')} (잔량: {output.get('askp_rsqn2', 'N/A')})")
                print(f"  매수 2호가: {output.get('bidp2', 'N/A')} (잔량: {output.get('bidp_rsqn2', 'N/A')})")
                print(f"  총 매도잔량: {output.get('total_askp_rsqn', 'N/A')}")
                print(f"  총 매수잔량: {output.get('total_bidp_rsqn', 'N/A')}")
                
            else:
                print(f"❌ 호가창 조회 실패: {orderbook.get('msg1')}")
                print(f"📝 전체 응답: {json.dumps(orderbook, indent=2, ensure_ascii=False)}")
        else:
            print("❌ 호가창 조회 실패 - 응답 없음")
        
        # 분봉 데이터 조회 테스트
        print(f"\n📈 {stock_code} 1분봉 데이터 조회 테스트")
        
        minute_data = api.get_minute_data(stock_code, "1")
        
        if minute_data:
            print(f"📡 HTTP 상태: 성공")
            print(f"📝 응답 코드: {minute_data.get('rt_cd')}")
            print(f"📝 응답 메시지: {minute_data.get('msg1')}")
            
            if minute_data.get('rt_cd') == '0':
                print("✅ 분봉 데이터 조회 성공!")
                
                output2 = minute_data.get('output2', [])
                if output2 and len(output2) > 0:
                    latest = output2[0]
                    print(f"\n📊 최신 1분봉:")
                    print(f"  시간: {latest.get('stck_bsop_date', '')} {latest.get('stck_cntg_hour', '')}")
                    print(f"  시가: {latest.get('stck_oprc', 'N/A')}")
                    print(f"  고가: {latest.get('stck_hgpr', 'N/A')}")
                    print(f"  저가: {latest.get('stck_lwpr', 'N/A')}")
                    print(f"  종가: {latest.get('stck_prpr', 'N/A')}")
                    print(f"  거래량: {latest.get('cntg_vol', 'N/A')}")
                else:
                    print("⚠️ 분봉 데이터가 비어있음")
                    
            else:
                print(f"❌ 분봉 데이터 조회 실패: {minute_data.get('msg1')}")
        else:
            print("❌ 분봉 데이터 조회 실패 - 응답 없음")
            
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_orderbook_api()