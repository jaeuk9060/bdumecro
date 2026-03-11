"""CustomTkinter 메인 앱"""
import logging
import threading
import time
import customtkinter as ctk
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

from src.browser.driver import BrowserDriver
from src.browser.login import LoginHandler
from src.parser.lms_parser import LMSParser, CourseInfo
from src.gui.dashboard import Dashboard
from src.gui.components import CourseConfirmModal
from src.utils.config import Config

logger = logging.getLogger(__name__)


class BDUTrackerApp(ctk.CTk):
    """BDU LMS 트래커 애플리케이션"""

    def __init__(self):
        super().__init__()

        self.config = Config()
        self.browser: BrowserDriver | None = None
        self.login_handler: LoginHandler | None = None
        self.is_logged_in = False
        self.courses: list[CourseInfo] = []  # 과목 목록 저장

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
            on_all_courses_click=self._on_all_courses_click,
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
                self.courses = courses  # 인스턴스에 저장
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
            on_confirm=lambda: self._on_modal_confirm(course),
            on_cancel=self._on_modal_cancel,
        )

    def _on_modal_confirm(self, course: CourseInfo) -> None:
        """모달 확인 - 전체 강의 새 탭으로 열기"""
        self.dashboard.set_status(f"'{course.name}' 강의 재생 준비 중...", "loading")
        thread = threading.Thread(
            target=self._open_all_lectures, args=(course,), daemon=True
        )
        thread.start()

    def _on_modal_cancel(self) -> None:
        """모달 취소 - LMS 페이지로 이동"""
        self.dashboard.set_status("LMS 페이지로 이동 중...", "loading")
        thread = threading.Thread(target=self._go_lms_process, daemon=True)
        thread.start()

    def _on_all_courses_click(self) -> None:
        """전체 자동 시청 버튼 클릭"""
        if not self.login_handler:
            self.dashboard.set_status("먼저 포털을 열어주세요.", "error")
            return

        self.dashboard.set_buttons_enabled(False, False, False, False)
        self.dashboard.set_status("미청취 과목 탐색 및 자동 시청 시작...", "loading")
        thread = threading.Thread(
            target=self._play_all_incomplete_courses,
            daemon=True
        )
        thread.start()

    def _play_all_incomplete_courses(self) -> None:
        """모든 미완료 과목을 순차적으로 시청 (매 과목 완료 후 재탐색)"""
        completed_count = 0

        try:
            while True:
                # 1. LMS 메인으로 이동
                self._update_status("LMS 페이지로 이동 중...", "loading")
                driver = self.login_handler.driver
                driver.get(self.config.LMS_URL)
                time.sleep(3)

                # 2. 과목 리스트 재파싱
                self._update_status("미청취 과목 탐색 중...", "loading")
                html = self.login_handler.get_lms_page_source()
                parser = LMSParser(html)
                courses = parser.parse()

                # 3. 미청취 강의가 있는 과목 필터링
                incomplete = [c for c in courses if c.remaining_lectures > 0]

                # 4. 미청취 과목이 없으면 종료
                if not incomplete:
                    self._update_status(
                        f"전체 {completed_count}개 과목 완료! 더 이상 미청취 강의 없음",
                        "success"
                    )
                    break

                # 5. 첫 번째 미완료 과목 시청
                course = incomplete[0]
                self._update_status(
                    f"'{course.name}' 시청 시작... (미청취: {course.remaining_lectures}개)",
                    "loading"
                )

                self._open_all_lectures(course)
                completed_count += 1
                self._update_status(
                    f"'{course.name}' 완료! 다음 과목 탐색 중...",
                    "loading"
                )

        except Exception as e:
            logger.error(f"전체 시청 중 오류: {e}")
            self._update_status(f"오류 발생: {str(e)}", "error")
        finally:
            self._enable_buttons()

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

    def _open_all_lectures(self, course: CourseInfo) -> None:
        """전체 미청취 강의를 새 탭으로 열기 (백그라운드 스레드)"""
        try:
            driver = self.login_handler.driver

            # 1. 강의실로 이동
            self._update_status(f"'{course.name}' 강의실 이동 중...", "loading")
            driver.execute_script(course.onclick_script)
            time.sleep(3)  # 페이지 로딩 대기

            # 2. 전체보기 버튼 클릭 (모든 주차 표시)
            self._update_status("전체 강의 목록 로딩 중...", "loading")
            try:
                all_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "btn_ALL"))
                )
                all_btn.click()
                time.sleep(2)
            except TimeoutException:
                logger.warning("전체보기 버튼을 찾을 수 없습니다.")

            # 3. 강의듣기/다시보기 버튼 모두 찾기
            lecture_buttons = driver.find_elements(
                By.CSS_SELECTOR, "button[onclick*='lectView']"
            )

            if not lecture_buttons:
                self._update_status("재생 가능한 강의를 찾을 수 없습니다.", "error")
                return

            # 미완료 강의만 필터링 (진도율 < 100%)
            incomplete_lectures = []
            for btn in lecture_buttons:
                try:
                    # 버튼 텍스트로 확인 (강의듣기 = 미완료, 다시보기 = 완료)
                    btn_text = btn.text.strip()
                    if "강의듣기" in btn_text:
                        onclick = btn.get_attribute("onclick")
                        incomplete_lectures.append(onclick)
                except Exception:
                    continue

            if not incomplete_lectures:
                self._update_status("미청취 강의가 없습니다!", "success")
                return

            # 4. 각 강의를 순차적으로 시청 (한 강의씩)
            total = len(incomplete_lectures)
            self._update_status(f"미청취 강의 {total}개 발견! 순차 시청 시작...", "loading")

            for i, onclick in enumerate(incomplete_lectures):
                try:
                    # 강의실 페이지로 이동
                    driver.get(self.config.LMS_URL)
                    time.sleep(2)

                    # 강의실로 이동
                    driver.execute_script(course.onclick_script)
                    time.sleep(2)

                    # 강의 재생 스크립트 실행
                    self._update_status(f"강의 {i+1}/{total} 열기 중...", "loading")
                    driver.execute_script(onclick)
                    time.sleep(5)  # 모달 로드 대기

                    # 이어듣기 모달 확인 및 "예" 클릭
                    self._handle_continue_modal(driver)
                    time.sleep(3)

                    # 비디오 자동 재생 시작
                    self._update_status(f"재생 버튼 대기 중... ({i+1}/{total})", "loading")
                    if not self._start_video_playback(driver):
                        self._update_status(f"재생 버튼 클릭 실패 ({i+1}/{total})", "error")
                        continue

                    self._update_status(f"강의 {i+1}/{total} 재생 중...", "loading")

                    # 강의 완료까지 대기 (출석 확인 포함)
                    self._wait_for_lecture_completion(driver, i + 1, total)

                    self._update_status(f"강의 {i+1}/{total} 완료!", "success")
                    time.sleep(2)

                except Exception as e:
                    logger.error(f"강의 {i+1} 시청 실패: {e}")
                    self._update_status(f"강의 {i+1} 오류: {str(e)}", "error")
                    continue

            self._update_status(f"모든 강의 완료! ({total}개)", "success")

        except Exception as e:
            logger.error(f"강의 열기 오류: {e}")
            self._update_status(f"오류: {str(e)}", "error")

    def _wait_for_lecture_completion(self, driver, current: int, total: int) -> None:
        """강의 완료까지 대기 (출석 확인 + 완료 확인 모달 자동 클릭)"""
        check_interval = 60  # 1분마다 체크
        attendance_clicked = False
        video_ended = False

        while True:
            try:
                # 1. 확인 모달 체크 및 클릭 (출석 확인 또는 완료 확인)
                modal_btn = self._find_attendance_modal_button(driver, timeout=2)
                if modal_btn:
                    modal_btn.click()
                    if not attendance_clicked:
                        logger.info(f"출석 확인 버튼 클릭됨 (강의 {current})")
                        self._update_status(f"출석 확인 완료! ({current}/{total})", "success")
                        attendance_clicked = True
                    else:
                        # 영상 종료 후 완료 확인 모달
                        logger.info(f"완료 확인 버튼 클릭됨 (강의 {current})")
                        self._update_status(f"강의 {current}/{total} 완료 확인!", "success")
                        time.sleep(1)
                        break  # 완료 확인 후 종료
                    time.sleep(1)
                    continue

                # 2. 영상 남은 시간 확인
                remaining = driver.execute_script("""
                    var video = document.querySelector('video');
                    if (video && video.duration && !isNaN(video.duration)) {
                        return video.duration - video.currentTime;
                    }
                    return -1;
                """)

                if remaining is not None and remaining >= 0:
                    remaining_min = int(remaining // 60)
                    remaining_sec = int(remaining % 60)

                    if remaining <= 5:
                        # 영상 종료됨 - 완료 확인 모달 대기
                        if not video_ended:
                            logger.info(f"강의 {current} 영상 종료, 완료 확인 대기...")
                            self._update_status(f"강의 {current}/{total} 종료, 완료 확인 대기...", "loading")
                            video_ended = True
                        time.sleep(3)  # 완료 모달이 뜰 때까지 짧게 대기
                        continue
                    else:
                        self._update_status(
                            f"강의 {current}/{total} 시청 중... 남은 시간: {remaining_min}분 {remaining_sec}초",
                            "loading"
                        )

                # 3. 다음 체크까지 대기
                time.sleep(check_interval)

            except Exception as e:
                logger.debug(f"강의 대기 중 오류: {e}")
                time.sleep(check_interval)

    def _start_attendance_monitor(self, tabs: list[str]) -> None:
        """출석 확인 모달 자동 클릭 모니터링 시작 (미사용 - 순차 시청으로 변경)"""
        self.attendance_monitor_active = True
        thread = threading.Thread(
            target=self._monitor_attendance_modal, args=(tabs,), daemon=True
        )
        thread.start()

    def _monitor_attendance_modal(self, tabs: list[str]) -> None:
        """출석 확인 모달 감지 및 자동 클릭 (백그라운드 스레드)"""
        driver = self.login_handler.driver
        check_interval = 60  # 1분마다 체크
        modal_timeout = 5  # 모달 찾기 타임아웃

        # 확인 버튼 클릭 완료된 탭
        confirmed_tabs = set()

        logger.info(f"출석 모달 모니터링 시작 ({len(tabs)}개 탭)")

        while getattr(self, "attendance_monitor_active", True) and tabs:
            try:
                # 각 탭을 순회하며 모달 확인
                active_tabs = []
                for tab_handle in tabs:
                    try:
                        # 탭이 아직 열려있는지 확인
                        if tab_handle not in driver.window_handles:
                            continue

                        active_tabs.append(tab_handle)

                        # 이미 확인된 탭은 스킵 (남은 시간 대기만)
                        if tab_handle in confirmed_tabs:
                            continue

                        driver.switch_to.window(tab_handle)

                        # 출석 확인 모달 찾기
                        modal_btn = self._find_attendance_modal_button(driver, modal_timeout)

                        if modal_btn:
                            modal_btn.click()
                            logger.info(f"출석 확인 버튼 클릭됨 (탭: {tab_handle[:10]}...)")
                            self._update_status("출석 확인 버튼 클릭!", "success")
                            confirmed_tabs.add(tab_handle)
                            time.sleep(1)

                    except Exception as e:
                        logger.debug(f"탭 {tab_handle[:10]} 처리 중 오류: {e}")
                        continue

                tabs = active_tabs

                # 모든 탭이 닫히면 종료
                if not tabs:
                    logger.info("모든 강의 탭이 닫힘. 모니터링 종료.")
                    self._update_status("모든 강의 완료!", "success")
                    break

                time.sleep(check_interval)

            except Exception as e:
                logger.error(f"모달 모니터링 오류: {e}")
                time.sleep(check_interval)

    def _handle_continue_modal(self, driver) -> bool:
        """이어듣기 모달 처리 - '예' 버튼 클릭"""
        try:
            # 이어듣기 모달의 "예" 버튼 찾기 (btn-light-blue 클래스)
            yes_btn = driver.execute_script("""
                var modal = document.querySelector('.modal-type-confirm');
                if (modal) {
                    var yesBtn = modal.querySelector('a.modal-btn.btn-light-blue');
                    if (yesBtn) {
                        yesBtn.click();
                        return true;
                    }
                }
                return false;
            """)
            if yes_btn:
                logger.info("이어듣기 모달 '예' 클릭")
                return True
        except Exception as e:
            logger.debug(f"이어듣기 모달 처리: {e}")
        return False

    def _start_video_playback(self, driver, max_attempts: int = 15) -> bool:
        """비디오 재생 시작 - Selenium 클릭 방식 (브라우저 자동재생 정책 우회)"""

        # 1. video 요소가 로드될 때까지 대기
        logger.info("비디오 요소 대기 중...")
        for i in range(max_attempts):
            video_ready = driver.execute_script("""
                var video = document.querySelector('video');
                return video && video.readyState >= 2;
            """)
            if video_ready:
                logger.info("비디오 준비 완료")
                break
            time.sleep(1)

        time.sleep(2)  # 추가 안정화

        # 2. 재생 버튼 클릭 시도 (Selenium 실제 클릭 = 사용자 상호작용)
        play_button_selectors = [
            ".plyr__control--overlaid",  # Plyr 큰 재생 버튼 (오버레이)
            "button[data-plyr='play']",  # Plyr 재생 버튼
            ".plyr__controls button[data-plyr='play']",  # 컨트롤바 재생 버튼
            ".vjs-big-play-button",  # Video.js 스타일
            ".play-button",  # 일반적인 재생 버튼
            "video",  # 비디오 요소 직접 클릭
        ]

        for attempt in range(5):
            for selector in play_button_selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if element and element.is_displayed():
                        element.click()
                        logger.info(f"재생 버튼 클릭 (선택자: {selector})")
                        time.sleep(1)

                        if self._check_video_playing(driver):
                            logger.info("비디오 재생 시작됨!")
                            return True
                except Exception:
                    continue

            # 모든 선택자 실패 시 잠시 대기 후 재시도
            time.sleep(1)

        return False

    def _check_video_playing(self, driver) -> bool:
        """비디오가 재생 중인지 확인"""
        try:
            return driver.execute_script("""
                var video = document.querySelector('video');
                return video && !video.paused && video.currentTime > 0;
            """)
        except Exception:
            return False

    def _find_attendance_modal_button(self, driver, timeout: int = 5):
        """출석 확인 모달의 확인 버튼 찾기"""
        try:
            # 모달 확인 버튼 선택자들
            selectors = [
                "a.modal-btn",  # BDU LMS 모달
                "#modal-window .modal-btn",
                ".modal-buttons .modal-btn",
                "button.modal-btn",
            ]

            for selector in selectors:
                try:
                    btn = WebDriverWait(driver, timeout).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    # 모달이 보이는지 확인
                    modal = driver.find_element(By.ID, "modal-window")
                    if modal and modal.is_displayed():
                        return btn
                except TimeoutException:
                    continue
                except Exception:
                    continue

        except Exception:
            pass

        return None

    def stop_attendance_monitor(self) -> None:
        """출석 모달 모니터링 중지"""
        self.attendance_monitor_active = False
        logger.info("출석 모달 모니터링 중지됨")

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
        self.stop_attendance_monitor()
        if self.browser:
            self.browser.quit()
        self.destroy()

    def run(self) -> None:
        """앱 실행"""
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.mainloop()
