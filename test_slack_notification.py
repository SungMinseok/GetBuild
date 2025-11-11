"""슬랙 알림 테스트 스크립트"""
import json
import os
from slack import send_slack_webhook, send_schedule_notification

def test_slack_notifications():
    """슬랙 알림 기능 테스트"""
    
    print("=" * 60)
    print("슬랙 알림 테스트 시작")
    print("=" * 60)
    
    # hook.json 파일 확인
    hook_file = 'hook.json'
    if not os.path.exists(hook_file):
        print(f"\n❌ {hook_file} 파일이 없습니다.")
        print("hook.json 파일을 먼저 생성하고 실제 Webhook URL을 입력하세요.")
        return
    
    # hook.json 로드
    try:
        with open(hook_file, 'r', encoding='utf-8') as f:
            hooks = json.load(f)
    except Exception as e:
        print(f"❌ hook.json 로드 오류: {e}")
        return
    
    if not hooks or len(hooks) == 0:
        print("❌ hook.json에 Webhook URL이 없습니다.")
        return
    
    # 첫 번째 Webhook URL 사용
    test_webhook = hooks[0].get('url', '')
    webhook_name = hooks[0].get('name', 'Unknown')
    
    if not test_webhook or not test_webhook.startswith('https://hooks.slack.com'):
        print(f"❌ 유효하지 않은 Webhook URL: {test_webhook}")
        print("실제 Slack Incoming Webhook URL을 입력하세요.")
        return
    
    print(f"\n📢 테스트 채널: {webhook_name}")
    print(f"🔗 Webhook URL: {test_webhook[:50]}...")
    print("\n" + "=" * 60)
    
    # 테스트 1: 기본 메시지
    print("\n[테스트 1] 기본 메시지 전송")
    result1 = send_slack_webhook(
        webhook_url=test_webhook,
        message="안녕하세요! 슬랙 알림 테스트입니다. 🚀\n한글 메시지도 잘 전송됩니다."
    )
    print(f"결과: {'✅ 성공' if result1 else '❌ 실패'}")
    
    # 테스트 2: 제목과 색상이 있는 메시지
    print("\n[테스트 2] 제목과 색상이 있는 메시지")
    result2 = send_slack_webhook(
        webhook_url=test_webhook,
        message="이 메시지는 제목과 파란색 배경을 가지고 있습니다.",
        title="📋 테스트 알림",
        color="#2196F3"
    )
    print(f"결과: {'✅ 성공' if result2 else '❌ 실패'}")
    
    # 테스트 3: 스케줄 시작 알림
    print("\n[테스트 3] 스케줄 시작 알림")
    result3 = send_schedule_notification(
        webhook_url=test_webhook,
        schedule_name="game_SEL 빌드 복사",
        status="시작",
        details="옵션: 클라복사\n빌드: CompileBuild_DEV_game_SEL_271167_r306671"
    )
    print(f"결과: {'✅ 성공' if result3 else '❌ 실패'}")
    
    # 테스트 4: 스케줄 완료 알림
    print("\n[테스트 4] 스케줄 완료 알림")
    result4 = send_schedule_notification(
        webhook_url=test_webhook,
        schedule_name="game_SEL 빌드 복사",
        status="완료",
        details="빌드 복사가 성공적으로 완료되었습니다.\n소요 시간: 5분 32초"
    )
    print(f"결과: {'✅ 성공' if result4 else '❌ 실패'}")
    
    # 테스트 5: 스케줄 실패 알림
    print("\n[테스트 5] 스케줄 실패 알림")
    result5 = send_schedule_notification(
        webhook_url=test_webhook,
        schedule_name="game_dev 서버 패치",
        status="실패",
        details="FileNotFoundError: 빌드 파일을 찾을 수 없습니다."
    )
    print(f"결과: {'✅ 성공' if result5 else '❌ 실패'}")
    
    # 테스트 결과 요약
    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)
    
    success_count = sum([result1, result2, result3, result4, result5])
    print(f"\n총 5개 테스트 중 {success_count}개 성공")
    
    if success_count == 5:
        print("✅ 모든 테스트 통과!")
    else:
        print(f"⚠️  {5 - success_count}개 테스트 실패")


if __name__ == "__main__":
    test_slack_notifications()




