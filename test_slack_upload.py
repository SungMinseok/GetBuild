"""Slack 파일 업로드 테스트"""
import requests
import io
from PIL import Image

# 설정
bot_token = "xoxb-YOUR-BOT-TOKEN-HERE"  # 실제 토큰으로 교체하세요
channel_id = "C09RYABRECB"

print("=" * 60)
print("Slack 파일 업로드 테스트")
print("=" * 60)

# 1. Bot 정보 확인
print("\n[1] Bot 정보 확인...")
url = "https://slack.com/api/auth.test"
headers = {'Authorization': f'Bearer {bot_token}'}
response = requests.post(url, headers=headers)
result = response.json()

if result.get('ok'):
    print(f"   Bot 이름: {result.get('user')}")
    print(f"   팀: {result.get('team')}")
    print(f"   User ID: {result.get('user_id')}")
else:
    print(f"   오류: {result.get('error')}")
    exit(1)

# 2. 권한 확인
print("\n[2] Bot 권한 확인...")
# 참고: auth.test는 권한 목록을 반환하지 않음
# 실제 업로드를 시도해서 권한 확인

# 3. 테스트 이미지 생성
print("\n[3] 테스트 이미지 생성...")
img = Image.new('RGB', (300, 200), color='red')

# 텍스트 추가
from PIL import ImageDraw, ImageFont
draw = ImageDraw.Draw(img)
draw.text((50, 80), "Test Screenshot", fill='white')

# PNG로 변환
byte_array = io.BytesIO()
img.save(byte_array, 'PNG')
byte_array.seek(0)

print(f"   이미지 크기: {len(byte_array.getvalue())} bytes")

# 4. 파일 업로드 테스트
print("\n[4] 파일 업로드 테스트...")
url = "https://slack.com/api/files.upload"

files = {
    'file': ('test_screenshot.png', byte_array, 'image/png')
}

data = {
    'channels': channel_id,
    'title': '테스트 스크린샷',
    'initial_comment': '📸 이것은 테스트 이미지입니다',
}

headers = {
    'Authorization': f'Bearer {bot_token}'
}

response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
result = response.json()

print(f"\n[응답]")
print(f"   성공: {result.get('ok')}")

if result.get('ok'):
    print(f"   파일 ID: {result.get('file', {}).get('id')}")
    print(f"   파일 이름: {result.get('file', {}).get('name')}")
    print(f"   파일 URL: {result.get('file', {}).get('permalink')}")
    print("\n✅ 파일 업로드 성공!")
    print("   Slack 채널을 확인하세요.")
else:
    error = result.get('error')
    print(f"   오류: {error}")
    
    if error == 'missing_scope':
        print("\n[X] 권한 오류!")
        print("   files:write 권한이 필요합니다.")
        print("\n해결 방법:")
        print("   1. https://api.slack.com/apps 접속")
        print("   2. 앱 선택")
        print("   3. OAuth & Permissions 메뉴")
        print("   4. Bot Token Scopes에 'files:write' 추가")
        print("   5. 'Reinstall to Workspace' 클릭")
    elif error == 'not_in_channel':
        print("\n[X] 채널 오류!")
        print("   Bot이 채널에 추가되지 않았습니다.")
        print("\n해결 방법:")
        print("   1. Slack 채널 열기")
        print("   2. /invite @봇이름 입력")
    else:
        print("\n[X] 알 수 없는 오류: {0}".format(error))

print("\n" + "=" * 60)

