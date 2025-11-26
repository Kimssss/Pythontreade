"""
AI 기반 자동 리포트 생성
참조: https://twentytwentyone.tistory.com/361

[주요 기능]
- 투자 분석 리포트 자동 생성
- 일일/주간/월간 리포트
- 종목별 상세 분석
- PDF/HTML 형식 출력
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from jinja2 import Template
import pdfkit
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64


class AIReportGenerator:
    """AI 기반 리포트 생성기"""
    
    def __init__(self, api, auto_trader_manager):
        self.api = api
        self.auto_trader_manager = auto_trader_manager
        
        # 리포트 템플릿
        self.report_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: 'Nanum Gothic', sans-serif;
            margin: 40px;
            line-height: 1.6;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        .header {
            background-color: #3498db;
            color: white;
            padding: 20px;
            margin: -40px -40px 20px -40px;
        }
        .metric {
            display: inline-block;
            margin: 10px 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        .profit {
            color: #e74c3c;
        }
        .loss {
            color: #3498db;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #34495e;
            color: white;
        }
        .chart {
            margin: 20px 0;
            text-align: center;
        }
        .analysis-box {
            background-color: #ecf0f1;
            padding: 15px;
            margin: 15px 0;
            border-left: 4px solid #3498db;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p>{{ date_range }}</p>
    </div>
    
    <h2>📊 투자 성과 요약</h2>
    <div class="metrics">
        <div class="metric">
            <div class="metric-label">총 평가금액</div>
            <div class="metric-value">{{ total_amount }}</div>
        </div>
        <div class="metric">
            <div class="metric-label">평가 손익</div>
            <div class="metric-value {% if profit_amount > 0 %}profit{% else %}loss{% endif %}">
                {{ profit_amount }}
            </div>
        </div>
        <div class="metric">
            <div class="metric-label">수익률</div>
            <div class="metric-value {% if profit_rate > 0 %}profit{% else %}loss{% endif %}">
                {{ profit_rate }}%
            </div>
        </div>
        <div class="metric">
            <div class="metric-label">승률</div>
            <div class="metric-value">{{ win_rate }}%</div>
        </div>
    </div>
    
    <h2>💼 포트폴리오 현황</h2>
    {{ portfolio_table }}
    
    <div class="chart">
        <img src="data:image/png;base64,{{ portfolio_chart }}" width="600">
    </div>
    
    <h2>🤖 AI 분석 결과</h2>
    {{ ai_analysis }}
    
    <h2>📈 거래 내역</h2>
    {{ trade_history_table }}
    
    <h2>💡 투자 인사이트</h2>
    <div class="analysis-box">
        {{ investment_insights }}
    </div>
    
    <h2>⚠️ 리스크 분석</h2>
    <div class="analysis-box">
        {{ risk_analysis }}
    </div>
    
    <h2>📅 다음 주 전망</h2>
    <div class="analysis-box">
        {{ next_week_outlook }}
    </div>
    
    <div class="footer">
        <p>이 리포트는 AI 자동매매 시스템에 의해 자동으로 생성되었습니다.</p>
        <p>생성일시: {{ generated_at }}</p>
        <p>전략: {{ strategy_name }}</p>
    </div>
</body>
</html>
        """
        
    def generate_report(self, report_type: str = "daily") -> str:
        """리포트 생성"""
        print(f"\n📄 {report_type} 리포트 생성 중...")
        
        # 데이터 수집
        data = self.collect_report_data(report_type)
        
        # 차트 생성
        portfolio_chart = self.create_portfolio_chart(data['holdings'])
        
        # AI 분석 결과 정리
        ai_analysis = self.format_ai_analysis(data['ai_results'])
        
        # 투자 인사이트 생성
        insights = self.generate_insights(data)
        
        # 리스크 분석
        risk_analysis = self.analyze_risks(data)
        
        # 다음 주 전망
        outlook = self.generate_outlook(data)
        
        # 템플릿 렌더링
        template = Template(self.report_template)
        html_content = template.render(
            title=f"KIS AI 자동매매 {report_type.upper()} 리포트",
            date_range=self.get_date_range(report_type),
            total_amount=f"{data['balance']['total_amount']:,}원",
            profit_amount=f"{data['balance']['profit_amount']:,}원",
            profit_rate=f"{data['balance']['profit_rate']:.2f}",
            win_rate=f"{data['performance']['win_rate']:.1f}",
            portfolio_table=self.create_portfolio_table(data['holdings']),
            portfolio_chart=portfolio_chart,
            ai_analysis=ai_analysis,
            trade_history_table=self.create_trade_history_table(data['trades']),
            investment_insights=insights,
            risk_analysis=risk_analysis,
            next_week_outlook=outlook,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            strategy_name=data['strategy_name']
        )
        
        # 파일 저장
        filename = self.save_report(html_content, report_type)
        
        print(f"✅ 리포트 생성 완료: {filename}")
        return filename
        
    def collect_report_data(self, report_type: str) -> Dict:
        """리포트용 데이터 수집"""
        # 계좌 정보
        balance = self.api.get_balance()
        balance_data = {
            'total_amount': 0,
            'profit_amount': 0,
            'profit_rate': 0
        }
        
        if balance and balance.get('rt_cd') == '0':
            output2 = balance.get('output2', [{}])[0]
            balance_data['total_amount'] = int(output2.get('tot_evlu_amt', 0))
            balance_data['profit_amount'] = int(output2.get('evlu_pfls_smtl_amt', 0))
            buy_amount = int(output2.get('pchs_amt_smtl_amt', 1))
            balance_data['profit_rate'] = (balance_data['profit_amount'] / buy_amount * 100) if buy_amount > 0 else 0
        
        # 보유 종목
        holdings = self.api.get_holding_stocks() or []
        
        # 거래 내역
        trades = []
        if self.auto_trader_manager.trader and hasattr(self.auto_trader_manager.trader.strategy, 'trade_history'):
            trades = self.auto_trader_manager.trader.strategy.trade_history[-50:]  # 최근 50개
        
        # AI 분석 결과
        ai_results = []
        if trades:
            ai_results = [t for t in trades if t.get('type') == 'ANALYSIS'][-10:]  # 최근 10개
        
        # 성과 지표
        performance = self.calculate_performance(trades)
        
        # 전략 이름
        strategy_name = "N/A"
        if self.auto_trader_manager.trader:
            strategy_name = self.auto_trader_manager.trader.strategy_type.upper()
        
        return {
            'balance': balance_data,
            'holdings': holdings,
            'trades': trades,
            'ai_results': ai_results,
            'performance': performance,
            'strategy_name': strategy_name
        }
    
    def calculate_performance(self, trades: List[Dict]) -> Dict:
        """성과 지표 계산"""
        if not trades:
            return {'win_rate': 0, 'total_trades': 0, 'profit_trades': 0}
        
        # 매매 기록만 필터
        buy_sells = [t for t in trades if t.get('type') in ['BUY', 'SELL']]
        
        # 승률 계산 (간단히)
        profit_trades = len([t for t in buy_sells if t.get('profit_rate', 0) > 0])
        total_trades = len(buy_sells)
        
        win_rate = (profit_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'win_rate': win_rate,
            'total_trades': total_trades,
            'profit_trades': profit_trades
        }
    
    def create_portfolio_table(self, holdings: List[Dict]) -> str:
        """포트폴리오 테이블 생성"""
        if not holdings:
            return "<p>보유 종목이 없습니다.</p>"
        
        html = """
        <table>
            <thead>
                <tr>
                    <th>종목명</th>
                    <th>종목코드</th>
                    <th>수량</th>
                    <th>매수가</th>
                    <th>현재가</th>
                    <th>평가금액</th>
                    <th>수익률</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for holding in holdings:
            profit_class = "profit" if holding.get('profit_rate', 0) > 0 else "loss"
            html += f"""
                <tr>
                    <td>{holding.get('stock_name', 'N/A')}</td>
                    <td>{holding.get('stock_code', 'N/A')}</td>
                    <td>{holding.get('quantity', 0):,}</td>
                    <td>{holding.get('buy_price', 0):,}원</td>
                    <td>{holding.get('current_price', 0):,}원</td>
                    <td>{holding.get('current_value', 0):,}원</td>
                    <td class="{profit_class}">{holding.get('profit_rate', 0):.2f}%</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def create_portfolio_chart(self, holdings: List[Dict]) -> str:
        """포트폴리오 차트 생성"""
        if not holdings:
            return ""
        
        # 차트 생성
        plt.figure(figsize=(8, 6))
        
        names = [h.get('stock_name', 'N/A') for h in holdings]
        values = [h.get('current_value', 0) for h in holdings]
        
        plt.pie(values, labels=names, autopct='%1.1f%%')
        plt.title('포트폴리오 구성')
        
        # Base64 인코딩
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        chart_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return chart_base64
    
    def format_ai_analysis(self, ai_results: List[Dict]) -> str:
        """AI 분석 결과 포맷팅"""
        if not ai_results:
            return "<p>최근 AI 분석 결과가 없습니다.</p>"
        
        html = ""
        for result in ai_results[:5]:  # 최근 5개
            signal_class = "profit" if result.get('signal') == 'BUY' else "loss"
            html += f"""
            <div class="analysis-box">
                <h4>{result.get('name', 'N/A')} ({result.get('code', 'N/A')})</h4>
                <p><strong>신호:</strong> <span class="{signal_class}">{result.get('signal', 'N/A')}</span></p>
                <p><strong>신뢰도:</strong> {result.get('confidence', 0)}%</p>
                <p><strong>분석:</strong> {result.get('reason', 'N/A')}</p>
                <p><small>분석시간: {result.get('timestamp', 'N/A')}</small></p>
            </div>
            """
        
        return html
    
    def create_trade_history_table(self, trades: List[Dict]) -> str:
        """거래 내역 테이블 생성"""
        if not trades:
            return "<p>거래 내역이 없습니다.</p>"
        
        # 최근 거래만
        recent_trades = [t for t in trades if t.get('type') in ['BUY', 'SELL']][-20:]
        
        if not recent_trades:
            return "<p>최근 거래 내역이 없습니다.</p>"
        
        html = """
        <table>
            <thead>
                <tr>
                    <th>시간</th>
                    <th>유형</th>
                    <th>종목명</th>
                    <th>수량</th>
                    <th>가격</th>
                    <th>금액</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for trade in recent_trades:
            trade_type = "매수" if trade.get('type') == 'BUY' else "매도"
            amount = trade.get('quantity', 0) * trade.get('price', 0)
            
            html += f"""
                <tr>
                    <td>{trade.get('timestamp', 'N/A')}</td>
                    <td>{trade_type}</td>
                    <td>{trade.get('name', 'N/A')}</td>
                    <td>{trade.get('quantity', 0):,}</td>
                    <td>{trade.get('price', 0):,}원</td>
                    <td>{amount:,}원</td>
                </tr>
            """
        
        html += """
            </tbody>
        </table>
        """
        
        return html
    
    def generate_insights(self, data: Dict) -> str:
        """투자 인사이트 생성"""
        insights = []
        
        # 수익률 기반 인사이트
        profit_rate = data['balance']['profit_rate']
        if profit_rate > 5:
            insights.append("✅ 우수한 수익률을 기록하고 있습니다. 현재 전략이 시장에 잘 맞고 있습니다.")
        elif profit_rate > 0:
            insights.append("✅ 안정적인 플러스 수익을 유지하고 있습니다.")
        else:
            insights.append("⚠️ 현재 손실 상태입니다. 리스크 관리에 더 신경쓸 필요가 있습니다.")
        
        # 포트폴리오 분석
        holdings = data['holdings']
        if len(holdings) > 5:
            insights.append("📊 포트폴리오가 다소 분산되어 있습니다. 집중 투자를 고려해보세요.")
        elif len(holdings) == 0:
            insights.append("💰 현재 보유 종목이 없습니다. 좋은 매수 기회를 찾고 있습니다.")
        
        # 승률 분석
        win_rate = data['performance']['win_rate']
        if win_rate > 60:
            insights.append(f"🎯 {win_rate:.1f}%의 높은 승률을 보이고 있습니다.")
        elif win_rate < 40:
            insights.append(f"⚠️ 승률이 {win_rate:.1f}%로 낮습니다. 전략 조정이 필요할 수 있습니다.")
        
        return "<br>".join(insights)
    
    def analyze_risks(self, data: Dict) -> str:
        """리스크 분석"""
        risks = []
        
        # 손실 종목 분석
        holdings = data['holdings']
        if holdings:
            loss_stocks = [h for h in holdings if h.get('profit_rate', 0) < -5]
            if loss_stocks:
                for stock in loss_stocks:
                    risks.append(f"⚠️ {stock['stock_name']}: {stock['profit_rate']:.1f}% 손실")
        
        # 포지션 집중도
        if holdings and len(holdings) < 3:
            risks.append("⚠️ 포지션이 소수 종목에 집중되어 있습니다.")
        
        # 전체 손실률
        if data['balance']['profit_rate'] < -3:
            risks.append(f"🚨 총 손실률이 {data['balance']['profit_rate']:.1f}%입니다.")
        
        if not risks:
            risks.append("✅ 현재 특별한 리스크는 감지되지 않았습니다.")
        
        return "<br>".join(risks)
    
    def generate_outlook(self, data: Dict) -> str:
        """다음 주 전망"""
        outlook = []
        
        # 현재 전략 기반
        strategy = data['strategy_name']
        
        if strategy == "CREWAI":
            outlook.append("🤖 AI가 시장 상황을 지속적으로 모니터링하며 최적의 매매 시점을 포착할 예정입니다.")
        elif strategy == "DQN":
            outlook.append("🧠 강화학습 모델이 더 많은 데이터를 학습하며 성능이 개선될 것으로 예상됩니다.")
        
        # 시장 상황 (실제로는 외부 데이터 필요)
        outlook.append("📈 현재 시장은 변동성이 높은 상황입니다. 신중한 접근이 필요합니다.")
        
        # 전략 제안
        if data['performance']['win_rate'] < 50:
            outlook.append("💡 승률 개선을 위해 매매 조건을 더 엄격하게 조정할 예정입니다.")
        
        return "<br>".join(outlook)
    
    def get_date_range(self, report_type: str) -> str:
        """리포트 기간 반환"""
        end_date = datetime.now()
        
        if report_type == "daily":
            start_date = end_date.replace(hour=0, minute=0, second=0)
        elif report_type == "weekly":
            start_date = end_date - timedelta(days=7)
        else:  # monthly
            start_date = end_date - timedelta(days=30)
        
        return f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
    
    def save_report(self, html_content: str, report_type: str) -> str:
        """리포트 저장"""
        # reports 디렉토리 생성
        os.makedirs("reports", exist_ok=True)
        
        # 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reports/{report_type}_report_{timestamp}.html"
        
        # HTML 저장
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # PDF로도 저장 (wkhtmltopdf 설치 필요)
        try:
            pdf_filename = filename.replace('.html', '.pdf')
            pdfkit.from_string(html_content, pdf_filename)
            print(f"   PDF 저장: {pdf_filename}")
        except Exception as e:
            print(f"   PDF 변환 실패: {e}")
        
        return filename
    
    def schedule_reports(self):
        """정기 리포트 스케줄링"""
        import schedule
        import time
        
        # 일일 리포트 (매일 오후 4시)
        schedule.every().day.at("16:00").do(lambda: self.generate_report("daily"))
        
        # 주간 리포트 (매주 금요일 오후 4시)
        schedule.every().friday.at("16:00").do(lambda: self.generate_report("weekly"))
        
        # 월간 리포트 (매월 마지막 날)
        # schedule.every().month.do(lambda: self.generate_report("monthly"))
        
        print("📅 리포트 스케줄 설정 완료")
        print("   - 일일 리포트: 매일 오후 4시")
        print("   - 주간 리포트: 매주 금요일 오후 4시")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크