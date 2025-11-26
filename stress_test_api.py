#!/usr/bin/env python3
"""
한국투자증권 API 스트레스 테스트 - 500 에러 재현 시도
"""

import time
import requests
from kis_api import KisAPI
from config import Config
import threading
import json
from datetime import datetime


def stress_test_single_api(api, test_name, iterations=10):
    """단일 API 스트레스 테스트"""
    print(f"\n🔥 {test_name} 스트레스 테스트 ({iterations}회)")
    print("-" * 50)
    
    success_count = 0
    error_count = 0
    errors = []
    
    for i in range(iterations):
        try:
            print(f"  🔄 테스트 {i+1}/{iterations}...", end=" ")
            
            if test_name == "잔고 조회":
                result = api.get_balance()
            elif test_name == "주식 현재가":
                result = api.get_stock_price("005930")
            elif test_name == "호가창 조회":
                result = api.get_orderbook("005930")
            elif test_name == "분봉 데이터":
                result = api.get_minute_data("005930", "1")
            elif test_name == "거래량 순위":
                result = api.get_volume_rank()
            elif test_name == "등락률 순위":
                result = api.get_fluctuation_rank()
            else:
                result = None
            
            if result and result.get('rt_cd') == '0':
                print("✅")
                success_count += 1
            elif result:
                print(f"❌ (rt_cd: {result.get('rt_cd')})")
                error_count += 1
                errors.append(f"API 에러: {result.get('msg1')}")
            else:
                print("❌ (응답 없음)")
                error_count += 1
                errors.append("응답 없음")
                
        except Exception as e:
            print(f"❌ (예외: {str(e)[:30]}...)")
            error_count += 1
            errors.append(str(e))
        
        # 짧은 딜레이
        time.sleep(0.1)
    
    print(f"\n📊 결과:")
    print(f"  성공: {success_count}/{iterations}")
    print(f"  실패: {error_count}/{iterations}")
    
    if errors:
        print(f"  주요 에러:")
        for error in errors[:3]:  # 상위 3개 에러만 표시
            print(f"    - {error}")


def concurrent_api_test(api, num_threads=5, requests_per_thread=5):
    """동시 API 호출 테스트"""
    print(f"\n⚡ 동시 API 호출 테스트 ({num_threads}개 스레드, 각각 {requests_per_thread}회 요청)")
    print("-" * 50)
    
    results = []
    
    def worker(thread_id):
        """작업 스레드"""
        thread_results = {
            'thread_id': thread_id,
            'success': 0,
            'error': 0,
            'errors': []
        }
        
        for i in range(requests_per_thread):
            try:
                # 여러 API를 번갈아 호출
                if i % 3 == 0:
                    result = api.get_balance()
                elif i % 3 == 1:
                    result = api.get_stock_price("005930")
                else:
                    result = api.get_orderbook("005930")
                
                if result and result.get('rt_cd') == '0':
                    thread_results['success'] += 1
                else:
                    thread_results['error'] += 1
                    if result:
                        thread_results['errors'].append(result.get('msg1', 'Unknown error'))
                    else:
                        thread_results['errors'].append('No response')
                        
            except Exception as e:
                thread_results['error'] += 1
                thread_results['errors'].append(str(e))
            
            time.sleep(0.05)  # 매우 짧은 딜레이
        
        results.append(thread_results)
    
    # 스레드 생성 및 시작
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    # 모든 스레드 완료 대기
    for t in threads:
        t.join()
    
    # 결과 집계
    total_success = sum(r['success'] for r in results)
    total_error = sum(r['error'] for r in results)
    total_requests = total_success + total_error
    
    print(f"📊 동시 호출 결과:")
    print(f"  총 요청: {total_requests}")
    print(f"  성공: {total_success}")
    print(f"  실패: {total_error}")
    
    if total_error > 0:
        all_errors = []
        for r in results:
            all_errors.extend(r['errors'])
        
        # 에러 빈도 분석
        error_counts = {}
        for error in all_errors:
            error_counts[error] = error_counts.get(error, 0) + 1
        
        print(f"  주요 에러:")
        for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    - {error}: {count}회")


