"""환경 변수 및 피드백 시스템 테스트"""
import os
import sys

print("=" * 60)
print("환경 변수 및 피드백 시스템 테스트")
print("=" * 60)

# 1. 환경 변수 확인
print("\n[1] 환경 변수 확인")
bot_token = os.environ.get('DEFAULT_SLACK_BOT_TOKEN')
channel_id = os.environ.get('DEFAULT_SLACK_CHANNEL_ID')

print(f"   DEFAULT_SLACK_BOT_TOKEN: {bot_token[:20] + '...' if bot_token else 'NOT SET'}")
print(f"   DEFAULT_SLACK_CHANNEL_ID: {channel_id if channel_id else 'NOT SET'}")

if not bot_token or not channel_id:
    print("\n[!] 환경 변수가 설정되지 않았습니다!")
    print("\nPowerShell에서 다음 명령 실행:")
    print('.\setup_env.ps1')
    print('\n또는 관리자에게 토큰 정보를 받아서 수동 설정하세요.')
    sys.exit(1)

# 2. feedback_dialog_slack 모듈 테스트
print("\n[2] feedback_dialog_slack 모듈 로드 테스트")
try:
    from ui.feedback_dialog_slack import SlackFeedbackThread
    print("   모듈 로드 성공!")
except Exception as e:
    print(f"   모듈 로드 실패: {e}")
    sys.exit(1)

# 3. 설정 로드 테스트
print("\n[3] 설정 로드 테스트")
try:
    # 임시 스레드 생성하여 설정 로드 테스트
    thread = SlackFeedbackThread('버그', '테스터', '테스트', '테스트 내용', '1.0.0')
    config = thread.load_encrypted_config()
    
    print(f"   Bot Token: {config['bot_token'][:20] + '...'}")
    print(f"   Channel ID: {config['channel_id']}")
    
    if config['bot_token'] == 'xoxb-YOUR-BOT-TOKEN-HERE':
        print("\n[!] 경고: 플레이스홀더 토큰이 사용되고 있습니다!")
        print("   환경 변수가 제대로 설정되지 않았을 수 있습니다.")
    else:
        print("\n   설정 로드 성공!")
        
except Exception as e:
    print(f"   설정 로드 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. Slack API 연결 테스트
print("\n[4] Slack API 연결 테스트")
try:
    import requests
    
    url = "https://slack.com/api/auth.test"
    headers = {'Authorization': f'Bearer {config["bot_token"]}'}
    response = requests.post(url, headers=headers, timeout=10)
    result = response.json()
    
    if result.get('ok'):
        print(f"   연결 성공!")
        print(f"   Bot 이름: {result.get('user')}")
        print(f"   팀: {result.get('team')}")
    else:
        print(f"   연결 실패: {result.get('error')}")
        if result.get('error') == 'invalid_auth':
            print("\n[!] invalid_auth 오류:")
            print("   - Bot Token이 잘못되었거나")
            print("   - Token이 만료되었거나")
            print("   - 환경 변수가 잘못 설정되었습니다")
        sys.exit(1)
        
except Exception as e:
    print(f"   API 테스트 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("모든 테스트 통과! 피드백 시스템이 정상 작동합니다.")
print("=" * 60)
print("\n이제 앱을 실행하고 피드백을 제출할 수 있습니다:")
print("  python index.py")

