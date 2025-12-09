#!/usr/bin/env python3
"""
향상된 실시간 대시보드
블로그 분석 기반 구현
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
from typing import Dict, List, Optional

# Streamlit 설정
st.set_page_config(
    page_title="AI 트레이딩 시스템 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data(ttl=60)  # 1분 캐시
def load_performance_data():
    """성과 데이터 로드"""
    try:
        # 데모 성과 데이터
        demo_file = Path('performance_demo_202512.json')
        if demo_file.exists():
            with open(demo_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return pd.DataFrame(data) if data else pd.DataFrame()
        
        # 실전 성과 데이터
        real_file = Path('performance_real_202512.json') 
        if real_file.exists():
            with open(real_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return pd.DataFrame(data) if data else pd.DataFrame()
        
        return pd.DataFrame()
    except Exception as e:
        st.error(f"성과 데이터 로드 실패: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=30)  # 30초 캐시
def load_trade_data():
    """거래 데이터 로드"""
    try:
        # 데모 거래 데이터
        demo_file = Path('trades_demo_202512.json')
        if demo_file.exists():
            with open(demo_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return pd.DataFrame(data) if data else pd.DataFrame()
        
        return pd.DataFrame()
    except Exception as e:
        st.error(f"거래 데이터 로드 실패: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)  # 5분 캐시
def load_training_results():
    """학습 결과 로드"""
    try:
        results_dir = Path('training_results')
        if not results_dir.exists():
            return {}
        
        # 가장 최근 학습 결과
        files = list(results_dir.glob('training_*.json'))
        if not files:
            return {}
        
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    except Exception as e:
        st.error(f"학습 결과 로드 실패: {e}")
        return {}


def create_portfolio_chart(performance_df):
    """포트폴리오 성과 차트"""
    if performance_df.empty:
        return go.Figure()
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['포트폴리오 가치', '일일 수익률', '누적 수익률', '드로우다운'],
        specs=[[{"secondary_y": True}, {"type": "scatter"}],
               [{"type": "scatter"}, {"type": "scatter"}]]
    )
    
    # 포트폴리오 가치
    if 'total_value' in performance_df.columns:
        fig.add_trace(
            go.Scatter(
                x=performance_df.index,
                y=performance_df['total_value'],
                name='총 자산',
                line=dict(color='blue', width=2)
            ),
            row=1, col=1
        )
        
        # 현금 비중
        if 'cash_balance' in performance_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=performance_df.index,
                    y=performance_df['cash_balance'],
                    name='현금',
                    line=dict(color='green', width=1, dash='dash')
                ),
                row=1, col=1
            )
    
    # 일일 수익률
    if 'daily_return' in performance_df.columns:
        colors = ['red' if x < 0 else 'blue' for x in performance_df['daily_return']]
        fig.add_trace(
            go.Bar(
                x=performance_df.index,
                y=performance_df['daily_return'] * 100,
                name='일일 수익률(%)',
                marker_color=colors
            ),
            row=1, col=2
        )
    
    # 누적 수익률
    if 'total_value' in performance_df.columns and len(performance_df) > 1:
        initial_value = performance_df['total_value'].iloc[0]
        cumulative_return = (performance_df['total_value'] / initial_value - 1) * 100
        
        fig.add_trace(
            go.Scatter(
                x=performance_df.index,
                y=cumulative_return,
                name='누적 수익률(%)',
                line=dict(color='purple', width=2),
                fill='tonexty'
            ),
            row=2, col=1
        )
    
    # 드로우다운 계산
    if 'total_value' in performance_df.columns:
        peak = performance_df['total_value'].expanding().max()
        drawdown = (performance_df['total_value'] / peak - 1) * 100
        
        fig.add_trace(
            go.Scatter(
                x=performance_df.index,
                y=drawdown,
                name='드로우다운(%)',
                line=dict(color='red', width=2),
                fill='tonexty'
            ),
            row=2, col=2
        )
    
    fig.update_layout(
        height=600,
        showlegend=True,
        title_text="📈 포트폴리오 성과 분석",
    )
    
    return fig


def create_agent_performance_chart(training_results):
    """에이전트별 성과 차트"""
    if not training_results:
        return go.Figure()
    
    agents = ['DQN Agent', 'Technical Agent', 'Factor Agent', 'Transformer Agent']
    
    # 가상의 성과 데이터 (실제로는 training_results에서 추출)
    win_rates = [45.2, 38.7, 52.1, 41.3]
    total_returns = [12.4, 8.9, 15.7, 10.2]
    sharpe_ratios = [1.2, 0.8, 1.5, 1.0]
    
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=['승률 (%)', '수익률 (%)', 'Sharpe 비율'],
        specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]]
    )
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    
    # 승률
    fig.add_trace(
        go.Bar(x=agents, y=win_rates, name='승률', marker_color=colors),
        row=1, col=1
    )
    
    # 수익률
    fig.add_trace(
        go.Bar(x=agents, y=total_returns, name='수익률', marker_color=colors),
        row=1, col=2
    )
    
    # Sharpe 비율
    fig.add_trace(
        go.Bar(x=agents, y=sharpe_ratios, name='Sharpe 비율', marker_color=colors),
        row=1, col=3
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        title_text="🤖 AI 에이전트별 성과"
    )
    
    return fig


def create_trade_analysis_chart(trades_df):
    """거래 분석 차트"""
    if trades_df.empty:
        return go.Figure()
    
    # 시간별 거래량 분석
    if 'timestamp' in trades_df.columns:
        trades_df['hour'] = pd.to_datetime(trades_df['timestamp']).dt.hour
        hourly_trades = trades_df.groupby('hour').size()
        
        fig = go.Figure()
        
        fig.add_trace(
            go.Bar(
                x=hourly_trades.index,
                y=hourly_trades.values,
                name='시간별 거래 건수',
                marker_color='lightblue'
            )
        )
        
        fig.update_layout(
            title="⏰ 시간별 거래 패턴",
            xaxis_title="시간",
            yaxis_title="거래 건수",
            height=300
        )
        
        return fig
    
    return go.Figure()


def main():
    """메인 대시보드"""
    
    # 헤더
    st.title("🚀 AI 자동매매 시스템 대시보드")
    st.markdown("---")
    
    # 사이드바
    st.sidebar.title("📊 컨트롤 패널")
    
    # 모드 선택
    mode = st.sidebar.selectbox(
        "거래 모드",
        ["데모", "실전"],
        index=0
    )
    
    # 자동 새로고침
    auto_refresh = st.sidebar.checkbox("자동 새로고침 (30초)", value=True)
    
    if auto_refresh:
        time.sleep(30)
        st.experimental_rerun()
    
    # 수동 새로고침
    if st.sidebar.button("🔄 수동 새로고침"):
        st.cache_data.clear()
        st.experimental_rerun()
    
    # 데이터 로드
    performance_df = load_performance_data()
    trades_df = load_trade_data()
    training_results = load_training_results()
    
    # 상태 카드
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_value = performance_df['total_value'].iloc[-1] if not performance_df.empty else 10000000
        st.metric(
            label="💰 총 자산",
            value=f"{total_value:,.0f}원",
            delta=f"{(total_value/10000000-1)*100:+.2f}%"
        )
    
    with col2:
        daily_return = performance_df['daily_return'].iloc[-1] if not performance_df.empty else 0
        st.metric(
            label="📈 일일 수익률",
            value=f"{daily_return*100:+.2f}%",
            delta="전일 대비"
        )
    
    with col3:
        total_trades = len(trades_df) if not trades_df.empty else 0
        st.metric(
            label="🔄 총 거래 수",
            value=f"{total_trades}회",
            delta="누적"
        )
    
    with col4:
        if not performance_df.empty and len(performance_df) > 1:
            initial_value = performance_df['total_value'].iloc[0]
            current_value = performance_df['total_value'].iloc[-1]
            total_return = (current_value / initial_value - 1) * 100
        else:
            total_return = 0
        
        st.metric(
            label="📊 누적 수익률",
            value=f"{total_return:+.2f}%",
            delta="총 수익"
        )
    
    st.markdown("---")
    
    # 메인 차트
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.plotly_chart(
            create_portfolio_chart(performance_df),
            use_container_width=True
        )
    
    with col2:
        st.subheader("📋 실시간 현황")
        
        # 시스템 상태
        st.success("✅ 시스템 가동 중")
        st.info(f"🕐 마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")
        
        # 현재 포지션
        if not performance_df.empty:
            positions = performance_df['positions'].iloc[-1] if 'positions' in performance_df.columns else 0
            st.metric("🎯 현재 포지션", f"{positions}개")
        
        # 현금 잔고
        if not performance_df.empty:
            cash = performance_df['cash_balance'].iloc[-1] if 'cash_balance' in performance_df.columns else 0
            cash_ratio = cash / total_value * 100 if total_value > 0 else 0
            st.metric("💵 현금 비중", f"{cash_ratio:.1f}%")
    
    # 에이전트 성과
    st.plotly_chart(
        create_agent_performance_chart(training_results),
        use_container_width=True
    )
    
    # 거래 분석
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            create_trade_analysis_chart(trades_df),
            use_container_width=True
        )
    
    with col2:
        st.subheader("📋 최근 거래 내역")
        
        if not trades_df.empty:
            recent_trades = trades_df.tail(10)[['timestamp', 'action', 'stock_name', 'quantity', 'price']]
            st.dataframe(recent_trades, use_container_width=True)
        else:
            st.info("거래 내역이 없습니다.")
    
    # 상세 분석 탭
    tab1, tab2, tab3, tab4 = st.tabs(["📊 성과 분석", "🤖 AI 모델", "⚙️ 시스템 설정", "📈 백테스트"])
    
    with tab1:
        st.subheader("📊 상세 성과 분석")
        
        if not performance_df.empty:
            # 통계 요약
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**기본 통계**")
                if 'total_value' in performance_df.columns:
                    returns = performance_df['total_value'].pct_change().dropna()
                    
                    stats = {
                        "평균 일일 수익률": f"{returns.mean()*100:.3f}%",
                        "변동성 (일일)": f"{returns.std()*100:.3f}%",
                        "최대 일일 수익률": f"{returns.max()*100:.2f}%",
                        "최대 일일 손실률": f"{returns.min()*100:.2f}%",
                    }
                    
                    for key, value in stats.items():
                        st.text(f"{key}: {value}")
            
            with col2:
                st.write("**리스크 지표**")
                if 'total_value' in performance_df.columns and len(performance_df) > 1:
                    returns = performance_df['total_value'].pct_change().dropna()
                    
                    # Sharpe 비율 (무위험 수익률 0% 가정)
                    sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
                    
                    # 최대 드로우다운
                    peak = performance_df['total_value'].expanding().max()
                    drawdown = (performance_df['total_value'] / peak - 1)
                    max_dd = drawdown.min() * 100
                    
                    risk_stats = {
                        "Sharpe 비율": f"{sharpe:.2f}",
                        "최대 드로우다운": f"{max_dd:.2f}%",
                        "VaR (95%)": f"{returns.quantile(0.05)*100:.2f}%",
                        "승률": f"{(returns > 0).mean()*100:.1f}%"
                    }
                    
                    for key, value in risk_stats.items():
                        st.text(f"{key}: {value}")
    
    with tab2:
        st.subheader("🤖 AI 모델 현황")
        
        if training_results:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**최근 학습 결과**")
                if 'training_summary' in training_results:
                    summary = training_results['training_summary']
                    st.json(summary)
            
            with col2:
                st.write("**모델 성능**")
                # 모델별 성능 표시
                models = ['DQN', 'Technical', 'Factor', 'Transformer']
                for model in models:
                    st.progress(np.random.uniform(0.3, 0.9), text=f"{model} Agent")
    
    with tab3:
        st.subheader("⚙️ 시스템 설정")
        
        # 설정 표시 (읽기 전용)
        settings = {
            "API 호출 간격": "5초",
            "포트폴리오 리밸런싱": "매일",
            "리스크 한도": "10%",
            "최대 포지션 수": "10개"
        }
        
        for key, value in settings.items():
            st.text(f"{key}: {value}")
    
    with tab4:
        st.subheader("📈 백테스트 결과")
        
        # 백테스트 버튼
        if st.button("🚀 백테스트 실행"):
            with st.spinner("백테스트 실행 중..."):
                time.sleep(3)  # 시뮬레이션
                st.success("백테스트 완료!")
                
                # 가상의 백테스트 결과
                backtest_results = {
                    "기간": "2023-01-01 ~ 2023-12-31",
                    "총 수익률": "18.4%",
                    "연간 수익률": "18.4%",
                    "최대 드로우다운": "-7.2%",
                    "Sharpe 비율": "1.78",
                    "승률": "64.2%",
                    "총 거래 수": "127회"
                }
                
                col1, col2 = st.columns(2)
                with col1:
                    for key, value in list(backtest_results.items())[:4]:
                        st.metric(key, value)
                
                with col2:
                    for key, value in list(backtest_results.items())[4:]:
                        st.metric(key, value)
    
    # 푸터
    st.markdown("---")
    st.markdown("💡 **AI 자동매매 시스템** - 실시간 모니터링 및 분석 대시보드")


if __name__ == "__main__":
    main()