"""설정 관리 모듈"""
from dataclasses import dataclass


@dataclass
class Config:
    """애플리케이션 설정"""

    # BDU Portal URLs
    PORTAL_URL: str = "https://portal.bdu.ac.kr/"
    LMS_URL: str = "https://lms.bdu.ac.kr/"

    # Login detection
    LOGIN_CHECK_INTERVAL: float = 1.0  # 초
    LOGIN_TIMEOUT: int = 300  # 5분

    # Browser settings
    WINDOW_WIDTH: int = 1200
    WINDOW_HEIGHT: int = 800

    # GUI settings
    APP_TITLE: str = "BDU LMS 트래커"
    APP_WIDTH: int = 800
    APP_HEIGHT: int = 600
