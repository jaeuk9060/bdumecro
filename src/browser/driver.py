"""Selenium WebDriver 관리 모듈"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from src.utils.config import Config


class BrowserDriver:
    """Chrome WebDriver 관리 클래스"""

    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.driver: webdriver.Chrome | None = None

    def start(self) -> webdriver.Chrome:
        """Chrome 브라우저 시작 (headful 모드)"""
        options = Options()

        # Headful 모드 설정 (창이 보이도록)
        options.add_argument(f"--window-size={self.config.WINDOW_WIDTH},{self.config.WINDOW_HEIGHT}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # 한국어 설정
        options.add_argument("--lang=ko-KR")

        # WebDriver 자동 관리
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

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
