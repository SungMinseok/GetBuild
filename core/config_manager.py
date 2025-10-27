"""설정 및 환경 관리 모듈"""
import json
import os
from typing import Dict, List, Any, Optional


class ConfigManager:
    """config.json, settings.json 등 설정 파일 관리"""
    
    def __init__(self, config_path: str = 'config.json', settings_path: str = 'settings.json'):
        self.config_path = config_path
        self.settings_path = settings_path
    
    def load_json(self, path: str) -> Dict[str, Any]:
        """JSON 파일 로드"""
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"JSON 로드 오류 ({path}): {e}")
            return {}
    
    def save_json(self, path: str, data: Dict[str, Any]) -> None:
        """JSON 파일 저장"""
        try:
            dirname = os.path.dirname(path)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"JSON 저장 오류 ({path}): {e}")
    
    # Config 관리
    def get_buildnames(self) -> List[str]:
        """빌드명 목록 조회"""
        config = self.load_json(self.config_path)
        names = config.get('buildnames', [])
        return [str(n) for n in names] if isinstance(names, list) else []
    
    def add_buildname(self, name: str) -> List[str]:
        """빌드명 추가"""
        if not name.strip():
            return self.get_buildnames()
        config = self.load_json(self.config_path)
        names = config.get('buildnames', [])
        if not isinstance(names, list):
            names = []
        if name not in names:
            names.append(name)
        config['buildnames'] = names
        self.save_json(self.config_path, config)
        return names
    
    def remove_buildname(self, name: str) -> List[str]:
        """빌드명 삭제"""
        config = self.load_json(self.config_path)
        names = config.get('buildnames', [])
        if isinstance(names, list) and name in names:
            names.remove(name)
        config['buildnames'] = names
        self.save_json(self.config_path, config)
        return names if isinstance(names, list) else []
    
    def get_awsurls(self) -> List[str]:
        """AWS URL 목록 조회"""
        config = self.load_json(self.config_path)
        urls = config.get('awsurl', [])
        return [str(u) for u in urls] if isinstance(urls, list) else []
    
    # Settings 관리
    def load_settings(self) -> Dict[str, Any]:
        """설정 로드"""
        return self.load_json(self.settings_path)
    
    def save_settings(self, settings: Dict[str, Any]) -> None:
        """설정 저장"""
        self.save_json(self.settings_path, settings)
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """특정 설정값 조회"""
        settings = self.load_settings()
        return settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """특정 설정값 저장"""
        settings = self.load_settings()
        settings[key] = value
        self.save_settings(settings)

