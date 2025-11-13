"""슬랙 메시지 전송 모듈

필요한 Slack Bot 권한:
- chat:write - 메시지 전송
- channels:history - 공개 채널 메시지 읽기
- channels:read - 공개 채널 정보 읽기
- groups:history - 비공개 채널 메시지 읽기 (비공개 채널 사용 시)
- groups:read - 비공개 채널 정보 읽기 (비공개 채널 사용 시)
- im:history - DM 메시지 읽기 (DM 사용 시)
"""
import os
import json
import requests
from typing import Optional, Tuple
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


# Slack OAuth 토큰 설정 (환경 변수에서 가져오기)
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
CHANNEL_ID = "CXXXXXXXX"  # 메시지를 보낼 채널 ID


def send_slack_message(message: str) -> bool:
    """
    Slack OAuth 토큰을 이용한 메시지 전송 (기존 방식)
    
    Args:
        message: 전송할 메시지
    
    Returns:
        전송 성공 여부
    """
    client = WebClient(token=SLACK_TOKEN)
    
    try:
        response = client.chat_postMessage(
            channel=CHANNEL_ID,
            text=message
        )
        print(f"Message sent successfully: {response['ts']}")
        return True
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")
        return False


def send_slack_webhook(webhook_url: str, message: str, 
                      title: Optional[str] = None,
                      color: Optional[str] = None) -> bool:
    """
    Slack Incoming Webhook을 이용한 메시지 전송 (한글 지원)
    
    Args:
        webhook_url: Slack Incoming Webhook URL
        message: 전송할 메시지 (한글 가능)
        title: 메시지 제목 (선택사항)
        color: 메시지 색상 (good, warning, danger 또는 HEX 색상)
    
    Returns:
        전송 성공 여부
    """
    if not webhook_url or not message:
        print("Webhook URL 또는 메시지가 없습니다.")
        return False
    
    try:
        # 메시지 페이로드 구성
        payload = {}
        
        if title:
            # 제목이 있으면 attachment 형식 사용
            attachment = {
                "fallback": message,
                "text": message,
                "title": title,
            }
            
            if color:
                attachment["color"] = color
            
            payload["attachments"] = [attachment]
        else:
            # 제목이 없으면 단순 텍스트 메시지
            payload["text"] = message
        
        # UTF-8 인코딩으로 JSON 전송 (한글 지원)
        response = requests.post(
            webhook_url,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json; charset=utf-8'},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"슬랙 메시지 전송 성공: {message[:50]}...")
            return True
        else:
            print(f"슬랙 메시지 전송 실패 (상태코드: {response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        print(f"슬랙 메시지 전송 오류: {e}")
        return False


def check_bot_permissions(bot_token: str) -> bool:
    """
    Bot Token의 권한을 확인하고 출력
    
    Args:
        bot_token: Slack Bot Token
    
    Returns:
        권한 확인 성공 여부
    """
    try:
        client = WebClient(token=bot_token)
        response = client.auth_test()
        
        if response['ok']:
            print(f"[Slack] ✅ Bot 인증 성공")
            print(f"[Slack]    - Bot 이름: {response.get('user', 'unknown')}")
            print(f"[Slack]    - Workspace: {response.get('team', 'unknown')}")
            return True
        else:
            print(f"[Slack] ❌ Bot 인증 실패")
            return False
            
    except SlackApiError as e:
        print(f"[Slack] ❌ Bot Token 오류: {e.response.get('error')}")
        print(f"[Slack] Bot Token이 유효한지 확인하세요.")
        return False


def find_thread_by_keyword(bot_token: str, channel_id: str, keyword: str, 
                           days_back: int = 30, fuzzy_match: bool = True, 
                           limit: int = 200) -> Optional[str]:
    """
    특정 채널에서 키워드가 포함된 최근 스레드 찾기
    
    Args:
        bot_token: Slack Bot Token (OAuth Token)
        channel_id: 검색할 채널 ID (C로 시작: 채널, G로 시작: 그룹, D로 시작: DM)
        keyword: 검색할 키워드 (예: "251110 빌드 세팅 스레드")
        days_back: 검색할 기간 (일) - 기본 30일
        fuzzy_match: True면 키워드의 각 단어를 개별적으로도 검색
        limit: 가져올 최대 메시지 수 (기본 200개)
    
    Returns:
        찾은 스레드의 timestamp (thread_ts), 없으면 None
    """
    try:
        client = WebClient(token=bot_token)
        
        # Bot Token 유효성 확인
        print(f"[Slack] Bot 인증 확인 중...")
        auth_response = client.auth_test()
        if auth_response['ok']:
            bot_name = auth_response.get('user', 'unknown')
            print(f"[Slack] ✅ Bot 인증 성공: @{bot_name}")
        
        # 채널 ID 유형 확인
        if channel_id.startswith('D'):
            print(f"[Slack] ⚠️ DM 채널 감지 (ID: {channel_id})")
            print(f"[Slack] 💡 DM은 스레드 검색이 제한적입니다. 일반 채널 사용을 권장합니다.")
            # DM도 conversations.history로 시도
        elif channel_id.startswith('C'):
            print(f"[Slack] 공개 채널에서 검색 중... (ID: {channel_id})")
        elif channel_id.startswith('G'):
            print(f"[Slack] 비공개 채널에서 검색 중... (ID: {channel_id})")
        else:
            print(f"[Slack] ⚠️ 알 수 없는 채널 ID 형식: {channel_id}")
            print(f"[Slack] 올바른 형식: C로 시작(공개), G로 시작(비공개), D로 시작(DM)")
        
        # 먼저 채널 정보를 가져와서 봇이 채널에 접근 가능한지 확인
        try:
            channel_info = client.conversations_info(channel=channel_id)
            if channel_info['ok']:
                is_member = channel_info['channel'].get('is_member', False)
                channel_name = channel_info['channel'].get('name', 'unknown')
                
                if not is_member:
                    print(f"[Slack] ⚠️ 경고: 봇이 #{channel_name} 채널에 추가되지 않았습니다.")
                    print(f"[Slack] 💡 '/invite @봇이름' 명령으로 봇을 채널에 초대하세요.")
                else:
                    print(f"[Slack] ✅ 채널 접근 확인: #{channel_name}")
        except SlackApiError as info_error:
            # conversations_info 실패 시 계속 진행 (일부 채널 타입에서는 지원 안 됨)
            error_msg = info_error.response.get('error')
            print(f"[Slack] 채널 정보 조회 실패 (계속 진행): {error_msg}")
            if error_msg == 'missing_scope':
                print(f"[Slack] 💡 권한 부족이지만 메시지 검색은 시도합니다.")
                print(f"[Slack]    Bot Token에 'channels:read' 권한을 추가하면 더 나은 검증이 가능합니다.")
        
        # 검색 기간 설정 (Unix timestamp)
        oldest = (datetime.now() - timedelta(days=days_back)).timestamp()
        oldest_date = datetime.fromtimestamp(oldest).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"[Slack] 검색 기간: {oldest_date} 이후 (최근 {days_back}일)")
        
        # 채널 히스토리 가져오기
        print(f"[Slack] 최대 {limit}개의 메시지를 검색합니다...")
        response = client.conversations_history(
            channel=channel_id,
            oldest=str(oldest),
            limit=limit  # 설정된 개수만큼 메시지 검색
        )
        
        if response['ok']:
            messages = response['messages']
            print(f"[Slack] {len(messages)}개의 메시지 검색됨")
            
            # Slack API는 최신 메시지부터 반환하지만, 명시적으로 정렬
            # 최신 메시지가 먼저 오도록 timestamp 기준 내림차순 정렬
            messages = sorted(messages, key=lambda m: float(m.get('ts', 0)), reverse=True)
            
            # 디버깅: 처음 5개 메시지 내용과 시간 출력
            print(f"[Slack] 🔍 디버깅: 최신 메시지 미리보기 (최대 5개, 최신순)")
            for idx, msg in enumerate(messages[:5]):
                text = msg.get('text', '')
                ts = msg.get('ts', '0')
                
                # timestamp를 datetime으로 변환
                try:
                    msg_time = datetime.fromtimestamp(float(ts))
                    time_str = msg_time.strftime('%Y-%m-%d %H:%M:%S')
                    time_ago = datetime.now() - msg_time
                    
                    if time_ago.days > 0:
                        time_ago_str = f"{time_ago.days}일 전"
                    elif time_ago.seconds >= 3600:
                        time_ago_str = f"{time_ago.seconds // 3600}시간 전"
                    else:
                        time_ago_str = f"{time_ago.seconds // 60}분 전"
                except:
                    time_str = "시간 불명"
                    time_ago_str = "?"
                
                preview = text[:60] if text else '(빈 메시지)'
                print(f"[Slack]    메시지 {idx+1} [{time_ago_str}]: {preview}")
                print(f"[Slack]             시간: {time_str}")
            
            # 키워드가 포함된 메시지 찾기 (최신순)
            keyword_lower = keyword.lower()
            
            # fuzzy_match를 위한 키워드 분리
            keyword_parts = keyword_lower.split() if fuzzy_match else [keyword_lower]
            
            print(f"[Slack] 검색 모드: {'퍼지 매칭' if fuzzy_match else '정확 매칭'}")
            if fuzzy_match and len(keyword_parts) > 1:
                print(f"[Slack] 검색 키워드 분리: {keyword_parts}")
            
            for idx, message in enumerate(messages):
                # 다양한 필드에서 검색
                text = message.get('text', '')
                
                # attachments, blocks 등 다른 필드도 확인
                attachments = message.get('attachments', [])
                blocks = message.get('blocks', [])
                
                # 검색 대상 텍스트 수집
                search_texts = [text]
                
                # attachments에서 텍스트 추출
                for att in attachments:
                    if 'text' in att:
                        search_texts.append(att['text'])
                    if 'pretext' in att:
                        search_texts.append(att['pretext'])
                    if 'title' in att:
                        search_texts.append(att['title'])
                
                # blocks에서 텍스트 추출
                for block in blocks:
                    if block.get('type') == 'section' and 'text' in block:
                        block_text = block['text'].get('text', '')
                        search_texts.append(block_text)
                
                # 모든 텍스트에서 키워드 검색
                all_text = ' '.join(search_texts).lower()
                
                # 정확 매칭 시도
                if keyword_lower in all_text:
                    thread_ts = message.get('ts')
                    matched_text = text if text else search_texts[1] if len(search_texts) > 1 else '(내용 없음)'
                    print(f"[Slack] ✅ 스레드 발견 (정확 매칭, 메시지 #{idx+1})")
                    print(f"[Slack]    내용: '{matched_text[:60]}...'")
                    print(f"[Slack]    thread_ts: {thread_ts}")
                    return thread_ts
                
                # fuzzy_match가 켜져 있으면 부분 매칭 시도
                if fuzzy_match and len(keyword_parts) > 1:
                    matched_parts = sum(1 for part in keyword_parts if part in all_text)
                    match_ratio = matched_parts / len(keyword_parts)
                    
                    # 키워드의 70% 이상이 매칭되면 선택
                    if match_ratio >= 0.7:
                        thread_ts = message.get('ts')
                        matched_text = text if text else search_texts[1] if len(search_texts) > 1 else '(내용 없음)'
                        print(f"[Slack] ✅ 스레드 발견 (퍼지 매칭 {match_ratio*100:.0f}%, 메시지 #{idx+1})")
                        print(f"[Slack]    내용: '{matched_text[:60]}...'")
                        print(f"[Slack]    thread_ts: {thread_ts}")
                        return thread_ts
            
            print(f"[Slack] ⚠️ 키워드 '{keyword}'가 포함된 스레드를 찾을 수 없습니다.")
            print(f"[Slack] 💡 팁:")
            print(f"  - 키워드가 정확한지 확인하세요. (입력된 키워드: '{keyword}')")
            print(f"  - 최근 {days_back}일 내의 메시지만 검색됩니다.")
            print(f"  - 대소문자는 구분하지 않습니다.")
            print(f"  - 위 미리보기에서 키워드가 포함된 메시지가 있는지 확인하세요.")
            print(f"  - 키워드를 더 짧게 입력하거나 핵심 단어만 사용해보세요.")
            return None
        else:
            print(f"[Slack] conversations.history 오류: {response.get('error')}")
            return None
            
    except SlackApiError as e:
        error_type = e.response.get('error', 'unknown')
        
        if error_type == 'missing_scope':
            # 필요한 권한이 없는 경우
            needed_scopes = e.response.get('needed', 'channels:history')
            print(f"[Slack] ❌ 권한 오류: Bot Token에 필요한 권한이 없습니다.")
            print(f"[Slack] 필요한 권한: {needed_scopes}")
            print(f"[Slack] 해결 방법:")
            print(f"  1. https://api.slack.com/apps 접속")
            print(f"  2. 해당 앱 선택 → 'OAuth & Permissions' 메뉴")
            print(f"  3. 'Scopes' 섹션에서 다음 권한 추가:")
            
            # 채널 타입에 따라 필요한 권한 안내
            if channel_id.startswith('D'):
                print(f"     - im:history (DM 읽기)")
            elif channel_id.startswith('G'):
                print(f"     - groups:history (비공개 채널 읽기)")
            else:
                print(f"     - channels:history (공개 채널 읽기)")
            
            print(f"  4. 'Reinstall to Workspace' 클릭")
            print(f"  5. 새로운 Bot Token 복사하여 다시 설정")
        elif error_type == 'channel_not_found':
            print(f"[Slack] ❌ 채널 오류: 채널 ID '{channel_id}'를 찾을 수 없습니다.")
            print(f"[Slack] ")
            print(f"[Slack] 🔍 가장 흔한 원인:")
            print(f"  ⚠️  봇이 채널에 추가되지 않았습니다!")
            print(f"")
            print(f"[Slack] ✅ 해결 방법 (순서대로 시도):")
            print(f"")
            print(f"  1️⃣  먼저 봇을 채널에 초대하세요:")
            print(f"     - Slack 채널로 이동")
            print(f"     - 채널 메시지 입력창에 '/invite @봇이름' 입력")
            print(f"     - 예: /invite @QuickBuild")
            print(f"     - 봇이 추가되면 '○○○님이 #채널에 추가되었습니다' 메시지 확인")
            print(f"")
            print(f"  2️⃣  채널 ID가 정확한지 확인:")
            print(f"     - 채널 클릭 → 오른쪽 상단 ⋮ → '채널 세부정보 보기'")
            print(f"     - 하단에서 '채널 ID' 복사")
            print(f"     - 공개 채널: C로 시작 (예: C0123456789)")
            print(f"     - 비공개 채널: G로 시작 (예: G0123456789)")
            print(f"")
            print(f"  3️⃣  Bot Token 권한 확인:")
            print(f"     - https://api.slack.com/apps 접속")
            print(f"     - 앱 선택 → 'OAuth & Permissions'")
            print(f"     - 'Scopes'에서 다음 권한이 있는지 확인:")
            if channel_id.startswith('G'):
                print(f"       ✓ groups:history")
                print(f"       ✓ groups:read")
            else:
                print(f"       ✓ channels:history")
                print(f"       ✓ channels:read")
            print(f"     - 권한이 없다면 추가 후 'Reinstall to Workspace'")
        elif error_type == 'not_in_channel':
            print(f"[Slack] ❌ 채널 접근 오류: 봇이 채널에 추가되지 않았습니다.")
            print(f"[Slack] ")
            print(f"[Slack] ✅ 해결 방법:")
            print(f"  - Slack 채널로 이동")
            print(f"  - 채널 메시지 입력창에 '/invite @봇이름' 입력")
            print(f"  - 예: /invite @QuickBuild")
        else:
            print(f"[Slack] ❌ 스레드 검색 오류: {error_type}")
            if 'error' in e.response:
                print(f"[Slack] 상세 정보: {e.response}")
        
        return None
    except Exception as e:
        print(f"[Slack] ❌ 스레드 검색 예외: {e}")
        return None


def send_thread_reply(bot_token: str, channel_id: str, thread_ts: str, 
                     message: str, title: Optional[str] = None) -> bool:
    """
    특정 스레드에 댓글로 메시지 전송
    
    Args:
        bot_token: Slack Bot Token (OAuth Token)
        channel_id: 채널 ID
        thread_ts: 스레드 timestamp
        message: 전송할 메시지
        title: 메시지 제목 (선택사항)
    
    Returns:
        전송 성공 여부
    """
    try:
        client = WebClient(token=bot_token)
        
        # 메시지 구성
        full_message = message
        if title:
            full_message = f"*{title}*\n{message}"
        
        response = client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=full_message
        )
        
        if response['ok']:
            print(f"[Slack] ✅ 스레드 댓글 전송 성공: {response['ts']}")
            return True
        else:
            print(f"[Slack] ❌ 스레드 댓글 전송 실패: {response.get('error')}")
            return False
            
    except SlackApiError as e:
        error_type = e.response.get('error', 'unknown')
        
        if error_type == 'missing_scope':
            # 필요한 권한이 없는 경우
            needed_scopes = e.response.get('needed', 'chat:write')
            print(f"[Slack] ❌ 권한 오류: Bot Token에 메시지 전송 권한이 없습니다.")
            print(f"[Slack] 필요한 권한: {needed_scopes}")
            print(f"[Slack] 해결 방법:")
            print(f"  1. https://api.slack.com/apps 접속")
            print(f"  2. 해당 앱 선택 → 'OAuth & Permissions' 메뉴")
            print(f"  3. 'Scopes' 섹션에서 다음 권한 추가:")
            print(f"     - chat:write (메시지 전송)")
            print(f"  4. 'Reinstall to Workspace' 클릭")
            print(f"  5. 새로운 Bot Token 복사하여 다시 설정")
        elif error_type == 'channel_not_found':
            print(f"[Slack] ❌ 채널 오류: 채널 ID '{channel_id}'를 찾을 수 없습니다.")
        elif error_type == 'not_in_channel':
            print(f"[Slack] ❌ 채널 접근 오류: 봇이 채널에 추가되지 않았습니다.")
            print(f"[Slack] 해결 방법: 채널에서 '/invite @앱이름' 명령 실행")
        elif error_type == 'thread_not_found':
            print(f"[Slack] ❌ 스레드 오류: 스레드를 찾을 수 없습니다. (ts: {thread_ts})")
        elif error_type == 'invalid_auth':
            print(f"[Slack] ❌ 인증 오류: Bot Token이 유효하지 않습니다.")
            print(f"[Slack] 해결 방법: Bot Token을 다시 확인하세요. (xoxb-로 시작)")
        else:
            print(f"[Slack] ❌ 스레드 댓글 전송 오류: {error_type}")
            if 'error' in e.response:
                print(f"[Slack] 상세 정보: {e.response}")
        
        return False
    except Exception as e:
        print(f"[Slack] ❌ 스레드 댓글 전송 예외: {e}")
        return False


