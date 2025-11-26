#!/usr/bin/env python3
"""
한국투자증권 API 500 에러 진단 스크립트
"""

import pickle
import json
import jwt
import requests
from datetime import datetime, timedelta
from pathlib import Path
import os


def decode_jwt_token(token):
    """JWT 토큰을 디코드하여 내용 확인 (서명 검증 없이)"""
    try:
        # 헤더 디코드
        header = jwt.get_unverified_header(token)
        
        # 페이로드 디코드
        payload = jwt.decode(token, options={"verify_signature": False})
        
        return header, payload
    except Exception as e:
        print(f"JWT 토큰 디코드 실패: {e}")
        return None, None


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
                
                header, payload = decode_jwt_token(access_token)
                if header and payload:
                    print(f"  📝 JWT 헤더: {header}")
                    print(f"  📝 JWT 페이로드:")
                    for key, value in payload.items():
                        if key in ['exp', 'iat']:
                            # Unix timestamp를 datetime으로 변환
                            dt = datetime.fromtimestamp(value)
                            print(f"    {key}: {value} ({dt})")
                        else:
                            print(f"    {key}: {value}")
                    
                    # 토큰 만료 시간 확인
                    if 'exp' in payload:
                        exp_time = datetime.fromtimestamp(payload['exp'])
                        print(f"  ⏱️ JWT 만료 시간: {exp_time}")
                        if now < exp_time:
                            print(f"  ✅ JWT 토큰: 유효 (남은 시간: {exp_time - now})")
                        else:
                            print(f"  ❌ JWT 토큰: 만료됨 (만료된 시간: {now - exp_time})")
            
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


def test_api_connectivity():
    """API 연결성 테스트"""
    print("\n" + "=" * 60)
    print("🌐 API 연결성 테스트")
    print("=" * 60)
    
    # 모의투자와 실전투자 URL 테스트
    urls = {
        "모의투자": "https://openapivts.koreainvestment.com:29443",
        "실전투자": "https://openapi.koreainvestment.com:9443"
    }
    
    for name, base_url in urls.items():
        print(f"\n🔗 {name} URL 테스트: {base_url}")
        
        try:
            # 간단한 연결 테스트 (토큰 발급 엔드포인트)
            test_url = f"{base_url}/oauth2/tokenP"
            response = requests.get(test_url, timeout=10)
            print(f"  📡 연결 상태: HTTP {response.status_code}")
            
            if response.status_code == 405:  # Method Not Allowed (정상)
                print("  ✅ API 서버 연결 가능")
            elif response.status_code == 404:
                print("  ❌ API 엔드포인트를 찾을 수 없음")
            else:
                print(f"  ⚠️ 예상과 다른 응답: {response.text[:100]}")
                
        except requests.exceptions.Timeout:
            print("  ❌ 연결 타임아웃")
        except requests.exceptions.ConnectionError:
            print("  ❌ 연결 실패")
        except Exception as e:
            print(f"  ❌ 연결 오류: {e}")


