#!/usr/bin/env python3
"""
한국투자증권 API 500 에러 간단 진단 스크립트
"""

import pickle
import json
import requests
import base64
from datetime import datetime, timedelta
from pathlib import Path


def decode_jwt_payload_simple(token):
    """JWT 토큰의 페이로드를 간단히 디코드 (서명 검증 없이)"""
    try:
        # JWT는 header.payload.signature 형태
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # 페이로드 부분 (base64 디코드)
        payload = parts[1]
        # base64 패딩 추가
        payload += '=' * (4 - len(payload) % 4)
        decoded_bytes = base64.b64decode(payload)
        payload_data = json.loads(decoded_bytes.decode('utf-8'))
        
        return payload_data
    except Exception as e:
        print(f"JWT 토큰 디코드 실패: {e}")
        return None


def analyze_token_cache():
    """토큰 캐시 파일들을 분석"""
    print("=" * 60)
    print("🔍 토큰 캐시 파일 분석")
    print("=" * 60)
    
    cache_dir = Path("cache")
    if not cache_dir.exists():
        print("❌ cache 디렉토리가 존재하지 않습니다.")
        return {}
    
    token_data = {}
    
    for cache_file in cache_dir.glob("token_*.pkl"):
        print(f"\n📁 파일: {cache_file}")
        
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            access_token = cache_data.get('access_token')
            token_expire_time = cache_data.get('token_expire_time')
            saved_at = cache_data.get('saved_at')
            
            print(f"  ⏰ 저장 시간: {saved_at}")
            print(f"  ⌛ 만료 시간: {token_expire_time}")
            
            # 현재 시간과 비교
            now = datetime.now()
            if token_expire_time:
                if now < token_expire_time:
                    print(f"  ✅ 토큰 상태: 유효 (남은 시간: {token_expire_time - now})")
                else:
                    print(f"  ❌ 토큰 상태: 만료됨 (만료된 시간: {now - token_expire_time})")
            
            # JWT 토큰 디코드
            if access_token:
                print(f"  🔑 토큰 길이: {len(access_token)} 문자")
                print(f"  🔑 토큰 앞부분: {access_token[:30]}...")
                
                payload = decode_jwt_payload_simple(access_token)
                if payload:
                    print(f"  📝 JWT 페이로드:")
                    for key, value in payload.items():
                        if key in ['exp', 'iat']:
                            # Unix timestamp를 datetime으로 변환
                            try:
                                dt = datetime.fromtimestamp(value)
                                print(f"    {key}: {value} ({dt})")
                            except:
                                print(f"    {key}: {value}")
                        else:
                            print(f"    {key}: {value}")
                    
                    # 토큰 만료 시간 확인
                    if 'exp' in payload:
                        try:
                            exp_time = datetime.fromtimestamp(payload['exp'])
                            print(f"  ⏱️ JWT 만료 시간: {exp_time}")
                            if now < exp_time:
                                print(f"  ✅ JWT 토큰: 유효 (남은 시간: {exp_time - now})")
                            else:
                                print(f"  ❌ JWT 토큰: 만료됨 (만료된 시간: {now - exp_time})")
                        except:
                            print(f"  ⚠️ JWT 만료 시간 파싱 실패")
            
            # 토큰 데이터 저장
            mode = "demo" if "demo" in str(cache_file) else "real"
            token_data[mode] = {
                'access_token': access_token,
                'token_expire_time': token_expire_time,
                'saved_at': saved_at,
                'cache_file': cache_file
            }
            
        except Exception as e:
            print(f"  ❌ 파일 읽기 실패: {e}")
    
    return token_data


