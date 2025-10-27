"""기존 schedule.json을 새 포맷으로 마이그레이션"""
import json
import os
import uuid
from datetime import datetime
import shutil


def migrate_schedule_json(old_file='schedule.json', backup=True):
    """
    기존 schedule.json을 새 포맷으로 마이그레이션
    
    Args:
        old_file: 기존 schedule.json 파일 경로
        backup: 백업 생성 여부
    """
    if not os.path.exists(old_file):
        print(f"⚠️  {old_file} 파일이 없습니다.")
        return
    
    # 백업 생성
    if backup:
        backup_file = f"{old_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy(old_file, backup_file)
        print(f"✅ 백업 생성: {backup_file}")
    
    # 기존 파일 로드
    with open(old_file, 'r', encoding='utf-8') as f:
        old_schedules = json.load(f)
    
    # 새 포맷으로 변환
    new_schedules = []
    
    for old_schedule in old_schedules:
        # 기존 필드
        time = old_schedule.get('time', '')
        option = old_schedule.get('option', '')
        buildname = old_schedule.get('buildname', '')
        awsurl = old_schedule.get('awsurl', '')
        branch = old_schedule.get('branch', '')
        
        # 새 필드 추가
        new_schedule = {
            'id': old_schedule.get('id', str(uuid.uuid4())),
            'name': f"{option} - {time}",
            'time': time,
            'option': option,
            'buildname': buildname,
            'awsurl': awsurl,
            'branch': branch,
            'repeat_type': 'once',  # 기본값: 일회성
            'repeat_days': [],
            'enabled': True,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        new_schedules.append(new_schedule)
    
    # 새 파일 저장
    with open(old_file, 'w', encoding='utf-8') as f:
        json.dump(new_schedules, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 마이그레이션 완료: {len(new_schedules)}개 스케줄")
    print(f"   파일: {old_file}")


def create_sample_schedule():
    """샘플 스케줄 생성"""
    sample_schedules = [
        {
            'id': str(uuid.uuid4()),
            'name': '매일 아침 빌드 테스트',
            'time': '08:00',
            'option': '테스트(로그)',
            'buildname': 'game_dev',
            'awsurl': '',
            'branch': '',
            'repeat_type': 'daily',
            'repeat_days': [],
            'enabled': True,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'id': str(uuid.uuid4()),
            'name': '주간 서버 패치 (월/수/금)',
            'time': '10:00',
            'option': '서버패치',
            'buildname': 'game_SEL',
            'awsurl': 'https://awsdeploy.pbb-qa.pubg.io/environment/sel-game',
            'branch': 'game',
            'repeat_type': 'weekly',
            'repeat_days': [0, 2, 4],  # 월, 수, 금
            'enabled': True,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    with open('schedule_sample.json', 'w', encoding='utf-8') as f:
        json.dump(sample_schedules, f, ensure_ascii=False, indent=2)
    
    print("✅ 샘플 스케줄 생성: schedule_sample.json")


if __name__ == '__main__':
    print("="*50)
    print("QuickBuild v2 - 스케줄 마이그레이션")
    print("="*50)
    print()
    
    # 마이그레이션 실행
    migrate_schedule_json()
    print()
    
    # 샘플 생성
    print("샘플 스케줄을 생성하시겠습니까? (y/n): ", end='')
    choice = input().strip().lower()
    if choice == 'y':
        create_sample_schedule()
    
    print()
    print("완료!")

