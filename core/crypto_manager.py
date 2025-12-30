"""암호화 관리 모듈 - Slack 토큰 보안"""
from cryptography.fernet import Fernet
import os
import base64
import hashlib


class CryptoManager:
    """토큰 암호화/복호화 관리"""
    
    @staticmethod
    def generate_key_from_machine():
        """
        머신 고유 정보로 암호화 키 생성
        각 PC마다 다른 키가 생성되므로 토큰 유출 시에도 다른 PC에서 복호화 불가
        """
        # 머신 고유 정보 수집
        import platform
        import uuid
        
        machine_info = f"{platform.node()}-{uuid.getnode()}"
        
        # SHA256 해시 생성 후 Fernet 키 형식으로 변환
        hash_object = hashlib.sha256(machine_info.encode())
        key = base64.urlsafe_b64encode(hash_object.digest())
        
        return key
    
    @staticmethod
    def encrypt_token(token: str) -> str:
        """
        토큰 암호화
        
        Args:
            token: 암호화할 토큰
            
        Returns:
            암호화된 토큰 (base64 문자열)
        """
        key = CryptoManager.generate_key_from_machine()
        fernet = Fernet(key)
        
        encrypted = fernet.encrypt(token.encode())
        return encrypted.decode()
    
    @staticmethod
    def decrypt_token(encrypted_token: str) -> str:
        """
        토큰 복호화
        
        Args:
            encrypted_token: 암호화된 토큰
            
        Returns:
            복호화된 원본 토큰
        """
        try:
            key = CryptoManager.generate_key_from_machine()
            fernet = Fernet(key)
            
            decrypted = fernet.decrypt(encrypted_token.encode())
            return decrypted.decode()
        except Exception as e:
            raise Exception(f"토큰 복호화 실패: {e}")
    
    @staticmethod
    def encrypt_and_save(token: str, channel_id: str, output_file: str = 'feedback_config_encrypted.json'):
        """
        토큰과 채널 ID를 암호화하여 파일에 저장
        
        Args:
            token: Slack Bot Token
            channel_id: Slack Channel ID
            output_file: 저장할 파일명
        """
        import json
        
        encrypted_data = {
            'bot_token': CryptoManager.encrypt_token(token),
            'channel_id': CryptoManager.encrypt_token(channel_id),
            'encrypted': True,
            'note': 'This file is encrypted with machine-specific key. Safe to commit to Git.'
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(encrypted_data, f, indent=2)
        
        print(f"✅ 암호화 완료: {output_file}")
        print(f"   Bot Token: {token[:20]}... → 암호화됨")
        print(f"   Channel ID: {channel_id} → 암호화됨")
    
    @staticmethod
    def load_and_decrypt(input_file: str = 'feedback_config_encrypted.json') -> dict:
        """
        암호화된 파일을 읽어서 복호화
        
        Args:
            input_file: 읽을 파일명
            
        Returns:
            {'bot_token': str, 'channel_id': str}
        """
        import json
        
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"암호화 파일이 없습니다: {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            encrypted_data = json.load(f)
        
        if not encrypted_data.get('encrypted'):
            raise Exception("암호화되지 않은 파일입니다")
        
        return {
            'bot_token': CryptoManager.decrypt_token(encrypted_data['bot_token']),
            'channel_id': CryptoManager.decrypt_token(encrypted_data['channel_id'])
        }


# 암호화 유틸리티 스크립트
if __name__ == '__main__':
    print("=" * 60)
    print("Slack 토큰 암호화 도구")
    print("=" * 60)
    
    # 토큰 입력
    bot_token = input("\nSlack Bot Token 입력: ").strip()
    channel_id = input("Slack Channel ID 입력: ").strip()
    
    if not bot_token or not channel_id:
        print("❌ 토큰과 채널 ID를 모두 입력하세요")
        exit(1)
    
    # 암호화 및 저장
    CryptoManager.encrypt_and_save(bot_token, channel_id)
    
    print("\n" + "=" * 60)
    print("✅ 완료!")
    print("=" * 60)
    print("\n다음 단계:")
    print("1. feedback_config_encrypted.json 파일이 생성되었습니다")
    print("2. 이 파일은 Git에 안전하게 커밋할 수 있습니다")
    print("3. 다른 PC에서는 복호화되지 않으므로 안전합니다")

