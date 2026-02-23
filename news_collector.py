"""
네이버 뉴스 수집 시스템 (함수 버전)
"""
import requests
import os
from urllib.parse import quote
from datetime import datetime, timedelta, timezone
import json
import re

# KST 타임존 설정
KST = timezone(timedelta(hours=9))

# 네이버 API 키
NAVER_CLIENT_ID = 'EU6h_rE1b4pu48Bsrfdk'
NAVER_CLIENT_SECRET = 'nz0wgmUPUK'

def clean_html_tags(text):
    """HTML 태그 제거"""
    if not text:
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def collect_company_news(company_name):
    """기업명으로 뉴스 수집 (메인 함수)"""
    try:
        print(f"📰 '{company_name}' 뉴스 수집 시작...")
        
        # 최신순 뉴스 수집
        encoded_query = quote(company_name)
        url = f"https://openapi.naver.com/v1/search/news.json?query={encoded_query}&display=50&start=1&sort=date"
        
        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            items = response.json().get('items', [])
            
            # 뉴스 정제
            cleaned_news = []
            for item in items:
                cleaned_item = {
                    'title': clean_html_tags(item.get('title', '')),
                    'description': clean_html_tags(item.get('description', '')),
                    'link': item.get('link', ''),
                    'pubDate': item.get('pubDate', ''),
                    'collection_time': datetime.now(KST).isoformat()
                }
                cleaned_news.append(cleaned_item)
            
            return {
                "status": "success",
                "company_name": company_name,
                "news_count": len(cleaned_news),
                "news_data": cleaned_news,
                "collection_time": datetime.now(KST).isoformat()
            }
        else:
            return {
                "status": "error",
                "error": f"API 호출 실패: {response.status_code}",
                "company_name": company_name
            }
            
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "company_name": company_name
        }
