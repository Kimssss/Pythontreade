#!/usr/bin/env python3
"""
자동 패키지 설치 모듈
실행 시 필요한 패키지가 없으면 자동으로 설치
"""

import subprocess
import sys
import pkg_resources
from pathlib import Path

def install_package(package):
    """패키지 설치"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 설치 완료")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package} 설치 실패: {e}")
        return False

def check_and_install_requirements():
    """requirements.txt 기반 패키지 확인 및 설치"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt 파일이 없습니다.")
        return False
    
    # requirements.txt 읽기
    with open(requirements_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 패키지 목록 파싱
    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('-'):
            # >= 버전 표기 제거하여 패키지명만 추출
            package_name = line.split('>=')[0].split('==')[0].split('~=')[0]
            packages.append((package_name, line))
    
    print(f"📋 총 {len(packages)}개 패키지 확인 중...")
    
    # 설치된 패키지 확인
    installed_packages = {pkg.project_name.lower(): pkg.version for pkg in pkg_resources.working_set}
    
    missing_packages = []
    for package_name, requirement in packages:
        if package_name.lower() not in installed_packages:
            missing_packages.append(requirement)
        else:
            print(f"✅ {package_name} 이미 설치됨 (v{installed_packages[package_name.lower()]})")
    
    # 누락된 패키지 설치
    if missing_packages:
        print(f"\n🔧 {len(missing_packages)}개 누락된 패키지 설치 시작...")
        failed_packages = []
        
        for package in missing_packages:
            print(f"📦 {package} 설치 중...")
            if not install_package(package):
                failed_packages.append(package)
        
        if failed_packages:
            print(f"\n❌ 설치 실패한 패키지들:")
            for package in failed_packages:
                print(f"   - {package}")
            return False
        else:
            print(f"\n✅ 모든 패키지 설치 완료!")
    else:
        print("\n✅ 모든 필수 패키지가 이미 설치되어 있습니다.")
    
    return True

def check_package(package_name):
    """특정 패키지 설치 여부 확인"""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def auto_install_on_import(package_name, pip_name=None):
    """임포트 시 자동 설치 데코레이터"""
    if pip_name is None:
        pip_name = package_name
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_package(package_name):
                print(f"📦 {package_name} 패키지가 없습니다. 자동 설치 중...")
                if install_package(pip_name):
                    print(f"✅ {package_name} 설치 완료. 함수를 실행합니다.")
                else:
                    print(f"❌ {package_name} 설치 실패. 수동으로 설치해주세요.")
                    return None
            return func(*args, **kwargs)
        return wrapper
    return decorator

if __name__ == "__main__":
    print("🚀 AI 자동매매 시스템 - 자동 패키지 설치")
    print("=" * 50)
    
    success = check_and_install_requirements()
    
    if success:
        print("\n🎉 모든 의존성 설치가 완료되었습니다!")
        print("이제 메인 프로그램을 실행할 수 있습니다.")
    else:
        print("\n⚠️ 일부 패키지 설치에 실패했습니다.")
        print("수동으로 설치하거나 Python 환경을 확인해주세요.")
        sys.exit(1)