from functools import lru_cache
from typing import Union

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


@lru_cache
def _get_cipher() -> Fernet:
    """根据配置的 ENCRYPTION_KEY 获取全局 Fernet 加密器"""
    key: Union[str, bytes] = settings.ENCRYPTION_KEY
    if not key:
        raise ValueError("未配置 ENCRYPTION_KEY，无法执行加密/解密操作")
    if isinstance(key, str):
        key_bytes = key.encode()
    else:
        key_bytes = key
    try:
        return Fernet(key_bytes)
    except (ValueError, TypeError) as exc:
        raise ValueError("ENCRYPTION_KEY 非法，请提供有效的Fernet密钥") from exc


def encrypt_text(plain_text: str) -> str:
    """使用Fernet加密文本"""
    if plain_text is None:
        return ""
    cipher = _get_cipher()
    token = cipher.encrypt(plain_text.encode())
    return token.decode()


def decrypt_text(token: str) -> str:
    """解密Fernet密文"""
    if not token:
        return ""
    cipher = _get_cipher()
    try:
        plain = cipher.decrypt(token.encode())
        return plain.decode()
    except InvalidToken as exc:
        raise ValueError("API密钥解密失败，请确认ENCRYPTION_KEY是否正确") from exc
