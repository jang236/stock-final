#!/bin/bash
echo "🚀 Replit 환경 설정 및 서버 시작"

# pip 업그레이드 (Nix Python 사용)
pip install --upgrade pip

# 의존성 설치 (Nix Python 사용)
echo "📦 의존성 설치 중..."
pip install -r requirements.txt

echo "✅ 환경 설정 완료!"