def send_schedule_notification(webhook_url: str, schedule_name: str, 
                               status: str, details: Optional[str] = None,
                               notification_type: str = 'standalone',
                               bot_token: Optional[str] = None,
                               channel_id: Optional[str] = None,
                               thread_keyword: Optional[str] = None) -> bool:
    """
    스케줄 실행 알림 전송 (단독 알림 또는 스레드 댓글)
    
    Args:
        webhook_url: Slack Webhook URL (단독 알림용)
        schedule_name: 스케줄 이름
        status: 상태 (시작, 완료, 실패)
        details: 추가 상세 정보
        notification_type: 알림 타입 ('standalone' 또는 'thread')
        bot_token: Slack Bot Token (스레드 댓글용)
        channel_id: 채널 ID (스레드 댓글용)
        thread_keyword: 스레드 검색 키워드 (스레드 댓글용)
    
    Returns:
        전송 성공 여부
    """
    # 상태에 따른 색상 설정
    color_map = {
        '시작': '#2196F3',  # 파란색
        '완료': 'good',      # 녹색
        '성공': 'good',
        '실패': 'danger',    # 빨간색
        '오류': 'danger',
        '경고': 'warning'    # 노란색
    }
    
    color = color_map.get(status, '#808080')  # 기본: 회색
    
    # 메시지 구성
    title = f"🔔 스케줄 알림: {schedule_name}"
    message = f"상태: {status}"
    
    if details:
        message += f"\n{details}"
    
    # 알림 타입에 따라 전송 방식 선택
    if notification_type == 'thread' and bot_token and channel_id and thread_keyword:
        # 스레드 댓글 알림
        print(f"[Slack] 스레드 댓글 알림 시도: 키워드='{thread_keyword}'")
        
        # 1. 스레드 찾기
        thread_ts = find_thread_by_keyword(bot_token, channel_id, thread_keyword)
        
        if thread_ts:
            # 2. 스레드에 댓글 달기
            return send_thread_reply(bot_token, channel_id, thread_ts, message, title)
        else:
            # 스레드를 찾지 못한 경우 단독 알림으로 폴백
            print(f"[Slack] 스레드를 찾지 못해 단독 알림으로 전송합니다.")
            return send_slack_webhook(webhook_url, message, title=title, color=color)
    else:
        # 단독 알림 (기본)
        return send_slack_webhook(webhook_url, message, title=title, color=color)


if __name__ == "__main__":
    # 테스트 코드
    test_message = "안녕하세요! 슬랙 채널에 메시지를 보냅니다. 🚀"
    
    # OAuth 토큰 방식 테스트
    if SLACK_TOKEN:
        print("OAuth 토큰 방식 테스트:")
        send_slack_message(test_message)
    
    # Webhook 방식 테스트 (hook.json에서 로드)
    if os.path.exists('hook.json'):
        try:
            with open('hook.json', 'r', encoding='utf-8') as f:
                hooks = json.load(f)
            
            if hooks and len(hooks) > 0:
                test_webhook = hooks[0].get('url', '')
                if test_webhook and test_webhook.startswith('https://'):
                    print("\nWebhook 방식 테스트:")
                    send_slack_webhook(test_webhook, test_message, title="테스트 알림", color="good")
                    
                    print("\n스케줄 알림 테스트:")
                    send_schedule_notification(
                        test_webhook, 
                        "테스트 스케줄", 
                        "완료",
                        "빌드 복사가 성공적으로 완료되었습니다."
                    )
        except Exception as e:
            print(f"hook.json 로드 오류: {e}")
