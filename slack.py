import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Slack OAuth 토큰 설정 (환경 변수에서 가져오기)
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
CHANNEL_ID = "CXXXXXXXX"  # 메시지를 보낼 채널 ID

def send_slack_message(message):
    client = WebClient(token=SLACK_TOKEN)
    
    try:
        response = client.chat_postMessage(
            channel=CHANNEL_ID,
            text=message
        )
        print(f"Message sent successfully: {response['ts']}")
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

if __name__ == "__main__":
    message = "안녕하세요! 슬랙 채널에 메시지를 보냅니다. 🚀"
    send_slack_message(message)
