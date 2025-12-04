#!/usr/bin/env python3
"""
AI 트레이딩 시스템 백테스팅 실행 스크립트
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 프로젝트 경로 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / 'ai_trading_system'))

# 환경변수 로드
load_dotenv()

try:
    from ai_trading_system.utils.kis_api import KisAPIEnhanced
    from ai_trading_system.backtesting.strategy_backtester import StrategyBacktester
    import logging
except ImportError as e:
    print(f"Import 오류: {e}")
    print("필요한 의존성을 설치하세요.")
    sys.exit(1)


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'backtest_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8')
        ]
    )


def parse_date(date_str: str) -> datetime:
    """날짜 문자열 파싱"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"날짜 형식이 올바르지 않습니다: {date_str}. YYYY-MM-DD 형식을 사용하세요.")


async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='AI 트레이딩 시스템 백테스터')
    
    # 기본 날짜 설정 (최근 3개월)
    default_end = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    default_start = default_end - timedelta(days=90)
    
    parser.add_argument(
        '--start-date',
        type=parse_date,
        default=default_start,
        help=f'백테스트 시작일 (YYYY-MM-DD, 기본값: {default_start.strftime("%Y-%m-%d")})'
    )
    parser.add_argument(
        '--end-date',
        type=parse_date,
        default=default_end,
        help=f'백테스트 종료일 (YYYY-MM-DD, 기본값: {default_end.strftime("%Y-%m-%d")})'
    )
    parser.add_argument(
        '--capital',
        type=float,
        default=10000000,
        help='초기 자본 (기본값: 10,000,000원)'
    )
    parser.add_argument(
        '--market',
        choices=['domestic', 'overseas', 'both'],
        default='both',
        help='백테스트 시장 (기본값: both)'
    )
    parser.add_argument(
        '--mode',
        choices=['demo', 'real'],
        default='demo',
        help='API 모드 (기본값: demo)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='backtest_results',
        help='결과 출력 디렉토리 (기본값: backtest_results)'
    )
    
    args = parser.parse_args()
    
    # 로깅 설정
    setup_logging()
    logger = logging.getLogger('backtest_main')
    
    print("🚀 AI 트레이딩 시스템 백테스터")
    print("=" * 60)
    print(f"📅 백테스트 기간: {args.start_date.strftime('%Y-%m-%d')} ~ {args.end_date.strftime('%Y-%m-%d')}")
    print(f"💰 초기 자본: {args.capital:,.0f}원")
    print(f"📈 대상 시장: {args.market}")
    print(f"🔧 API 모드: {args.mode}")
    print("=" * 60)
    
    # 날짜 유효성 검사
    if args.start_date >= args.end_date:
        logger.error("시작일이 종료일보다 늦습니다.")
        return
        
    if args.end_date > datetime.now():
        logger.warning("종료일이 현재 날짜보다 미래입니다. 현재 날짜로 조정합니다.")
        args.end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    try:
        # KIS API 초기화
        print("🔧 KIS API 초기화 중...")
        
        api_mode = args.mode.upper()
        api = KisAPIEnhanced(
            appkey=os.getenv(f'KIS_{api_mode}_APPKEY'),
            appsecret=os.getenv(f'KIS_{api_mode}_APPSECRET'),
            account_no=os.getenv(f'KIS_{api_mode}_ACCOUNT'),
            is_real=(args.mode == 'real')
        )
        
        # 토큰 발급
        if not api.get_access_token():
            logger.error("API 토큰 발급 실패")
            return
            
        print("✅ KIS API 초기화 완료")
        
        # 백테스터 초기화
        print("🎯 백테스터 초기화 중...")
        backtester = StrategyBacktester(
            kis_api=api,
            start_date=args.start_date,
            end_date=args.end_date,
            initial_capital=args.capital
        )
        
        print("✅ 백테스터 초기화 완료")
        
        # 백테스트 실행
        if args.market == 'both':
            print("📊 종합 백테스트 실행 중...")
            results = await backtester.run_comprehensive_backtest()
        else:
            print(f"📊 {args.market} 백테스트 실행 중...")
            results = {args.market: await backtester.run_backtest(args.market)}
            backtester.results = results
            
        # 결과 저장
        print("💾 결과 저장 중...")
        backtester.save_results(args.output_dir)
        
        # 결과 요약 출력
        print("\n" + "=" * 60)
        print("📋 백테스트 결과 요약")
        print("=" * 60)
        
        for market, result in results.items():
            if not result:
                continue
                
            print(f"\n🎯 {market.upper()} 시장:")
            print("-" * 40)
            
            perf = result.get('performance', {})
            trading = result.get('trading_summary', {})
            
            print(f"  💰 총 수익률: {perf.get('total_return', 0)*100:+.2f}%")
            print(f"  📈 연간 수익률: {perf.get('annual_return', 0)*100:+.2f}%")
            print(f"  🎯 샤프 비율: {perf.get('sharpe_ratio', 0):.3f}")
            print(f"  📉 최대 낙폭: {perf.get('max_drawdown', 0)*100:.2f}%")
            print(f"  🎲 승률: {perf.get('win_rate', 0)*100:.1f}%")
            print(f"  🏁 최종 자산: {perf.get('final_value', 0):,.0f}원")
            print(f"  💸 손익: {perf.get('profit_loss', 0):+,.0f}원")
            print(f"  🔄 총 거래: {trading.get('total_trades', 0)}회")
            
        print(f"\n📁 상세 결과가 '{args.output_dir}' 폴더에 저장되었습니다.")
        print("✅ 백테스트 완료!")
        
    except KeyboardInterrupt:
        logger.info("사용자에 의해 백테스트가 중단되었습니다.")
    except Exception as e:
        logger.error(f"백테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())