#!/usr/bin/env python3
"""
AI 자동매매 시스템 모니터링 대시보드
- 실시간 성과 추적
- 포트폴리오 분석
- 리스크 모니터링
- 거래 내역 시각화
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# 로컬 모듈 임포트
sys.path.append('.')
from kis_api_enhanced import KisAPIEnhanced as KisAPI
from config import Config
from auto_install import auto_install_on_import

# 페이지 설정
st.set_page_config(
    page_title="AI 자동매매 대시보드",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .performance-positive {
        color: #2E8B57;
        font-weight: bold;
    }
    .performance-negative {
        color: #DC143C;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_kis_api(mode='demo'):
    """KIS API 로드 (캐시됨)"""
    try:
        account_info = Config.get_account_info(mode)
        api = KisAPI(
            account_info['appkey'],
            account_info['appsecret'], 
            account_info['account'],
            is_real=(mode == 'real')
        )
        if api.get_access_token():
            return api
    except Exception as e:
        st.error(f"API 초기화 실패: {e}")
    return None

def get_portfolio_data(api):
    """포트폴리오 데이터 조회 (에러 처리 강화)"""
    if not api:
        return None, None, None
    
    try:
        balance = api.get_balance()
        holdings = api.get_holding_stocks()
        available_cash = api.get_available_cash()
        
        return balance, holdings, available_cash
    except Exception as e:
        st.warning(f"⚠️ 포트폴리오 데이터 조회 실패: {e}")
        st.info("💡 데모 서버 불안정성으로 인한 일시적 오류일 수 있습니다.")
        return None, None, None

def load_performance_log(mode='demo'):
    """성과 로그 로드"""
    log_file = Path(f"logs/performance_{mode}.json")
    
    if not log_file.exists():
        return pd.DataFrame()
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
        
        return df
    except Exception as e:
        st.error(f"성과 로그 로드 실패: {e}")
        return pd.DataFrame()

def create_portfolio_pie_chart(holdings):
    """포트폴리오 파이 차트 생성"""
    if not holdings:
        return None
    
    fig = go.Figure(data=[go.Pie(
        labels=[h['stock_name'] for h in holdings],
        values=[h['quantity'] * h['current_price'] for h in holdings],
        textinfo='label+percent',
        hole=0.4
    )])
    
    fig.update_layout(
        title="포트폴리오 구성",
        height=400,
        showlegend=True
    )
    
    return fig

def create_performance_chart(performance_df):
    """성과 차트 생성"""
    if performance_df.empty:
        return None
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('포트폴리오 가치 변화', '일일 수익률'),
        vertical_spacing=0.1
    )
    
    # 포트폴리오 가치
    fig.add_trace(
        go.Scatter(
            x=performance_df['timestamp'],
            y=performance_df['balance'],
            mode='lines+markers',
            name='포트폴리오 가치',
            line=dict(color='#1f77b4', width=2)
        ),
        row=1, col=1
    )
    
    # 일일 수익률 계산
    if len(performance_df) > 1:
        daily_returns = performance_df['balance'].pct_change().fillna(0) * 100
        
        colors = ['red' if x < 0 else 'green' for x in daily_returns]
        
        fig.add_trace(
            go.Bar(
                x=performance_df['timestamp'],
                y=daily_returns,
                name='일일 수익률 (%)',
                marker_color=colors
            ),
            row=2, col=1
        )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        title_text="성과 분석"
    )
    
    fig.update_yaxis(title_text="포트폴리오 가치 (원)", row=1, col=1)
    fig.update_yaxis(title_text="수익률 (%)", row=2, col=1)
    
    return fig

def calculate_performance_metrics(performance_df):
    """성과 지표 계산"""
    if performance_df.empty or len(performance_df) < 2:
        return {}
    
    # 수익률 계산
    initial_value = performance_df['balance'].iloc[0]
    current_value = performance_df['balance'].iloc[-1]
    total_return = (current_value - initial_value) / initial_value * 100
    
    # 일일 수익률
    daily_returns = performance_df['balance'].pct_change().dropna()
    
    # 연환산 수익률
    days = len(daily_returns)
    annualized_return = ((1 + total_return/100) ** (252/days) - 1) * 100 if days > 0 else 0
    
    # 변동성 (연환산)
    volatility = daily_returns.std() * np.sqrt(252) * 100 if len(daily_returns) > 1 else 0
    
    # 샤프 비율 (무위험 수익률 3% 가정)
    excess_return = annualized_return - 3
    sharpe_ratio = excess_return / volatility if volatility > 0 else 0
    
    # 최대 손실 (MDD)
    rolling_max = performance_df['balance'].expanding().max()
    drawdown = (performance_df['balance'] - rolling_max) / rolling_max * 100
    max_drawdown = drawdown.min()
    
    return {
        'total_return': total_return,
        'annualized_return': annualized_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'current_value': current_value,
        'trading_days': days
    }

def create_risk_gauge(sharpe_ratio, max_drawdown):
    """리스크 게이지 차트"""
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "indicator"}, {"type": "indicator"}]],
        subplot_titles=("샤프 비율", "최대 손실 (MDD)")
    )
    
    # 샤프 비율 게이지
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=sharpe_ratio,
            domain={'x': [0, 0.5], 'y': [0, 1]},
            title={'text': "샤프 비율"},
            gauge={
                'axis': {'range': [None, 3]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 1], 'color': "lightgray"},
                    {'range': [1, 2], 'color': "gray"},
                    {'range': [2, 3], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 1.5
                }
            }
        ),
        row=1, col=1
    )
    
    # MDD 게이지
    mdd_abs = abs(max_drawdown)
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=mdd_abs,
            domain={'x': [0.5, 1], 'y': [0, 1]},
            title={'text': "MDD (%)"},
            gauge={
                'axis': {'range': [0, 30]},
                'bar': {'color': "darkred"},
                'steps': [
                    {'range': [0, 10], 'color': "lightgreen"},
                    {'range': [10, 20], 'color': "yellow"},
                    {'range': [20, 30], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 15
                }
            }
        ),
        row=1, col=2
    )
    
    fig.update_layout(height=300)
    return fig

def main():
    """메인 대시보드"""
    st.markdown('<h1 class="main-header">🤖 AI 자동매매 시스템 대시보드</h1>', 
                unsafe_allow_html=True)
    
    # 사이드바 설정
    st.sidebar.header("⚙️ 설정")
    mode = st.sidebar.selectbox("모드 선택", ["demo", "real"])
    auto_refresh = st.sidebar.checkbox("자동 새로고침 (30초)", value=True)
    
    if auto_refresh:
        st.sidebar.markdown("🔄 자동 새로고침 활성화")
        # 자동 새로고침 비활성화 (수동으로 새로고침)
        # import time
        # time.sleep(1)
        # st.rerun()
    
    # API 초기화
    api = load_kis_api(mode)
    
    if not api:
        st.error("❌ API 연결 실패")
        return
    
    # 데이터 로드
    balance, holdings, available_cash = get_portfolio_data(api)
    performance_df = load_performance_log(mode)
    
    # 메인 메트릭
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 보유 현금",
            value=f"{available_cash:,}원" if available_cash else "N/A"
        )
    
    with col2:
        if holdings:
            total_stock_value = sum(h['quantity'] * h['current_price'] for h in holdings)
            st.metric(
                label="📊 주식 평가액",
                value=f"{total_stock_value:,}원"
            )
        else:
            st.metric("📊 주식 평가액", "0원")
    
    with col3:
        if holdings and available_cash:
            total_value = available_cash + sum(h['quantity'] * h['current_price'] for h in holdings)
            st.metric(
                label="💎 총 자산",
                value=f"{total_value:,}원"
            )
        else:
            st.metric("💎 총 자산", "N/A")
    
    with col4:
        num_holdings = len(holdings) if holdings else 0
        st.metric(
            label="🏢 보유 종목 수",
            value=f"{num_holdings}개"
        )
    
    # 성과 분석
    if not performance_df.empty:
        st.header("📈 성과 분석")
        
        metrics = calculate_performance_metrics(performance_df)
        
        # 성과 지표 카드
        col1, col2, col3 = st.columns(3)
        
        with col1:
            return_color = "performance-positive" if metrics['total_return'] > 0 else "performance-negative"
            st.markdown(f"""
            <div class="metric-card">
                <h4>총 수익률</h4>
                <h2 class="{return_color}">{metrics['total_return']:.2f}%</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h4>연환산 수익률</h4>
                <h2>{metrics['annualized_return']:.2f}%</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h4>샤프 비율</h4>
                <h2>{metrics['sharpe_ratio']:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # 차트들
        col1, col2 = st.columns([2, 1])
        
        with col1:
            performance_chart = create_performance_chart(performance_df)
            if performance_chart:
                st.plotly_chart(performance_chart, use_container_width=True)
        
        with col2:
            risk_chart = create_risk_gauge(metrics['sharpe_ratio'], metrics['max_drawdown'])
            st.plotly_chart(risk_chart, use_container_width=True)
    
    # 포트폴리오 구성
    st.header("💼 포트폴리오 구성")
    
    if holdings:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            pie_chart = create_portfolio_pie_chart(holdings)
            if pie_chart:
                st.plotly_chart(pie_chart, use_container_width=True)
        
        with col2:
            # 보유 종목 테이블
            holdings_df = pd.DataFrame(holdings)
            holdings_df['평가손익'] = holdings_df['profit_amount']
            holdings_df['수익률'] = holdings_df['profit_rate']
            
            st.dataframe(
                holdings_df[['stock_name', 'quantity', 'current_price', '평가손익', '수익률']],
                column_config={
                    'stock_name': '종목명',
                    'quantity': '수량',
                    'current_price': '현재가',
                    '평가손익': st.column_config.NumberColumn('평가손익', format='%d원'),
                    '수익률': st.column_config.NumberColumn('수익률', format='%.2f%%')
                },
                use_container_width=True
            )
    else:
        st.info("현재 보유 중인 주식이 없습니다.")
    
    # 시장 정보 (에러 처리 강화)
    st.header("📊 시장 정보")
    
    major_stocks = ['005930', '000660', '035420']  # 삼성전자, SK하이닉스, NAVER
    stock_names = {'005930': '삼성전자', '000660': 'SK하이닉스', '035420': 'NAVER'}
    
    market_data = []
    error_count = 0
    
    for stock_code in major_stocks:
        try:
            price_data = api.get_stock_price(stock_code)
            if price_data and price_data.get('rt_cd') == '0':
                output = price_data['output']
                market_data.append({
                    '종목명': stock_names.get(stock_code, stock_code),
                    '현재가': int(output['stck_prpr']),
                    '전일대비': int(output['prdy_vrss']),
                    '등락률': float(output['prdy_ctrt']),
                    '거래량': int(output['acml_vol'])
                })
            else:
                error_count += 1
        except Exception as e:
            error_count += 1
            continue
    
    if market_data:
        market_df = pd.DataFrame(market_data)
        st.dataframe(
            market_df,
            column_config={
                '현재가': st.column_config.NumberColumn('현재가', format='%d원'),
                '전일대비': st.column_config.NumberColumn('전일대비', format='%+d원'),
                '등락률': st.column_config.NumberColumn('등락률', format='%+.2f%%'),
                '거래량': st.column_config.NumberColumn('거래량', format='%d주')
            },
            use_container_width=True
        )
    else:
        st.warning("⚠️ 시장 데이터를 불러올 수 없습니다.")
        
    if error_count > 0:
        st.info(f"💡 {error_count}개 종목 조회 실패 (데모 서버 불안정성)")
    
    # 푸터
    st.markdown("---")
    st.markdown(
        f"**마지막 업데이트:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"**모드:** {mode.upper()}"
    )

if __name__ == "__main__":
    main()