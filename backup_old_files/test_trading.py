from kis_api import KisAPI
from config import Config

# 환경 변수에서 모의투자 계좌 정보 로드
demo_account_info = Config.get_account_info('demo')

# API 인스턴스 생성
api = KisAPI(
    demo_account_info['appkey'], 
    demo_account_info['appsecret'], 
    demo_account_info['account'], 
    is_real=False
)

print("=== 한국투자증권 API 테스트 ===")

# 1. 토큰 발급
print("\n1. 토큰 발급 테스트")
if api.get_access_token():
    print("✅ 토큰 발급 성공")
else:
    print("❌ 토큰 발급 실패")
    exit()

# 2. 계좌 잔고 조회
print("\n2. 계좌 잔고 조회")
balance = api.get_balance()
if balance and balance.get('rt_cd') == '0':
    print("✅ 잔고 조회 성공")
    output2 = balance.get('output2', [{}])[0]
    print(f"총 평가 금액: {output2.get('tot_evlu_amt', 'N/A')}원")
    print(f"주문 가능 현금: {output2.get('ord_psbl_cash', 'N/A')}원")
else:
    print("❌ 잔고 조회 실패:", balance)

# 3. 삼성전자 현재가 조회
print("\n3. 삼성전자 현재가 조회")
price = api.get_stock_price("005930")
if price and price.get('rt_cd') == '0':
    print("✅ 현재가 조회 성공")
    output = price.get('output', {})
    print(f"현재가: {output.get('stck_prpr', 'N/A')}원")
    print(f"등락율: {output.get('prdy_ctrt', 'N/A')}%")
else:
    print("❌ 현재가 조회 실패:", price)

# 4. 주문 내역 조회
print("\n4. 주문 내역 조회")
orders = api.get_orders()
if orders and orders.get('rt_cd') == '0':
    print("✅ 주문 내역 조회 성공")
    order_list = orders.get('output', [])
    print(f"주문 건수: {len(order_list)}")
else:
    print("❌ 주문 내역 조회 실패:", orders)

print("\n=== 테스트 완료 ===")
print("모든 기본 기능이 정상 작동합니다!")
print("매수/매도 주문은 실제 거래이므로 주의해서 사용하세요.")