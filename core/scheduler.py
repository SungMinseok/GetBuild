"""스케줄 관리 모듈"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class ScheduleManager:
    """예약 스케줄 관리 (daily/weekly 반복 지원)"""
    
    def __init__(self, schedule_path: str = 'schedule.json'):
        self.schedule_path = schedule_path
    
    def load_schedules(self) -> List[Dict[str, str]]:
        """스케줄 목록 로드 (dict 또는 list 포맷 모두 지원)"""
        if not os.path.exists(self.schedule_path):
            return []
        
        try:
            with open(self.schedule_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # dict 포맷 (구버전 호환): {"HH:MM": {option, buildname, ...}}
            if isinstance(data, dict):
                schedules = []
                for time_str, info in data.items():
                    if isinstance(info, dict):
                        schedule = {'time': time_str}
                        schedule.update(info)
                        schedules.append(schedule)
                return schedules
            
            # list 포맷 (신버전)
            if isinstance(data, list):
                return [s for s in data if isinstance(s, dict) and s.get('time')]
            
            return []
        except Exception as e:
            print(f"스케줄 로드 오류: {e}")
            return []
    
    def save_schedules(self, schedules: List[Dict[str, str]]) -> None:
        """스케줄 목록 저장 (list 포맷)"""
        try:
            with open(self.schedule_path, 'w', encoding='utf-8') as f:
                json.dump(schedules, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"스케줄 저장 오류: {e}")
    
    def add_schedule(self, time: str, option: str, buildname: str, 
                    awsurl: str = '', branch: str = '', 
                    repeat_type: str = 'once', repeat_days: List[int] = None,
                    enabled: bool = True, name: str = '') -> str:
        """
        스케줄 추가
        
        Args:
            time: 실행 시간 (HH:MM)
            option: 실행 옵션
            buildname: 빌드명
            awsurl: AWS URL
            branch: 브랜치명
            repeat_type: 반복 유형 ('once', 'daily', 'weekly')
            repeat_days: 반복 요일 (0=월, 1=화, ..., 6=일) - weekly일 때만 사용
            enabled: 활성화 여부
            name: 스케줄 이름 (선택)
        
        Returns:
            생성된 스케줄 ID
        """
        schedules = self.load_schedules()
        schedule_id = str(uuid.uuid4())
        
        new_schedule = {
            'id': schedule_id,
            'name': name or f"{option} - {time}",
            'time': time,
            'option': option,
            'buildname': buildname,
            'awsurl': awsurl,
            'branch': branch,
            'repeat_type': repeat_type,
            'repeat_days': repeat_days or [],
            'enabled': enabled,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        schedules.append(new_schedule)
        self.save_schedules(schedules)
        return schedule_id
    
    def update_schedule(self, schedule_id: str, updates: Dict[str, Any]) -> bool:
        """스케줄 업데이트"""
        schedules = self.load_schedules()
        for schedule in schedules:
            if schedule.get('id') == schedule_id:
                schedule.update(updates)
                self.save_schedules(schedules)
                return True
        return False
    
    def delete_schedule(self, schedule_id: str, force: bool = False) -> bool:
        """
        스케줄 삭제 (ID 기준)
        
        Args:
            schedule_id: 삭제할 스케줄 ID
            force: True면 JSON 파싱 오류 시에도 강제 삭제
        
        Returns:
            삭제 성공 여부
        """
        try:
            schedules = self.load_schedules()
            original_len = len(schedules)
            schedules = [s for s in schedules if s.get('id') != schedule_id]
            if len(schedules) < original_len:
                self.save_schedules(schedules)
                return True
            return False
        except Exception as e:
            if force:
                # 강제 삭제: 파일을 직접 읽어서 처리
                print(f"JSON 파싱 오류, 강제 삭제 시도: {e}")
                try:
                    with open(self.schedule_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 백업 생성
                    backup_path = f"{self.schedule_path}.error_backup"
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"오류 파일 백업: {backup_path}")
                    
                    # 빈 리스트로 초기화
                    self.save_schedules([])
                    print("스케줄 파일 초기화됨")
                    return True
                except Exception as e2:
                    print(f"강제 삭제 실패: {e2}")
                    return False
            raise
    
    def toggle_schedule(self, schedule_id: str) -> Optional[bool]:
        """스케줄 활성화/비활성화 토글"""
        schedules = self.load_schedules()
        for schedule in schedules:
            if schedule.get('id') == schedule_id:
                schedule['enabled'] = not schedule.get('enabled', True)
                self.save_schedules(schedules)
                return schedule['enabled']
        return None
    
    def copy_schedule(self, schedule_id: str) -> Optional[str]:
        """
        스케줄 복사
        
        Args:
            schedule_id: 복사할 스케줄 ID
        
        Returns:
            새로 생성된 스케줄 ID (실패 시 None)
        """
        schedule = self.get_schedule_by_id(schedule_id)
        if not schedule:
            return None
        
        # 새 스케줄 생성 (ID와 생성 시각만 새로 생성)
        new_schedule = schedule.copy()
        new_schedule['id'] = str(uuid.uuid4())
        new_schedule['name'] = f"{schedule.get('name', 'Unknown')} (복사본)"
        new_schedule['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        schedules = self.load_schedules()
        schedules.append(new_schedule)
        self.save_schedules(schedules)
        
        return new_schedule['id']
    
    def get_due_schedules(self, current_time: str, current_date: datetime = None) -> List[Dict[str, str]]:
        """
        현재 시각에 실행해야 할 스케줄 조회
        
        Args:
            current_time: 현재 시간 (HH:MM)
            current_date: 현재 날짜 (기본값: 현재 시각)
        
        Returns:
            실행해야 할 스케줄 목록 (활성화된 것만)
        """
        if current_date is None:
            current_date = datetime.now()
        
        schedules = self.load_schedules()
        due_schedules = []
        
        for schedule in schedules:
            # 비활성화된 스케줄은 건너뜀
            if not schedule.get('enabled', True):
                continue
            
            # 시간이 일치하지 않으면 건너뜀
            if schedule.get('time') != current_time:
                continue
            
            repeat_type = schedule.get('repeat_type', 'once')
            
            # 일회성
            if repeat_type == 'once':
                due_schedules.append(schedule)
            
            # 매일 반복
            elif repeat_type == 'daily':
                due_schedules.append(schedule)
            
            # 주간 반복 (특정 요일만)
            elif repeat_type == 'weekly':
                current_weekday = current_date.weekday()  # 0=월, 6=일
                repeat_days = schedule.get('repeat_days', [])
                if current_weekday in repeat_days:
                    due_schedules.append(schedule)
        
        return due_schedules
    
    def get_schedule_by_id(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """ID로 스케줄 조회"""
        schedules = self.load_schedules()
        for schedule in schedules:
            if schedule.get('id') == schedule_id:
                return schedule
        return None
    
    def remove_schedule(self, index: int) -> None:
        """스케줄 삭제 (인덱스 기준)"""
        schedules = self.load_schedules()
        if 0 <= index < len(schedules):
            schedules.pop(index)
            self.save_schedules(schedules)
    
    def get_formatted_schedules(self) -> str:
        """스케줄 포맷팅 (UI 표시용)"""
        schedules = self.load_schedules()
        schedules.sort(key=lambda x: x.get('time', ''))
        
        if not schedules:
            return "등록된 스케줄이 없습니다."
        
        lines = []
        for s in schedules:
            # 반복 유형 표시
            repeat_type = s.get('repeat_type', 'once')
            if repeat_type == 'once':
                repeat_str = '일회'
            elif repeat_type == 'daily':
                repeat_str = '매일'
            elif repeat_type == 'weekly':
                days = s.get('repeat_days', [])
                day_names = ['월', '화', '수', '목', '금', '토', '일']
                repeat_str = '매주 ' + ','.join([day_names[d] for d in days])
            else:
                repeat_str = repeat_type
            
            # 활성화 상태
            enabled = '✓' if s.get('enabled', True) else '✗'
            
            name = s.get('name', s.get('option', ''))
            time = s.get('time', '')
            
            line = f"[{enabled}] {time} | {repeat_str} | {name}"
            lines.append(line)
        return '\n'.join(lines)

