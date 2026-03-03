"""CustomTkinter 메인 앱"""
import threading
import customtkinter as ctk

from src.browser.driver import BrowserDriver
from src.browser.login import LoginHandler
from src.parser.lms_parser import LMSParser, CourseInfo
from src.gui.dashboard import Dashboard
from src.gui.components import CourseConfirmModal
from src.utils.config import Config


class BDUTrackerApp(ctk.CTk):
    """BDU LMS 트래커 애플리케이션"""

    def __init__(self):
        super().__init__()

        self.config = Config()
        self.browser: BrowserDriver | None = None
        self.login_handler: LoginHandler | None = None
        self.is_logged_in = False

        self._setup_window()
        self._create_dashboard()

    def _setup_window(self) -> None:
        """윈도우 설정"""
        # 라이트 모드 설정
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title(self.config.APP_TITLE)
        self.geometry(f"{self.config.APP_WIDTH}x{self.config.APP_HEIGHT}")
        self.minsize(600, 400)

        # 윈도우 중앙 배치
        self._center_window()

    def _center_window(self) -> None:
        """윈도우를 화면 중앙에 배치"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _create_dashboard(self) -> None:
        """대시보드 생성"""
        self.dashboard = Dashboard(
            self,
            config=self.config,
            on_login_click=self._on_login,
            on_refresh_click=self._on_refresh,
            on_go_lms_click=self._on_go_lms,
            on_course_click=self._on_course_click,
        )
        self.dashboard.pack(fill="both", expand=True)

    def _on_login(self) -> None:
        """로그인 버튼 클릭 핸들러"""
        self.dashboard.set_buttons_enabled(login=False, refresh=False, go_lms=False)
        self.dashboard.set_status("브라우저 시작 중...", "loading")

        # 백그라운드 스레드에서 브라우저 작업 실행
        thread = threading.Thread(target=self._login_process, daemon=True)
        thread.start()

    def _login_process(self) -> None:
        """로그인 프로세스 (백그라운드 스레드) - 포털만 열기"""
        try:
            # 브라우저 시작
            self.browser = BrowserDriver(self.config)
            driver = self.browser.start()

            self.login_handler = LoginHandler(driver, self.config)

            # 포털 페이지 열기
            self._update_status("포털 페이지 접속 중...", "loading")
            self.login_handler.open_portal()

            # 로그인 안내
            self._update_status("브라우저에서 로그인 후 '강의페이지' 버튼을 클릭하세요.", "waiting")

        except Exception as e:
            self._update_status(f"오류: {str(e)}", "error")

        finally:
            self._enable_buttons()

    def _fetch_courses(self) -> None:
        """수강 과목 정보 가져오기"""
        import time

        try:
            if not self.login_handler:
                return

            # LMS 페이지로 이동
            self._update_status("LMS 페이지로 이동 중...", "loading")
            if not self.login_handler.navigate_to_lms():
                self._update_status("LMS 페이지 접속 실패", "error")
                return

            # 페이지 로딩 대기
            self._update_status("페이지 로딩 대기 중...", "loading")
            time.sleep(3)

            # 현재 URL 표시
            current_url = self.login_handler.driver.current_url
            self._update_status(f"페이지 로드 완료: {current_url[:50]}...", "loading")

            # 파싱 전 추가 대기
            time.sleep(2)

            # HTML 파싱
            self._update_status("과목 정보 파싱 중...", "loading")
            html = self.login_handler.get_lms_page_source()
            parser = LMSParser(html)
            courses = parser.parse()

            if courses:
                self._update_status(f"{len(courses)}개 과목 발견!", "success")
                self.after(0, lambda: self.dashboard.display_courses(courses))
            else:
                self._update_status("과목 정보를 찾을 수 없습니다.", "error")

        except Exception as e:
            self._update_status(f"파싱 오류: {str(e)}", "error")

    def _on_go_lms(self) -> None:
        """강의페이지 버튼 클릭 핸들러"""
        if not self.login_handler:
            self.dashboard.set_status("먼저 포털을 열어주세요.", "error")
            return

        self.dashboard.set_buttons_enabled(login=False, refresh=False, go_lms=False)
        self.dashboard.set_status("강의페이지로 이동 중...", "loading")

        # 백그라운드 스레드에서 실행
        thread = threading.Thread(target=self._go_lms_process, daemon=True)
        thread.start()

    def _go_lms_process(self) -> None:
        """강의페이지 이동 프로세스 (백그라운드 스레드)"""
        try:
            self.is_logged_in = True
            self._fetch_courses()
        except Exception as e:
            self._update_status(f"오류: {str(e)}", "error")
        finally:
            self._enable_buttons()

    def _on_course_click(self, course: CourseInfo) -> None:
        """과목 카드 클릭 핸들러 - 모달 표시"""
        if not self.login_handler:
            self.dashboard.set_status("먼저 포털을 열어주세요.", "error")
            return

        if not course.onclick_script:
            self.dashboard.set_status("강의실 이동 정보가 없습니다.", "error")
            return

        # 확인 모달 표시
        CourseConfirmModal(
            self,
            course,
            on_cancel=self._on_modal_cancel,
        )

    def _on_modal_cancel(self) -> None:
        """모달 취소 - LMS 페이지로 이동"""
        self.dashboard.set_status("LMS 페이지로 이동 중...", "loading")
        thread = threading.Thread(target=self._go_lms_process, daemon=True)
        thread.start()

    def _start_lecture(self, course: CourseInfo) -> None:
        """강의 수강 시작"""
        self.dashboard.set_status(f"'{course.name}' 강의실로 이동 중...", "loading")

        # 백그라운드 스레드에서 실행
        thread = threading.Thread(
            target=self._navigate_to_lecture, args=(course,), daemon=True
        )
        thread.start()

    def _navigate_to_lecture(self, course: CourseInfo) -> None:
        """강의실로 이동 (백그라운드 스레드)"""
        try:
            # onclick 스크립트 실행
            self.login_handler.driver.execute_script(course.onclick_script)
            self._update_status(f"'{course.name}' 강의실 열림", "success")
        except Exception as e:
            self._update_status(f"강의실 이동 실패: {str(e)}", "error")

    def _on_refresh(self) -> None:
        """새로고침 버튼 클릭 핸들러"""
        if not self.is_logged_in:
            self.dashboard.set_status("먼저 강의페이지로 이동해주세요.", "error")
            return

        self.dashboard.set_buttons_enabled(login=False, refresh=False, go_lms=False)
        self.dashboard.set_status("새로고침 중...", "loading")

        # 백그라운드 스레드에서 실행
        thread = threading.Thread(target=self._refresh_process, daemon=True)
        thread.start()

    def _refresh_process(self) -> None:
        """새로고침 프로세스 (백그라운드 스레드)"""
        try:
            self._fetch_courses()
        except Exception as e:
            self._update_status(f"새로고침 오류: {str(e)}", "error")
        finally:
            self._enable_buttons()

    def _update_status(self, message: str, status_type: str = "normal") -> None:
        """상태 업데이트 (스레드 안전)"""
        self.after(0, lambda: self.dashboard.set_status(message, status_type))

    def _enable_buttons(self) -> None:
        """버튼 활성화 (스레드 안전)"""
        self.after(0, lambda: self.dashboard.set_buttons_enabled(True, True, True))

    def on_closing(self) -> None:
        """앱 종료 시 정리"""
        if self.browser:
            self.browser.quit()
        self.destroy()

    def run(self) -> None:
        """앱 실행"""
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.mainloop()
