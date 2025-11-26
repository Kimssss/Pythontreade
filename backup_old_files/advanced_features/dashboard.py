"""
Streamlit 기반 실시간 트레이딩 대시보드
참조: https://twentytwentyone.tistory.com/1842

[주요 기능]
- 실시간 포트폴리오 모니터링
- 손익 차트 및 성과 지표
- 거래 내역 조회
- 리스크 모니터링
- AI 분석 결과 표시
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import json
from typing import Dict, List, Optional


class TradingDashboard:
    """실시간 트레이딩 대시보드"""
    
    def __init__(self, api, auto_trader_manager):
        self.api = api
        self.auto_trader_manager = auto_trader_manager
        
        # Streamlit 설정
        st.set_page_config(
            page_title="KIS 자동매매 대시보드",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
    def run(self):
        """대시보드 실행"""
        st.title("🏦 한국투자증권 AI 자동매매 대시보드")
        
        # 사이드바
        with st.sidebar:
            st.header("⚙️ 컨트롤 패널")
            
            # 자동매매 제어
            if st.button("🚀 자동매매 시작", type="primary"):
                self.auto_trader_manager.start_trading(60)
                st.success("자동매매가 시작되었습니다!")
                
            if st.button("⏹️ 자동매매 중지"):
                self.auto_trader_manager.stop_trading()
                st.info("자동매매가 중지되었습니다.")
                
            # 새로고침 간격
            refresh_interval = st.slider(
                "새로고침 간격 (초)",
                min_value=5,
                max_value=60,
                value=10,
                step=5
            )
            
            # 전략 선택
            strategies = self.auto_trader_manager.get_available_strategies()
            current_strategy = "crewai"
            if self.auto_trader_manager.trader:
                current_strategy = self.auto_trader_manager.trader.strategy_type
                
            selected_strategy = st.selectbox(
                "전략 선택",
                options=list(strategies.keys()),
                index=list(strategies.keys()).index(current_strategy)
            )
            
            if st.button("전략 변경"):
                self.auto_trader_manager.set_strategy(selected_strategy)
                st.success(f"{strategies[selected_strategy]['name']} 전략으로 변경되었습니다!")
        
        # 메인 대시보드
        self.display_main_dashboard(refresh_interval)
        
    def display_main_dashboard(self, refresh_interval: int):
        """메인 대시보드 표시"""
        
        # 자동 새로고침
        placeholder = st.empty()
        
        while True:
            with placeholder.container():
                # 상태 표시
                col1, col2, col3, col4 = st.columns(4)
                
                # 계좌 정보
                balance_info = self.get_account_info()
                
                with col1:
                    st.metric(
                        "총 평가 금액",
                        f"{balance_info['total_amount']:,}원",
                        f"{balance_info['profit_rate']:.2f}%"
                    )
                    
                with col2:
                    st.metric(
                        "평가 손익",
                        f"{balance_info['profit_amount']:,}원",
                        f"{balance_info['daily_change']:.2f}%"
                    )
                    
                with col3:
                    st.metric(
                        "보유 종목 수",
                        f"{balance_info['stock_count']}개",
                        None
                    )
                    
                with col4:
                    status = self.auto_trader_manager.get_status()
                    if status.get('is_running'):
                        st.metric("자동매매 상태", "🟢 실행 중", None)
                    else:
                        st.metric("자동매매 상태", "🔴 중지됨", None)
                
                st.divider()
                
                # 탭 구성
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📊 포트폴리오", 
                    "📈 성과 분석", 
                    "🤖 AI 분석",
                    "📜 거래 내역",
                    "⚠️ 리스크"
                ])
                
                with tab1:
                    self.display_portfolio()
                    
                with tab2:
                    self.display_performance()
                    
                with tab3:
                    self.display_ai_analysis()
                    
                with tab4:
                    self.display_trade_history()
                    
                with tab5:
                    self.display_risk_monitoring()
                
            # 새로고침
            time.sleep(refresh_interval)
            
    def get_account_info(self) -> Dict:
        """계좌 정보 조회"""
        balance = self.api.get_balance()
        
        if balance and balance.get('rt_cd') == '0':
            output2 = balance.get('output2', [{}])[0]
            
            total_amount = int(output2.get('tot_evlu_amt', 0))
            buy_amount = int(output2.get('pchs_amt_smtl_amt', 0))
            profit_amount = int(output2.get('evlu_pfls_smtl_amt', 0))
            
            profit_rate = (profit_amount / buy_amount * 100) if buy_amount > 0 else 0
            
            # 보유 종목 수
            holdings = self.api.get_holding_stocks()
            stock_count = len(holdings) if holdings else 0
            
            return {
                'total_amount': total_amount,
                'profit_amount': profit_amount,
                'profit_rate': profit_rate,
                'stock_count': stock_count,
                'daily_change': 0  # 일일 변동률 (추가 계산 필요)
            }
        else:
            return {
                'total_amount': 0,
                'profit_amount': 0,
                'profit_rate': 0,
                'stock_count': 0,
                'daily_change': 0
            }
            
    def display_portfolio(self):
        """포트폴리오 표시"""
        st.subheader("💼 현재 포트폴리오")
        
        holdings = self.api.get_holding_stocks()
        
        if holdings:
            # 데이터프레임 생성
            df = pd.DataFrame(holdings)
            
            # 컬럼 정리
            display_df = df[[
                'stock_name', 'stock_code', 'quantity', 
                'buy_price', 'current_price', 'profit_rate'
            ]].copy()
            
            display_df.columns = [
                '종목명', '종목코드', '수량', 
                '매수가', '현재가', '수익률(%)'
            ]
            
            # 수익률에 따라 색상 지정
            def color_profit(val):
                if val > 0:
                    return 'color: red'
                elif val < 0:
                    return 'color: blue'
                else:
                    return ''
                    
            styled_df = display_df.style.applymap(
                color_profit, 
                subset=['수익률(%)']
            )
            
            st.dataframe(styled_df, use_container_width=True)
            
            # 포트폴리오 구성 차트
            if len(holdings) > 0:
                fig = px.pie(
                    df, 
                    values='current_value', 
                    names='stock_name',
                    title="포트폴리오 구성"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("보유 종목이 없습니다.")
            
    def display_performance(self):
        """성과 분석 표시"""
        st.subheader("📈 투자 성과 분석")
        
        # 수익률 차트 (시뮬레이션 데이터)
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=30),
            end=datetime.now(),
            freq='D'
        )
        
        # 임시 데이터 생성 (실제로는 거래 기록에서 계산)
        import numpy as np
        cumulative_returns = np.random.randn(len(dates)).cumsum() + 100
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=cumulative_returns,
            mode='lines',
            name='누적 수익률',
            line=dict(color='blue', width=2)
        ))
        
        fig.update_layout(
            title="누적 수익률 추이",
            xaxis_title="날짜",
            yaxis_title="수익률 (%)",
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 성과 지표
        col1, col2, col3, col4 = st.columns(4)
        
        # 실제로는 거래 기록에서 계산
        with col1:
            st.metric("Sharpe Ratio", "1.45", "↑ 0.12")
        with col2:
            st.metric("최대 낙폭", "-3.2%", "↓ 0.5%")
        with col3:
            st.metric("승률", "62.5%", "↑ 2.3%")
        with col4:
            st.metric("평균 보유일", "2.8일", "↓ 0.2일")
            
    def display_ai_analysis(self):
        """AI 분석 결과 표시"""
        st.subheader("🤖 AI 분석 현황")
        
        if not self.auto_trader_manager.trader:
            st.warning("자동매매가 설정되지 않았습니다.")
            return
            
        # 현재 전략 정보
        strategy_type = self.auto_trader_manager.trader.strategy_type
        st.info(f"현재 전략: {strategy_type.upper()}")
        
        # 최근 분석 결과 (있다면)
        if hasattr(self.auto_trader_manager.trader.strategy, 'trade_history'):
            recent_trades = self.auto_trader_manager.trader.strategy.trade_history[-5:]
            
            if recent_trades:
                st.write("**최근 AI 분석 결과:**")
                
                for trade in recent_trades:
                    timestamp = datetime.fromisoformat(trade['timestamp'])
                    
                    if trade['type'] == 'ANALYSIS':
                        col1, col2, col3 = st.columns([2, 1, 3])
                        
                        with col1:
                            st.write(f"**{trade.get('name', 'N/A')}**")
                            st.caption(trade.get('code', 'N/A'))
                            
                        with col2:
                            signal = trade.get('signal', 'HOLD')
                            if signal == 'BUY':
                                st.success(signal)
                            elif signal == 'SELL':
                                st.error(signal)
                            else:
                                st.info(signal)
                                
                        with col3:
                            st.write(trade.get('reason', 'N/A'))
                            st.caption(f"신뢰도: {trade.get('confidence', 0)}%")
                            
                        st.divider()
                        
        # CrewAI/Ollama 상태
        if strategy_type == 'crewai':
            if hasattr(self.auto_trader_manager.trader.strategy, 'crewai_available'):
                if self.auto_trader_manager.trader.strategy.crewai_available:
                    st.success("✅ Ollama AI 엔진 활성화")
                else:
                    st.warning("⚠️ AI 엔진 미활성화 (규칙 기반 모드)")
                    
    def display_trade_history(self):
        """거래 내역 표시"""
        st.subheader("📜 거래 내역")
        
        # 거래 내역 조회 (실제로는 DB나 파일에서 로드)
        if hasattr(self.auto_trader_manager.trader, 'strategy'):
            strategy = self.auto_trader_manager.trader.strategy
            if hasattr(strategy, 'trade_history'):
                trades = strategy.trade_history
                
                if trades:
                    # 데이터프레임 생성
                    df = pd.DataFrame(trades)
                    
                    # 시간 포맷팅
                    if 'timestamp' in df.columns:
                        df['시간'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                        
                    # 표시할 컬럼 선택
                    display_columns = ['시간', 'type', 'code', 'name', 'quantity', 'price']
                    display_columns = [col for col in display_columns if col in df.columns]
                    
                    if display_columns:
                        st.dataframe(
                            df[display_columns].tail(20),  # 최근 20개
                            use_container_width=True
                        )
                    else:
                        st.info("표시할 거래 내역이 없습니다.")
                else:
                    st.info("거래 내역이 없습니다.")
                    
    def display_risk_monitoring(self):
        """리스크 모니터링 표시"""
        st.subheader("⚠️ 리스크 모니터링")
        
        # 리스크 지표
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 포지션 집중도
            holdings = self.api.get_holding_stocks()
            if holdings:
                max_position = max([h.get('current_value', 0) for h in holdings])
                total_value = sum([h.get('current_value', 0) for h in holdings])
                concentration = (max_position / total_value * 100) if total_value > 0 else 0
                
                st.metric(
                    "최대 포지션 비중",
                    f"{concentration:.1f}%",
                    None
                )
                
                if concentration > 30:
                    st.error("⚠️ 포지션 집중도가 높습니다!")
            else:
                st.metric("최대 포지션 비중", "0%", None)
                
        with col2:
            # 손실 종목 수
            if holdings:
                loss_count = sum(1 for h in holdings if h.get('profit_rate', 0) < 0)
                st.metric(
                    "손실 종목 수",
                    f"{loss_count}개",
                    None
                )
                
                if loss_count > len(holdings) * 0.5:
                    st.warning("⚠️ 손실 종목이 많습니다!")
            else:
                st.metric("손실 종목 수", "0개", None)
                
        with col3:
            # 일일 매매 횟수
            if hasattr(self.auto_trader_manager.trader, 'strategy'):
                strategy = self.auto_trader_manager.trader.strategy
                if hasattr(strategy, 'daily_buy_count'):
                    st.metric(
                        "오늘 매매 횟수",
                        f"{strategy.daily_buy_count}회",
                        None
                    )
                else:
                    st.metric("오늘 매매 횟수", "0회", None)
                    
        # 리스크 경고
        st.divider()
        
        alerts = []
        
        # 계좌 정보 체크
        balance_info = self.get_account_info()
        if balance_info['profit_rate'] < -5:
            alerts.append(("danger", f"총 손실률이 {balance_info['profit_rate']:.1f}%입니다!"))
            
        # 보유 종목 체크
        if holdings:
            for holding in holdings:
                if holding.get('profit_rate', 0) < -10:
                    alerts.append((
                        "warning", 
                        f"{holding['stock_name']} 손실률 {holding['profit_rate']:.1f}%"
                    ))
                    
        # 경고 표시
        if alerts:
            st.write("**리스크 경고:**")
            for alert_type, message in alerts:
                if alert_type == "danger":
                    st.error(message)
                else:
                    st.warning(message)
        else:
            st.success("✅ 현재 리스크 수준은 정상입니다.")


def run_dashboard(api, auto_trader_manager):
    """대시보드 실행 함수"""
    dashboard = TradingDashboard(api, auto_trader_manager)
    dashboard.run()