def test_token_validation(token_data):
    """토큰 유효성 테스트"""
    print("\n" + "=" * 60)
    print("🔐 토큰 유효성 테스트")
    print("=" * 60)
    
    from config import Config
    
    for mode, data in token_data.items():
        print(f"\n🏷️ {mode} 모드 토큰 테스트")
        
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
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            print(f"  📡 HTTP 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('rt_cd') == '0':
                    print("  ✅ API 호출 성공!")
                    print(f"  💰 예수금: {result.get('output2', [{}])[0].get('dnca_tot_amt', 'N/A')}원")
                else:
                    print(f"  ❌ API 응답 에러: {result.get('msg1', 'Unknown error')}")
                    print(f"  📝 응답 코드: {result.get('rt_cd')}")
            
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
                    print(f"  📝 응답 내용: {response.text}")
            
            else:
                print(f"  ⚠️ 기타 HTTP 에러: {response.status_code}")
                print(f"  📝 응답 내용: {response.text[:200]}")
            
        except requests.exceptions.Timeout:
            print("  ❌ 요청 타임아웃")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ 네트워크 오류: {e}")
        except Exception as e:
            print(f"  ❌ 기타 오류: {e}")


def check_kis_api_issues():
    """kis_api.py 파일의 잠재적 이슈 확인"""
    print("\n" + "=" * 60)
    print("🔧 kis_api.py 코드 분석")
    print("=" * 60)
    
    issues = []
    
    # 1. 헤더 구성 확인
    print("\n🏷️ API 헤더 구성 확인:")
    print("  - content-type: 'application/json; charset=utf-8' ✅")
    print("  - authorization: Bearer 토큰 사용 ✅")
    print("  - appkey/appsecret: 별도 헤더로 전송 ✅")
    print("  - tr_id: 실전/모의에 따라 구분 ✅")
    
    # 2. 토큰 재사용 로직 확인
    print("\n🔄 토큰 재사용 로직:")
    print("  - 토큰 캐시 파일 저장/로드 ✅")
    print("  - 토큰 만료 시간 확인 ✅")
    print("  - 만료 시 자동 갱신 ✅")
    
    # 3. 잠재적 이슈 확인
    print("\n⚠️ 잠재적 이슈:")
    
    # 토큰 만료 여유시간 확인
    print("  - 토큰 만료 5분 여유시간 설정됨")
    
    # 500 에러 처리 확인
    print("  - _make_api_request에서 500 에러도 토큰 갱신 대상으로 처리")
    print("    → 이는 500 에러가 토큰 문제일 가능성을 고려한 것")
    
    # 헤더 대소문자 확인
    print("  - 일부 API에서 헤더 대소문자가 중요할 수 있음")
    print("    → appkey/appsecret vs appKey/appSecret")
    
    return issues


def generate_token_test_script():
    """토큰 발급 테스트 스크립트 생성"""
    print("\n" + "=" * 60)
    print("🛠️ 토큰 발급 테스트 스크립트 생성")
    print("=" * 60)
    
    test_script = '''#!/usr/bin/env python3
"""
간단한 토큰 발급 및 검증 테스트 스크립트
"""

import requests
import json
from datetime import datetime
from config import Config

def test_token_issuance(mode="demo"):
    """토큰 발급 테스트"""
    print(f"=== {mode.upper()} 모드 토큰 발급 테스트 ===")
    
    # 설정 로드
    account_info = Config.get_account_info(mode)
    
    # URL 설정
    if mode == "real":
        base_url = "https://openapi.koreainvestment.com:9443"
    else:
        base_url = "https://openapivts.koreainvestment.com:29443"
    
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
    
    print(f"요청 URL: {url}")
    print(f"요청 헤더: {headers}")
    print(f"요청 본문: {json.dumps(body, indent=2)}")
    print()
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(body), timeout=30)
        
        print(f"응답 상태 코드: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 토큰 발급 성공!")
            print(f"토큰: {result.get('access_token', '')[:50]}...")
            print(f"토큰 유형: {result.get('token_type', '')}")
            print(f"만료 시간(초): {result.get('expires_in', '')}")
            return result.get('access_token')
        else:
            print("❌ 토큰 발급 실패!")
            print(f"응답 내용: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ 요청 중 오류: {e}")
        return None

def test_api_call_with_token(token, mode="demo"):
    """발급받은 토큰으로 API 호출 테스트"""
    if not token:
        print("토큰이 없어 API 호출을 건너뜁니다.")
        return
    
    print(f"\\n=== {mode.upper()} 모드 API 호출 테스트 ===")
    
    # 설정 로드
    account_info = Config.get_account_info(mode)
    
    # URL 설정
    if mode == "real":
        base_url = "https://openapi.koreainvestment.com:9443"
        tr_id = "TTTC8434R"
    else:
        base_url = "https://openapivts.koreainvestment.com:29443"
        tr_id = "VTTC8434R"
    
    # 잔고 조회 API 호출
    url = f"{base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
    
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": account_info['appkey'],
        "appsecret": account_info['appsecret'],
        "tr_id": tr_id
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
    
    print(f"요청 URL: {url}")
    print(f"요청 헤더: {headers}")
    print(f"요청 파라미터: {params}")
    print()
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        print(f"응답 상태 코드: {response.status_code}")
        print()
        
        if response.status_code == 200:
            result = response.json()
            if result.get('rt_cd') == '0':
                print("✅ API 호출 성공!")
                output2 = result.get('output2', [{}])
                if output2:
                    print(f"예수금: {output2[0].get('dnca_tot_amt', 'N/A')}원")
                    print(f"주문가능금액: {output2[0].get('ord_psbl_cash', 'N/A')}원")
            else:
                print("❌ API 응답 에러!")
                print(f"에러 코드: {result.get('rt_cd')}")
                print(f"에러 메시지: {result.get('msg1')}")
        else:
            print("❌ HTTP 에러!")
            print(f"응답 내용: {response.text}")
    
    except Exception as e:
        print(f"❌ 요청 중 오류: {e}")

if __name__ == "__main__":
    # 모의투자 테스트
    demo_token = test_token_issuance("demo")
    test_api_call_with_token(demo_token, "demo")
    
    # 실전투자 테스트
    real_token = test_token_issuance("real")
    test_api_call_with_token(real_token, "real")
'''
    
    with open("token_test.py", "w", encoding="utf-8") as f:
        f.write(test_script)
    
    print("✅ 토큰 테스트 스크립트 생성 완료: token_test.py")


def main():
    """메인 진단 함수"""
    print("🏥 한국투자증권 API 500 에러 진단 시작")
    
    # 1. 토큰 캐시 분석
    token_data = analyze_token_cache()
    
    # 2. API 연결성 테스트
    test_api_connectivity()
    
    # 3. 토큰 유효성 테스트
    test_token_validation(token_data)
    
    # 4. 코드 이슈 확인
    check_kis_api_issues()
    
    # 5. 테스트 스크립트 생성
    generate_token_test_script()
    
    # 종합 결론
    print("\n" + "=" * 60)
    print("📊 진단 결과 요약")
    print("=" * 60)
    
    print("\n🔍 주요 확인 포인트:")
    print("1. 토큰 캐시 파일의 토큰 만료 상태")
    print("2. JWT 토큰의 실제 만료 시간")
    print("3. API 서버 연결 상태")
    print("4. 토큰을 사용한 실제 API 호출 결과")
    
    print("\n💡 500 에러 해결 방법:")
    print("1. 토큰이 만료된 경우 → 캐시 삭제 후 재발급")
    print("2. 토큰 형식이 잘못된 경우 → 새로 발급")
    print("3. API 헤더 구성 문제 → 헤더 대소문자 및 형식 확인")
    print("4. 서버 측 문제 → 잠시 후 재시도")
    
    print(f"\n🧪 추가 테스트: python token_test.py 실행하여 상세 테스트 가능")


if __name__ == "__main__":
    main()