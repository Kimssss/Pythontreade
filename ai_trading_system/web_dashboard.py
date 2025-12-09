"""
AI 자동매매 시스템 웹 대시보드
"""
import os
import json
import asyncio
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import queue

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# 전역 변수로 거래 시스템 참조
trading_system = None
message_queue = queue.Queue()

def set_trading_system(system):
    """거래 시스템 설정"""
    global trading_system
    trading_system = system

@app.route('/')
def index():
    """메인 대시보드 페이지"""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """시스템 상태 조회"""
    if not trading_system:
        return jsonify({'status': 'not_initialized'})
    
    return jsonify({
        'status': 'running' if trading_system.is_running else 'stopped',
        'mode': trading_system.mode,
        'total_value': trading_system.total_value,
        'cash_balance': trading_system.cash_balance,
        'positions': len(trading_system.portfolio),
        'active_markets': trading_system.get_active_markets() if hasattr(trading_system, 'get_active_markets') else {},
        'timestamp': datetime.now().isoformat(),
        'agents_active': ['DQN', 'Technical', 'Factor', 'Transformer'],
        'system_health': 'healthy',
        'last_update': datetime.now().strftime('%H:%M:%S'),
        'uptime_seconds': getattr(trading_system, 'uptime_seconds', 0)
    })

@app.route('/api/portfolio')
def get_portfolio():
    """포트폴리오 조회"""
    if not trading_system:
        return jsonify({'portfolio': {}, 'total_value': 0})
    
    portfolio_list = []
    for code, data in trading_system.portfolio.items():
        portfolio_list.append({
            'code': code,
            'name': data.get('name', 'Unknown'),
            'quantity': data.get('quantity', 0),
            'avg_price': data.get('avg_price', 0),
            'current_price': data.get('current_price', 0),
            'value': data.get('value', 0),
            'profit_loss': data.get('profit_loss', 0),
            'profit_rate': data.get('profit_rate', 0)
        })
    
    return jsonify({
        'portfolio': portfolio_list,
        'total_value': trading_system.total_value,
        'cash_balance': trading_system.cash_balance
    })

@app.route('/api/trades')
def get_trades():
    """최근 거래 내역 조회"""
    if not trading_system:
        return jsonify({'trades': []})
    
    # 최근 50개 거래만 반환
    trades = []
    for trade in trading_system.trade_history[-50:]:
        trades.append({
            'timestamp': trade['timestamp'].isoformat(),
            'stock_code': trade['stock_code'],
            'stock_name': trade['stock_name'],
            'action': trade['action'],
            'quantity': trade['quantity'],
            'price': trade['price'],
            'order_no': trade.get('order_no', 'N/A')
        })
    
    return jsonify({'trades': trades[::-1]})  # 최신순

@app.route('/api/performance')
def get_performance():
    """성과 데이터 조회"""
    if not trading_system:
        return jsonify({'performance': []})
    
    # 최근 100개 성과 데이터
    perf_data = []
    for perf in trading_system.performance_history[-100:]:
        perf_data.append({
            'timestamp': perf['timestamp'].isoformat(),
            'total_value': perf['total_value'],
            'cash_balance': perf['cash_balance'],
            'daily_return': perf.get('daily_return', 0),
            'positions': perf.get('positions', 0)
        })
    
    return jsonify({'performance': perf_data})

@app.route('/api/logs')
def get_logs():
    """최근 로그 조회"""
    logs = []
    while not message_queue.empty():
        try:
            logs.append(message_queue.get_nowait())
        except:
            break
    
    return jsonify({'logs': logs[-100:]})  # 최근 100개

@socketio.on('connect')
def handle_connect():
    """WebSocket 연결"""
    emit('connected', {'data': 'Connected to trading system'})

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket 연결 해제"""
    print('Client disconnected')

def emit_update(event_type, data):
    """실시간 업데이트 전송"""
    try:
        socketio.emit(event_type, data)
    except Exception as e:
        print(f"WebSocket emit error: {e}")

def run_server(host='0.0.0.0', port=5000):
    """서버 실행 - 외부 접근 허용"""
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)