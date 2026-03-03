"""로그인 감지 모듈"""
import time
from typing import Callable

from selenium import webdriver

from src.utils.config import Config


class LoginHandler:
    """BDU 포털 로그인 처리 클래스"""

    def __init__(self, driver: webdriver.Chrome, config: Config | None = None):
        self.driver = driver
        self.config = config or Config()

    def open_portal(self) -> None:
        """BDU 포털 페이지 열기"""
        self.driver.get(self.config.PORTAL_URL)

    def wait_for_login(
        self,
        on_progress: Callable[[str], None] | None = None,
        timeout: int | None = None,
    ) -> bool:
        """
        로그인 완료를 대기 (URL 폴링 방식)

        Args:
            on_progress: 진행 상태 콜백 함수
            timeout: 타임아웃 (초)

        Returns:
            로그인 성공 여부
        """
        timeout = timeout or self.config.LOGIN_TIMEOUT
        start_time = time.time()

        if on_progress:
            on_progress("로그인 대기 중... 브라우저에서 로그인해주세요.")

        while time.time() - start_time < timeout:
            current_url = self.driver.current_url

            # 로그인 완료 감지: URL이 포털 메인이 아닌 다른 페이지로 변경되었을 때
            if self._is_logged_in(current_url):
                if on_progress:
                    on_progress("로그인 완료!")
                return True

            time.sleep(self.config.LOGIN_CHECK_INTERVAL)

        if on_progress:
            on_progress("로그인 시간 초과")
        return False

    def _is_logged_in(self, current_url: str) -> bool:
        """
        로그인 여부 확인

        로그인 완료 조건:
        - URL이 포털 로그인 페이지가 아님
        - URL에 특정 키워드 포함 (main, home, lms 등)
        """
        login_indicators = ["main", "home", "dashboard", "mypage", "intro"]
        portal_login_page = self.config.PORTAL_URL

        # 포털 로그인 페이지가 아니고, 로그인 후 페이지 패턴과 일치
        if current_url != portal_login_page:
            for indicator in login_indicators:
                if indicator in current_url.lower():
                    return True

            # 또는 URL이 변경되었으면 로그인된 것으로 간주
            if len(current_url) > len(portal_login_page) + 10:
                return True

        return False

    def navigate_to_lms(self) -> bool:
        """LMS 페이지로 이동"""
        try:
            print(f"LMS 이동 시도: {self.config.LMS_URL}")
            self.driver.get(self.config.LMS_URL)
            time.sleep(5)  # 페이지 로딩 대기 (증가)
            print(f"현재 URL: {self.driver.current_url}")
            return True
        except Exception as e:
            print(f"LMS 이동 실패: {e}")
            return False

    def get_lms_page_source(self) -> str:
        """LMS 페이지 HTML 소스 반환"""
        return self.driver.page_source
