"""Selenium WebDriver 관리 모듈"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from src.utils.config import Config


class BrowserDriver:
    """Chrome WebDriver 관리 클래스"""

    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.driver: webdriver.Chrome | None = None

    def start(self) -> webdriver.Chrome:
        """Chrome 브라우저 시작 (일반 모드)"""
        options = Options()

        # Headful 모드 설정 (창이 보이도록)
        options.add_argument(f"--window-size={self.config.WINDOW_WIDTH},{self.config.WINDOW_HEIGHT}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # 한국어 설정
        options.add_argument("--lang=ko-KR")

        # WebDriver 자동 관리 (Selenium 4.6+ 내장 selenium-manager 사용)
        self.driver = webdriver.Chrome(options=options)

        # 자동화 감지 방지
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        return self.driver

    def get_driver(self) -> webdriver.Chrome | None:
        """현재 WebDriver 인스턴스 반환"""
        return self.driver

    def navigate(self, url: str) -> None:
        """지정된 URL로 이동"""
        if self.driver:
            self.driver.get(url)

    def get_page_source(self) -> str:
        """현재 페이지 HTML 소스 반환"""
        if self.driver:
            return self.driver.page_source
        return ""

    def get_current_url(self) -> str:
        """현재 URL 반환"""
        if self.driver:
            return self.driver.current_url
        return ""

    def open_new_tab(self, url: str = "") -> str | None:
        """새 탭 열기

        Args:
            url: 이동할 URL (비어있으면 빈 탭)

        Returns:
            새 탭의 window handle
        """
        if not self.driver:
            return None

        # 새 탭 열기
        self.driver.execute_script("window.open('');")
        new_handle = self.driver.window_handles[-1]

        # 새 탭으로 전환
        self.driver.switch_to.window(new_handle)

        # URL이 있으면 이동
        if url:
            self.driver.get(url)

        return new_handle

    def get_all_tabs(self) -> list[str]:
        """모든 탭 핸들 반환"""
        if self.driver:
            return self.driver.window_handles
        return []

    def switch_to_tab(self, handle: str) -> bool:
        """특정 탭으로 전환"""
        if self.driver and handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            return True
        return False

    def close_current_tab(self) -> None:
        """현재 탭 닫기"""
        if self.driver:
            self.driver.close()
            # 남은 탭이 있으면 마지막 탭으로 전환
            handles = self.driver.window_handles
            if handles:
                self.driver.switch_to.window(handles[-1])

    def execute_script(self, script: str, *args) -> any:
        """JavaScript 실행"""
        if self.driver:
            return self.driver.execute_script(script, *args)
        return None

    def execute_in_new_tab(self, script: str) -> str | None:
        """새 탭에서 스크립트 실행

        Returns:
            새 탭의 window handle
        """
        if not self.driver:
            return None

        new_handle = self.open_new_tab()
        if new_handle:
            self.driver.execute_script(script)
        return new_handle

    def quit(self) -> None:
        """브라우저 종료"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()
