"""
AI 자동매매 시스템 설정 파일
"""
import os
from pathlib import Path

# 프로젝트 루트 디렉토리
BASE_DIR = Path(__file__).resolve().parent.parent

# 한국투자증권 API 설정
KIS_CONFIG = {
    'demo': {
        'appkey': os.environ.get('KIS_DEMO_APPKEY', ''),
        'appsecret': os.environ.get('KIS_DEMO_APPSECRET', ''),
        'account': os.environ.get('KIS_DEMO_ACCOUNT', ''),
        'is_real': False
    },
    'real': {
        'appkey': os.environ.get('KIS_REAL_APPKEY', ''),
        'appsecret': os.environ.get('KIS_REAL_APPSECRET', ''),
        'account': os.environ.get('KIS_REAL_ACCOUNT', ''),
        'is_real': True
    },
    'MIN_REQUEST_INTERVAL': 5.0,  # API 호출 최소 간격 (초) - 500 에러 방지를 위해 5초로 증가
    'MAX_RETRIES': 5,  # 재시도 횟수 증가
    'TIMEOUT': 30,
}

# 거래 설정
TRADING_CONFIG = {
    'max_position_size': 0.1,      # 개별 종목 최대 10%
    'max_sector_exposure': 0.3,    # 섹터별 최대 30%
    'max_drawdown_limit': 0.15,    # 최대 낙폭 15%
    'var_limit': 0.02,            # 일일 VaR 2%
    'min_confidence': 0.7,        # 최소 신뢰도 70%
    'stop_loss_rate': 0.05,       # 손절 5%
    'take_profit_rate': 0.1,      # 익절 10%
}

# 모델 설정
MODEL_CONFIG = {
    'dqn': {
        'state_size': 31,
        'action_size': 3,
        'learning_rate': 0.001,
        'epsilon': 1.0,
        'epsilon_min': 0.01,
        'epsilon_decay': 0.995,
        'gamma': 0.95,
        'batch_size': 32,
        'memory_size': 2000,
        'update_target_freq': 100
    },
    'ensemble_weights': {
        'dqn_agent': 0.4,
        'factor_agent': 0.3,
        'technical_agent': 0.3
    }
}

# 데이터 설정
DATA_CONFIG = {
    'lookback_days': 60,          # 분석 기간
    'update_interval': 60,        # 데이터 업데이트 주기 (초)
    'cache_ttl': 300,            # 캐시 만료 시간 (초)
}

# 기술적 지표 설정
TECHNICAL_INDICATORS = {
    'sma_periods': [5, 20, 60, 120],
    'ema_periods': [12, 26],
    'rsi_period': 14,
    'macd_params': (12, 26, 9),
    'bb_params': (20, 2),
    'volume_ma_period': 20
}

# 팩터 투자 설정
FACTOR_CONFIG = {
    'value_factors': ['PER', 'PBR', 'PCR', 'PSR'],
    'quality_factors': ['ROE', 'ROA', 'DebtRatio', 'InterestCoverage'],
    'momentum_factors': ['Returns_1M', 'Returns_3M', 'Returns_6M'],
    'growth_factors': ['EPS_Growth', 'Revenue_Growth', 'FCF_Growth'],
    'weights': {
        'value': 0.4,
        'quality': 0.3,
        'momentum': 0.2,
        'growth': 0.1
    }
}

# 종목 스크리닝 설정
SCREENING_CONFIG = {
    'min_market_cap': 1000,       # 최소 시가총액 (억원)
    'min_volume': 1000000,        # 최소 거래량
    'max_per': 30,               # 최대 PER
    'min_roe': 5,                # 최소 ROE
    'exclude_sectors': ['금융', '보험'],  # 제외 섹터
    'top_n_stocks': 50           # 상위 종목 수
}

# 로깅 설정
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': str(BASE_DIR / 'logs' / 'ai_trading.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': str(BASE_DIR / 'logs' / 'errors.log'),
            'maxBytes': 10485760,
            'backupCount': 5
        }
    },
    'loggers': {
        'ai_trading': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        }
    }
}

# Redis 설정
REDIS_CONFIG = {
    'host': os.environ.get('REDIS_HOST', 'localhost'),
    'port': int(os.environ.get('REDIS_PORT', 6379)),
    'db': 0,
    'decode_responses': True
}

# PostgreSQL 설정
DATABASE_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'database': os.environ.get('DB_NAME', 'trading'),
    'user': os.environ.get('DB_USER', 'trader'),
    'password': os.environ.get('DB_PASSWORD', ''),
}