def rapid_fire_test(api, api_name, call_func, duration=30):
    """빠른 연속 호출 테스트"""
    print(f"\n🚀 빠른 연속 호출 테스트: {api_name} ({duration}초)")
    print("-" * 50)
    
    start_time = time.time()
    call_count = 0
    success_count = 0
    error_count = 0
    http_errors = {}
    
    while time.time() - start_time < duration:
        call_count += 1
        
        try:
            result = call_func()
            
            if result and result.get('rt_cd') == '0':
                success_count += 1
                print("✅", end="")
            elif result:
                error_count += 1
                print("❌", end="")
            else:
                error_count += 1
                print("⚠️", end="")
                
        except requests.exceptions.HTTPError as e:
            error_count += 1
            status_code = e.response.status_code if hasattr(e, 'response') else 'Unknown'
            http_errors[status_code] = http_errors.get(status_code, 0) + 1
            print(f"[{status_code}]", end="")
            
        except Exception as e:
            error_count += 1
            print("💥", end="")
        
        if call_count % 50 == 0:
            print(f" ({call_count})")
        
        time.sleep(0.05)  # 50ms 딜레이
    
    elapsed = time.time() - start_time
    rate = call_count / elapsed
    
    print(f"\n\n📊 빠른 연속 호출 결과:")
    print(f"  총 호출: {call_count}")
    print(f"  성공: {success_count}")
    print(f"  실패: {error_count}")
    print(f"  성공률: {success_count/call_count*100:.1f}%")
    print(f"  호출 속도: {rate:.2f} req/sec")
    
    if http_errors:
        print(f"  HTTP 에러:")
        for status_code, count in http_errors.items():
            print(f"    HTTP {status_code}: {count}회")


def token_expiry_test(api):
    """토큰 만료 시나리오 테스트"""
    print(f"\n⏰ 토큰 만료 시나리오 테스트")
    print("-" * 50)
    
    # 현재 토큰으로 정상 호출
    print("1. 현재 토큰으로 API 호출...")
    result = api.get_balance()
    if result and result.get('rt_cd') == '0':
        print("   ✅ 성공")
    else:
        print("   ❌ 실패")
    
    # 토큰 만료 시뮬레이션 (테스트용)
    print("2. 토큰 만료 시뮬레이션...")
    api.set_token_expiry_for_testing(-1)  # 1분 전으로 설정
    
    # 만료된 토큰으로 호출 시도
    print("3. 만료된 토큰으로 API 호출...")
    result = api.get_balance()
    if result and result.get('rt_cd') == '0':
        print("   ✅ 자동 갱신 후 성공")
    else:
        print("   ❌ 실패")


def main():
    """메인 테스트 함수"""
    print("🧪 한국투자증권 API 스트레스 테스트 시작")
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
        
        print(f"✅ KisAPI 객체 생성 완료")
        print(f"🔗 Base URL: {api.base_url}")
        
        # 초기 토큰 발급
        if not api.get_access_token():
            print("❌ 토큰 발급 실패")
            return
        
        print("✅ 토큰 발급 성공")
        
        # 1. 개별 API 스트레스 테스트
        stress_test_single_api(api, "잔고 조회", 10)
        stress_test_single_api(api, "주식 현재가", 10)
        stress_test_single_api(api, "호가창 조회", 10)
        stress_test_single_api(api, "분봉 데이터", 10)
        stress_test_single_api(api, "거래량 순위", 5)  # 더 무거운 API는 적게
        stress_test_single_api(api, "등락률 순위", 5)
        
        # 2. 동시 API 호출 테스트
        concurrent_api_test(api, 3, 5)
        
        # 3. 빠른 연속 호출 테스트
        rapid_fire_test(api, "잔고 조회", lambda: api.get_balance(), 15)
        
        # 4. 토큰 만료 테스트
        token_expiry_test(api)
        
        print("\n" + "=" * 60)
        print("🎯 테스트 완료!")
        print("💡 500 에러가 발생하지 않았다면:")
        print("   - 현재 토큰과 API 상태는 정상")
        print("   - 500 에러는 일시적이거나 특정 조건에서 발생")
        print("   - 실제 거래 상황에서 더 높은 빈도로 테스트 필요")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()