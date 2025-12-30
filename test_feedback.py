"""피드백 시스템 테스트 스크립트"""
import sys
import os

# UTF-8 인코딩 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("피드백 시스템 테스트")
print("=" * 60)

# 1. 암호화 파일 확인
print("\n[1/4] 암호화 파일 확인...")
if os.path.exists('feedback_config_encrypted.json'):
    print("[OK] feedback_config_encrypted.json 파일 존재")
else:
    print("[ERROR] feedback_config_encrypted.json 파일 없음")
    sys.exit(1)

# 2. 복호화 테스트
print("\n[2/4] 복호화 테스트...")
try:
    from core.crypto_manager import CryptoManager
    config = CryptoManager.load_and_decrypt('feedback_config_encrypted.json')
    print(f"[OK] 복호화 성공")
    print(f"   Bot Token: {config['bot_token'][:20]}...")
    print(f"   Channel ID: {config['channel_id']}")
except Exception as e:
    print(f"[ERROR] 복호화 실패: {e}")
    sys.exit(1)

# 3. Slack API 연결 테스트
print("\n[3/4] Slack API 연결 테스트...")
try:
    import requests
    
    url = "https://slack.com/api/auth.test"
    headers = {
        'Authorization': f'Bearer {config["bot_token"]}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, headers=headers, timeout=10)
    result = response.json()
    
    if result.get('ok'):
        print("[OK] Slack 연결 성공")
        print(f"   Bot 이름: {result.get('user', 'Unknown')}")
        print(f"   팀: {result.get('team', 'Unknown')}")
    else:
        print(f"[ERROR] Slack 연결 실패: {result.get('error', 'Unknown error')}")
        sys.exit(1)
except Exception as e:
    print(f"[ERROR] Slack 연결 오류: {e}")
    sys.exit(1)

# 4. 테스트 메시지 전송
print("\n[4/4] 테스트 메시지 전송...")
send_test = input("테스트 메시지를 Slack으로 전송하시겠습니까? (y/n): ")

if send_test.lower() == 'y':
    try:
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            'Authorization': f'Bearer {config["bot_token"]}',
            'Content-Type': 'application/json'
        }
        
        message = {
            'channel': config['channel_id'],
            'text': '🧪 GetBuild 피드백 시스템 테스트',
            'attachments': [
                {
                    'color': '#36a64f',
                    'fields': [
                        {'title': '상태', 'value': '정상 작동', 'short': True},
                        {'title': '테스트 시간', 'value': '지금', 'short': True},
                    ],
                    'footer': 'GetBuild 피드백 시스템'
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=message, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            print("[OK] 테스트 메시지 전송 성공!")
            print(f"   Slack 채널에서 메시지를 확인하세요.")
        else:
            print(f"[ERROR] 메시지 전송 실패: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"[ERROR] 메시지 전송 오류: {e}")
else:
    print("[SKIP] 테스트 메시지 전송 건너뜀")

print("\n" + "=" * 60)
print("[OK] 모든 테스트 완료!")
print("=" * 60)
print("\n앱에서 '버그 및 피드백' 메뉴를 사용할 수 있습니다.")