def test_token_validation():
    """토큰 유효성 테스트"""
    print("\n" + "=" * 60)
    print("🔐 토큰 유효성 테스트")
    print("=" * 60)
    
    try:
        from config import Config
    except Exception as e:
        print(f"❌ config 모듈 로드 실패: {e}")
        return
    
    token_data = analyze_token_cache()
    
    for mode, data in token_data.items():
        print(f"\n🏷️ {mode.upper()} 모드 토큰 테스트")
        
        if not data.get('access_token'):
            print("  ❌ 토큰이 없습니다.")
            continue
        
        # 설정 정보 로드
        try:
            account_info = Config.get_account_info(mode)
        except Exception as e:
            print(f"  ❌ 계정 정보 로드 실패: {e}")
            continue
        
        # 기본 API 호출 테스트 (잔고 조회)
        is_real = (mode == "real")
        base_url = "https://openapi.koreainvestment.com:9443" if is_real else "https://openapivts.koreainvestment.com:29443"
        
        url = f"{base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {data['access_token']}",
            "appkey": account_info['appkey'],
            "appsecret": account_info['appsecret'],
            "tr_id": "TTTC8434R" if is_real else "VTTC8434R"
        }
        
        params = {
            "CANO": account_info['account'].split('-')[0],
            "ACNT_PRDT_CD": account_info['account'].split('-')[1],
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        try:
            print("  🔄 잔고 조회 API 호출 중...")
            print(f"  📡 URL: {url}")
            print(f"  🔑 토큰: {data['access_token'][:20]}...")
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            print(f"  📡 HTTP 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"  📝 응답 코드: {result.get('rt_cd')}")
                print(f"  📝 응답 메시지: {result.get('msg1')}")
                
                if result.get('rt_cd') == '0':
                    print("  ✅ API 호출 성공!")
                    output2 = result.get('output2', [{}])
                    if output2:
                        print(f"  💰 예수금: {output2[0].get('dnca_tot_amt', 'N/A')}원")
                else:
                    print(f"  ❌ API 응답 에러: {result.get('msg1', 'Unknown error')}")
            
            elif response.status_code == 401:
                print("  ❌ 인증 실패 (401) - 토큰이 유효하지 않음")
                try:
                    error_data = response.json()
                    print(f"  📝 에러 메시지: {error_data}")
                except:
                    print(f"  📝 응답 내용: {response.text}")
            
            elif response.status_code == 403:
                print("  ❌ 권한 없음 (403) - API 키나 권한 문제")
                try:
                    error_data = response.json()
                    print(f"  📝 에러 메시지: {error_data}")
                except:
                    print(f"  📝 응답 내용: {response.text}")
            
            elif response.status_code == 500:
                print("  ❌ 서버 에러 (500) - 서버 내부 오류")
                try:
                    error_data = response.json()
                    print(f"  📝 에러 메시지: {error_data}")
                except:
                    print(f"  📝 응답 내용: {response.text[:300]}")
            
            else:
                print(f"  ⚠️ 기타 HTTP 에러: {response.status_code}")
                print(f"  📝 응답 내용: {response.text[:200]}")
            
        except requests.exceptions.Timeout:
            print("  ❌ 요청 타임아웃")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ 네트워크 오류: {e}")
        except Exception as e:
            print(f"  ❌ 기타 오류: {e}")


def test_new_token_issuance():
    """새 토큰 발급 테스트"""
    print("\n" + "=" * 60)
    print("🆕 새 토큰 발급 테스트")
    print("=" * 60)
    
    try:
        from config import Config
    except Exception as e:
        print(f"❌ config 모듈 로드 실패: {e}")
        return
    
    for mode in ["demo", "real"]:
        print(f"\n🏷️ {mode.upper()} 모드 토큰 발급")
        
        try:
            account_info = Config.get_account_info(mode)
        except Exception as e:
            print(f"  ❌ 계정 정보 로드 실패: {e}")
            continue
        
        # URL 설정
        is_real = (mode == "real")
        base_url = "https://openapi.koreainvestment.com:9443" if is_real else "https://openapivts.koreainvestment.com:29443"
        
        # 토큰 발급 요청
        url = f"{base_url}/oauth2/tokenP"
        
        headers = {
            "content-type": "application/json"
        }
        
        body = {
            "grant_type": "client_credentials",
            "appkey": account_info['appkey'],
            "appsecret": account_info['appsecret']
        }
        
        try:
            print("  🔄 토큰 발급 요청 중...")
            response = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)
            
            print(f"  📡 HTTP 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if 'access_token' in result:
                    print("  ✅ 토큰 발급 성공!")
                    print(f"  🔑 토큰: {result['access_token'][:30]}...")
                    print(f"  ⏰ 만료 시간(초): {result.get('expires_in', 'N/A')}")
                else:
                    print("  ❌ 토큰 발급 실패 - 응답에 토큰 없음")
                    print(f"  📝 응답: {result}")
            else:
                print("  ❌ 토큰 발급 실패")
                print(f"  📝 응답 내용: {response.text}")
            
        except Exception as e:
            print(f"  ❌ 요청 중 오류: {e}")


def check_config_file():
    """config 파일 확인"""
    print("\n" + "=" * 60)
    print("🔧 설정 파일 확인")
    print("=" * 60)
    
    try:
        from config import Config
        
        for mode in ["demo", "real"]:
            print(f"\n🏷️ {mode.upper()} 모드 설정:")
            try:
                account_info = Config.get_account_info(mode)
                print(f"  📁 App Key: {account_info['appkey'][:10]}...")
                print(f"  🔐 App Secret: {account_info['appsecret'][:10]}...")
                print(f"  🏦 계좌번호: {account_info['account']}")
                print("  ✅ 설정 로드 성공")
            except Exception as e:
                print(f"  ❌ 설정 로드 실패: {e}")
        
    except Exception as e:
        print(f"❌ Config 모듈 로드 실패: {e}")


def main():
    """메인 진단 함수"""
    print("🏥 한국투자증권 API 500 에러 간단 진단")
    print("=" * 60)
    
    # 1. 설정 파일 확인
    check_config_file()
    
    # 2. 토큰 캐시 분석 및 유효성 테스트
    test_token_validation()
    
    # 3. 새 토큰 발급 테스트
    test_new_token_issuance()
    
    # 종합 결론
    print("\n" + "=" * 60)
    print("📊 진단 결과 요약")
    print("=" * 60)
    
    print("\n💡 500 에러 주요 원인:")
    print("1. 토큰 만료 - 캐시된 토큰이 실제로는 만료됨")
    print("2. 토큰 형식 오류 - JWT 토큰 구조나 내용 문제")
    print("3. API 헤더 문제 - 필수 헤더 누락이나 형식 오류")
    print("4. 계좌 정보 오류 - 잘못된 앱키/시크릿/계좌번호")
    print("5. 서버 일시적 장애")
    
    print("\n🔧 해결 방법:")
    print("1. 토큰 캐시 삭제 후 재발급")
    print("   rm cache/token_*.pkl")
    print("2. 새로운 토큰으로 API 호출 재시도")
    print("3. API 헤더 구성 재확인")
    print("4. 계정 정보 재확인")


if __name__ == "__main__":
    main()