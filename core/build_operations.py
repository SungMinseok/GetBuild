"""빌드 복사/압축 관련 작업 모듈"""
import os
import shutil
import zipfile
from typing import Callable, Optional
import re


class BuildOperations:
    """빌드 파일 복사, 압축 등의 작업"""
    
    @staticmethod
    def extract_revision_number(folder_name: str) -> int:
        """폴더명에서 리비전 번호 추출 (_r 뒤의 숫자)"""
        match = re.search(r'_r(\d+)', folder_name)
        return int(match.group(1)) if match else 0
    
    @staticmethod
    def get_file_count(folder_path: str) -> int:
        """폴더 내 파일 개수 계산"""
        return sum(len(files) for _, _, files in os.walk(folder_path))
    
    @staticmethod
    def copy_folder(src_path: str, dest_path: str, 
                   progress_callback: Optional[Callable[[int], None]] = None,
                   cancel_check: Optional[Callable[[], bool]] = None) -> None:
        """
        폴더 복사
        
        Args:
            src_path: 소스 폴더 경로
            dest_path: 대상 폴더 경로
            progress_callback: 진행률 콜백 (0~100)
            cancel_check: 취소 체크 콜백 (True 반환시 중단)
        """
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        
        all_files = []
        for root, dirs, files in os.walk(src_path):
            for file in files:
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(root, src_path)
                all_files.append((src_file, rel_path, file))
        
        total = len(all_files)
        for idx, (src_file, rel_path, file) in enumerate(all_files):
            if cancel_check and cancel_check():
                raise InterruptedError("복사 취소됨")
            
            dest_dir = os.path.join(dest_path, rel_path)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.copy(src_file, dest_dir)
            
            if progress_callback and total > 0:
                progress = int((idx + 1) / total * 100)
                progress_callback(progress)
    
    @staticmethod
    def zip_folder(src_path: str, zip_path: str,
                  progress_callback: Optional[Callable[[int], None]] = None,
                  cancel_check: Optional[Callable[[], bool]] = None) -> None:
        """
        폴더 압축
        
        Args:
            src_path: 소스 폴더 경로
            zip_path: ZIP 파일 경로
            progress_callback: 진행률 콜백 (0~100)
            cancel_check: 취소 체크 콜백
        """
        all_files = []
        for root, dirs, files in os.walk(src_path):
            for file in files:
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(root, src_path)
                all_files.append((src_file, rel_path, file))
        
        total = len(all_files)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for idx, (src_file, rel_path, file) in enumerate(all_files):
                if cancel_check and cancel_check():
                    raise InterruptedError("압축 취소됨")
                
                arcname = os.path.join(rel_path, file)
                zipf.write(src_file, arcname)
                
                if progress_callback and total > 0:
                    progress = int((idx + 1) / total * 100)
                    progress_callback(progress)
    
    @staticmethod
    def get_latest_builds(source_path: str, filter_texts: list, max_count: int = 50) -> list:
        """
        최신 빌드 목록 조회 (리비전 기준 내림차순)
        
        Args:
            source_path: 빌드 소스 경로
            filter_texts: 필터 텍스트 목록
            max_count: 최대 개수
        
        Returns:
            빌드 폴더명 목록
        """
        if not os.path.isdir(source_path):
            return []
        
        folders = [f for f in os.listdir(source_path) 
                  if os.path.isdir(os.path.join(source_path, f))]
        
        # 리비전 번호로 정렬
        folders.sort(key=BuildOperations.extract_revision_number, reverse=True)
        
        result = []
        for folder in folders:
            if len(result) >= max_count:
                break
            
            folder_path = os.path.join(source_path, folder)
            version_file = os.path.join(folder_path, "version.txt")
            
            # version.txt 존재 확인 (첫 번째 제외)
            if len(result) >= 1 and not os.path.isfile(version_file):
                continue
            
            # 필터 적용
            if not filter_texts or any(ft in folder for ft in filter_texts):
                result.append(folder)
        
        return result
    
    @staticmethod
    def generate_backend_bat_files(output_dir: str, server_list: list) -> None:
        """백엔드 접속용 BAT 파일 생성"""
        base_command = r'start WindowsClient\Client.exe -HardwareBenchmark -gpucrashdebugging -aftermathall -norenderdoc -nosteam'
        
        for server in server_list:
            sanitized_name = server.replace(":", "_").replace(".", "_")
            bat_filename = f"{sanitized_name}.bat"
            bat_path = os.path.join(output_dir, bat_filename)
            
            command = f'{base_command} -Backend="{server}" -Backend_ssl=yes -Backend_root_cert=""'
            
            try:
                with open(bat_path, "w", encoding="utf-8") as f:
                    f.write(command)
            except Exception as e:
                print(f"BAT 파일 생성 오류 ({bat_filename}): {e}")

