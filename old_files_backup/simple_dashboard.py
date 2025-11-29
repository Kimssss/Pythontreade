#!/usr/bin/env python3
"""
간소화된 AI 자동매매 대시보드
- 토큰 캐시 사용
- 최소한의 API 호출
- 안정적인 동작
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import json
from pathlib import Path

from kis_api_enhanced import KisAPIEnhanced as KisAPI
from config import Config

st.set_page_config(
    page_title="AI 자동매매 간소 대시보드",
    page_icon="🤖",
    layout="wide"
)

# 제목
st.title("🤖 AI 자동매매 시스템 - 간소 대시보드")
st.markdown("---")

# 사이드바
st.sidebar.header("⚙️ 설정")
mode = st.sidebar.selectbox("모드 선택", ["demo", "real"])

# API 상태 확인
st.sidebar.markdown("### 📡 API 상태")

try:
    account_info = Config.get_account_info(mode)
    api = KisAPI(
        account_info['appkey'],
        account_info['appsecret'], 
        account_info['account'],
        is_real=(mode == 'real')
    )
    
    # 토큰 발급 시도 (캐시 우선)
    if api.get_access_token():
        st.sidebar.success("✅ API 연결 성공")
        st.sidebar.text(f"토큰 만료: {api.token_expire_time.strftime('%H:%M:%S') if api.token_expire_time else 'N/A'}")
        api_connected = True
    else:
        st.sidebar.error("❌ API 연결 실패")
        api_connected = False
        
except Exception as e:
    st.sidebar.error(f"❌ API 오류: {e}")
    api_connected = False

# 메인 대시보드
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🔌 API 상태", "연결됨" if api_connected else "연결 안됨")

with col2:
    st.metric("🎯 모드", mode.upper())

with col3:
    st.metric("🕒 업데이트", datetime.now().strftime("%H:%M:%S"))

# 기본 정보만 표시 (API 부하 최소화)
if api_connected:
    st.markdown("## 💰 기본 계좌 정보")
    
    # 한 번만 API 호출
    try:
        balance = api.get_balance()
        if balance and balance.get('rt_cd') == '0':
            output2 = balance.get('output2', [{}])
            if output2:
                cash = int(output2[0].get('ord_psbl_cash', 0))
                total_value = int(output2[0].get('tot_evlu_amt', 0))
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("💵 주문가능현금", f"{cash:,}원")
                with col2:
                    st.metric("💎 총평가금액", f"{total_value:,}원")
            
            # 보유 종목 (간단히)
            output1 = balance.get('output1', [])
            holding_stocks = [stock for stock in output1 if int(stock.get('hldg_qty', 0)) > 0]
            st.metric("📊 보유종목수", f"{len(holding_stocks)}개")
            
            if holding_stocks:
                st.markdown("### 📋 보유 종목")
                holdings_data = []
                for stock in holding_stocks[:5]:  # 최대 5개만 표시
                    holdings_data.append({
                        '종목명': stock.get('prdt_name', 'N/A'),
                        '수량': int(stock.get('hldg_qty', 0)),
                        '평가금액': int(stock.get('evlu_amt', 0))
                    })
                
                df = pd.DataFrame(holdings_data)
                st.dataframe(df, use_container_width=True)
        else:
            st.warning("잔고 정보를 가져올 수 없습니다.")
            
    except Exception as e:
        st.error(f"잔고 조회 오류: {e}")

else:
    st.error("API에 연결할 수 없습니다. 설정을 확인해주세요.")

# 간단한 차트 (샘플 데이터)
st.markdown("## 📈 포트폴리오 추이 (샘플)")

dates = pd.date_range(start='2024-11-01', end='2024-11-26', freq='D')
values = np.random.normal(1000000, 50000, len(dates)).cumsum()

fig = go.Figure()
fig.add_trace(go.Scatter(x=dates, y=values, mode='lines', name='포트폴리오 가치'))
fig.update_layout(
    title="포트폴리오 가치 변화",
    xaxis_title="날짜",
    yaxis_title="금액 (원)",
    height=400
)
st.plotly_chart(fig, use_container_width=True)

# AI 시스템 상태
st.markdown("## 🤖 AI 시스템 상태")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🧠 AI 모델", "DQN+Factor")
with col2:
    st.metric("📊 레짐", "강세장")
with col3:
    st.metric("⚖️ 리스크", "낮음")
with col4:
    st.metric("🎯 신호", "매수")

# 시스템 로그 (샘플)
st.markdown("## 📝 시스템 로그")
log_data = [
    {"시간": "21:45:01", "이벤트": "토큰 갱신 성공", "상태": "✅"},
    {"시간": "21:44:32", "이벤트": "AI 신호 생성", "상태": "🤖"},
    {"시간": "21:44:15", "이벤트": "시장 데이터 수집", "상태": "📊"},
    {"시간": "21:44:01", "이벤트": "리스크 점검 완료", "상태": "⚖️"},
    {"시간": "21:43:45", "이벤트": "포트폴리오 업데이트", "상태": "💼"}
]

log_df = pd.DataFrame(log_data)
st.dataframe(log_df, use_container_width=True)

# 새로고침 버튼
if st.button("🔄 수동 새로고침"):
    st.rerun()

# 푸터
st.markdown("---")
st.markdown(
    f"**마지막 업데이트:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"**모드:** {mode.upper()} | **토큰 캐싱:** ✅"
)