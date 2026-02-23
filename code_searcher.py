import os
import re
from pathlib import Path


def search_code_pattern():
    """
    Replit에서 time.sleep(random.uniform 패턴을 찾는 검색기
    """
    
    # 검색할 패턴들
    patterns = [
        r'time\.sleep\(random\.uniform',
        r'sleep\(random\.uniform',
        r'random\.uniform.*sleep',
        r'200.*휴식',
        r'200.*break',
        r'200.*rest',
        r'count.*%.*200',
        r'i.*%.*200',
        r'batch.*200'
    ]
    
    # 검색할 파일 확장자
    extensions = ['.py', '.ipynb', '.txt']
    
    results = {}
    
    print("🔍 코드 패턴 검색 시작...")
    print("=" * 50)
    
    # 현재 디렉토리부터 모든 파일 검색
    for root, dirs, files in os.walk('.'):
        # .git, __pycache__ 등 제외
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # 각 패턴 검색
                        for pattern in patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE)
                            
                            for match in matches:
                                if file_path not in results:
                                    results[file_path] = []
                                
                                # 매치된 라인 번호 찾기
                                line_num = content[:match.start()].count('\n') + 1
                                line_content = content.split('\n')[line_num-1].strip()
                                
                                results[file_path].append({
                                    'pattern': pattern,
                                    'line': line_num,
                                    'content': line_content,
                                    'match': match.group()
                                })
                
                except Exception as e:
                    continue
    
    # 결과 출력
    if results:
        print(f"✅ {len(results)}개 파일에서 패턴 발견!")
        print("=" * 50)
        
        for file_path, matches in results.items():
            print(f"\n📁 {file_path}")
            print("-" * 30)
            
            for match in matches:
                print(f"  📍 라인 {match['line']}: {match['content']}")
                print(f"     패턴: {match['pattern']}")
                print(f"     매치: {match['match']}")
                print()
    else:
        print("❌ 패턴을 찾을 수 없습니다.")
        print("\n💡 다른 검색 방법:")
        print("1. 파일명으로 검색:")
        search_by_filename()
        print("\n2. 키워드로 검색:")
        search_by_keywords()


def search_by_filename():
    """파일명으로 검색"""
    keywords = ['collector', 'batch', 'cf1001', 'naver', 'crawler', 'spider']
    
    print("📁 관련 파일명 검색:")
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                for keyword in keywords:
                    if keyword.lower() in file.lower():
                        print(f"   - {os.path.join(root, file)}")
                        break


def search_by_keywords():
    """키워드로 광범위 검색"""
    keywords = ['uniform', 'random', 'sleep', '200', '휴식', 'batch', 'collector']
    
    print("🔑 키워드 포함 파일:")
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        
                        found_keywords = [kw for kw in keywords if kw in content]
                        if len(found_keywords) >= 3:  # 3개 이상 키워드 포함
                            print(f"   - {file_path} ({', '.join(found_keywords)})")
                            
                except Exception:
                    continue


def show_file_content(file_path):
    """파일 내용 보기"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"\n📄 {file_path} 내용:")
            print("=" * 50)
            print(content)
    except Exception as e:
        print(f"❌ 파일 읽기 실패: {e}")


if __name__ == "__main__":
    print("🔍 네이버 cF1001 수집기 코드 검색")
    print("time.sleep(random.uniform 패턴 찾기")
    print("=" * 50)
    
    search_code_pattern()
    
    print("\n" + "=" * 50)
    print("💡 사용법:")
    print("1. 위 결과에서 파일을 찾았으면 내용 확인")
    print("2. Python 콘솔에서 show_file_content('파일경로') 실행")
    print("3. 또는 직접 파일 열어보기")
