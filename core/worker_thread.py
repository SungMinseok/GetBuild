"""작업 실행 스레드 모듈"""
from PyQt5.QtCore import QThread, pyqtSignal
from typing import Dict, Any, Callable, Optional
import traceback


class WorkerThread(QThread):
    """백그라운드 작업 실행 스레드"""
    
    # 시그널 정의
    progress = pyqtSignal(int)  # 진행률 (0-100)
    status = pyqtSignal(str)  # 상태 메시지
    finished = pyqtSignal(bool, str)  # (성공 여부, 결과/오류 메시지)
    log = pyqtSignal(str)  # 로그 메시지
    
    def __init__(self, task_func: Callable, task_args: tuple = (), task_kwargs: dict = None):
        """
        Args:
            task_func: 실행할 함수
            task_args: 함수 인자 (튜플)
            task_kwargs: 함수 키워드 인자 (딕셔너리)
        """
        super().__init__()
        self.task_func = task_func
        self.task_args = task_args
        self.task_kwargs = task_kwargs or {}
        self._is_cancelled = False
    
    def run(self):
        """스레드 실행"""
        try:
            self.status.emit("작업 시작...")
            self.log.emit(f"[작업 시작] {self.task_func.__name__}")
            
            # 작업 실행
            result = self.task_func(*self.task_args, **self.task_kwargs)
            
            if self._is_cancelled:
                self.log.emit("[작업 취소됨]")
                self.finished.emit(False, "사용자에 의해 취소됨")
            else:
                self.log.emit(f"[작업 완료] 결과: {result}")
                self.finished.emit(True, str(result) if result else "완료")
        
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            error_trace = traceback.format_exc()
            self.log.emit(f"[작업 오류]\n{error_trace}")
            self.finished.emit(False, error_msg)
    
    def cancel(self):
        """작업 취소 요청"""
        self._is_cancelled = True
        self.log.emit("[취소 요청됨]")
    
    def is_cancelled(self) -> bool:
        """취소 여부 확인"""
        return self._is_cancelled
    
    def emit_progress(self, value: int):
        """진행률 업데이트 (작업 함수에서 호출)"""
        if not self._is_cancelled:
            self.progress.emit(value)
    
    def emit_status(self, message: str):
        """상태 메시지 업데이트 (작업 함수에서 호출)"""
        if not self._is_cancelled:
            self.status.emit(message)


class ScheduleWorkerThread(WorkerThread):
    """스케줄 전용 작업 스레드 (스케줄 정보 포함)"""
    
    schedule_started = pyqtSignal(dict)  # 스케줄 시작 시그널
    schedule_finished = pyqtSignal(dict, bool, str)  # 스케줄 완료 시그널 (스케줄, 성공여부, 메시지)
    
    def __init__(self, schedule: Dict[str, Any], task_func: Callable, 
                 task_args: tuple = (), task_kwargs: dict = None):
        """
        Args:
            schedule: 스케줄 정보 (dict)
            task_func: 실행할 함수
            task_args: 함수 인자
            task_kwargs: 함수 키워드 인자
        """
        super().__init__(task_func, task_args, task_kwargs)
        self.schedule = schedule
    
    def run(self):
        """스레드 실행 (스케줄 정보 포함)"""
        try:
            self.schedule_started.emit(self.schedule)
            
            schedule_name = self.schedule.get('name', 'Unknown')
            schedule_option = self.schedule.get('option', 'Unknown')
            
            self.status.emit(f"{schedule_name} 실행 중...")
            self.log.emit(f"[스케줄 시작] {schedule_name} ({schedule_option})")
            
            # 작업 실행
            result = self.task_func(*self.task_args, **self.task_kwargs)
            
            if self._is_cancelled:
                self.log.emit(f"[스케줄 취소] {schedule_name}")
                self.schedule_finished.emit(self.schedule, False, "취소됨")
                self.finished.emit(False, "취소됨")
            else:
                self.log.emit(f"[스케줄 완료] {schedule_name}")
                self.schedule_finished.emit(self.schedule, True, str(result) if result else "완료")
                self.finished.emit(True, str(result) if result else "완료")
        
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            error_trace = traceback.format_exc()
            self.log.emit(f"[스케줄 오류] {self.schedule.get('name', 'Unknown')}\n{error_trace}")
            self.schedule_finished.emit(self.schedule, False, error_msg)
            self.finished.emit(False, error_msg)

