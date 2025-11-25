import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """환경 변수 설정 클래스"""
    
    # 실전투자 계좌 설정
    REAL_APPKEY = os.getenv('REAL_APPKEY')
    REAL_APPSECRET = os.getenv('REAL_APPSECRET')
    REAL_ACCOUNT_NO = os.getenv('REAL_ACCOUNT_NO')
    
    # 모의투자 계좌 설정
    DEMO_APPKEY = os.getenv('DEMO_APPKEY')
    DEMO_APPSECRET = os.getenv('DEMO_APPSECRET')
    DEMO_ACCOUNT_NO = os.getenv('DEMO_ACCOUNT_NO')
    
    @classmethod
    def validate_config(cls):
        """설정 값 검증"""
        required_vars = [
            'REAL_APPKEY', 'REAL_APPSECRET', 'REAL_ACCOUNT_NO',
            'DEMO_APPKEY', 'DEMO_APPSECRET', 'DEMO_ACCOUNT_NO'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"다음 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        
        return True
    
    @classmethod
    def get_account_info(cls, mode='demo'):
        """계좌 정보 반환"""
        cls.validate_config()
        
        if mode == 'real':
            return {
                'appkey': cls.REAL_APPKEY,
                'appsecret': cls.REAL_APPSECRET,
                'account': cls.REAL_ACCOUNT_NO
            }
        else:
            return {
                'appkey': cls.DEMO_APPKEY,
                'appsecret': cls.DEMO_APPSECRET,
                'account': cls.DEMO_ACCOUNT_NO
            }