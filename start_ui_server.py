#!/usr/bin/env python3
"""
AI 트레이딩 시스템 UI 서버 단독 실행
"""
import os
import sys
import socket
import webbrowser
from pathlib import Path

# 프로젝트 경로 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def get_local_ip():
    """로컬 IP 주소 획득"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def main():
    print("\n" + "="*60)
    print("🌐 AI TRADING SYSTEM - UI SERVER")
    print("="*60)
    
    try:
        from ai_trading_system.web_dashboard import app, socketio
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please install required packages: pip install flask flask-socketio flask-cors")
        sys.exit(1)
    
    # IP 정보 표시
    port = 8080  # 5000 대신 8080 사용
    local_ip = get_local_ip()
    local_url = f"http://127.0.0.1:{port}"
    external_url = f"http://{local_ip}:{port}"
    
    print("\n📡 Starting UI server...")
    print(f"🏠 Local access: {local_url}")
    
    if local_ip != "127.0.0.1":
        print(f"🌍 External access: {external_url}")
        print(f"ℹ️  Other devices on network can access: {external_url}")
        print(f"⚠️  Check firewall settings (Port {port})")
    
    print("\n📋 Available endpoints:")
    print("   GET  / - Main dashboard")
    print("   GET  /api/status - System status")
    print("   GET  /api/portfolio - Portfolio data")
    print("   GET  /api/trades - Trading history")
    print("   GET  /api/performance - Performance metrics")
    print("   GET  /api/logs - System logs")
    
    print(f"\n🚀 Starting server on 0.0.0.0:{port}...")
    print("Press Ctrl+C to stop\n")
    
    # 브라우저 열기 (선택사항)
    try:
        import time
        import threading
        
        def open_browser():
            time.sleep(2)  # 서버 시작 대기
            webbrowser.open(local_url)
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
    except:
        pass
    
    # 서버 실행
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=port, 
        debug=False, 
        allow_unsafe_werkzeug=True
    )

if __name__ == "__main__":
    main()