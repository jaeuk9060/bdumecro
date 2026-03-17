"""대시보드 화면"""
import customtkinter as ctk
from typing import Callable

from src.parser.lms_parser import CourseInfo
from src.gui.components import CourseCard, LogViewer, StatusLabel
from src.utils.config import Config


class Dashboard(ctk.CTkFrame):
    """메인 대시보드"""

    def __init__(
        self,
        master,
        config: Config | None = None,
        on_login_click: Callable[[], None] | None = None,
        on_refresh_click: Callable[[], None] | None = None,
        on_go_lms_click: Callable[[], None] | None = None,
        on_course_click: Callable[[CourseInfo], None] | None = None,
        on_all_courses_click: Callable[[], None] | None = None,
        on_pause_click: Callable[[], None] | None = None,
        on_stop_click: Callable[[], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="#F5F5F5", **kwargs)

        self.config = config or Config()
        self.on_login_click = on_login_click
        self.on_refresh_click = on_refresh_click
        self.on_go_lms_click = on_go_lms_click
        self.on_course_click = on_course_click
        self.on_all_courses_click = on_all_courses_click
        self.on_pause_click = on_pause_click
        self.on_stop_click = on_stop_click
        self.course_cards: list[CourseCard] = []
        self._initial_remaining: dict[str, int] = {}  # 과목명 → 초기 미청취 수
        self._log_visible = False

        self._create_widgets()

    def _create_widgets(self) -> None:
        """위젯 생성"""
        # 헤더
        self._create_header()

        # 재생 컨트롤 바
        self._create_toolbar()

        # 컨텐츠 영역 (스크롤 가능)
        self._create_content()

        # 푸터 (상태 표시)
        self._create_footer()

    def _create_header(self) -> None:
        """헤더 생성"""
        header_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", height=60)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)

        # 타이틀
        title_label = ctk.CTkLabel(
            header_frame,
            text=self.config.APP_TITLE,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#333333",
        )
        title_label.pack(side="left", padx=20, pady=15)

        # 버튼 프레임 (우측 네비게이션)
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right", padx=20, pady=10)

        # 새로고침 버튼
        self.refresh_btn = ctk.CTkButton(
            btn_frame,
            text="새로고침",
            width=70,
            height=32,
            fg_color="#4CAF50",
            hover_color="#45A049",
            command=self._on_refresh,
        )
        self.refresh_btn.pack(side="right", padx=3)

        # 로그 토글 버튼
        self.log_btn = ctk.CTkButton(
            btn_frame,
            text="로그",
            width=50,
            height=32,
            fg_color="#607D8B",
            hover_color="#455A64",
            command=self._toggle_log,
        )
        self.log_btn.pack(side="right", padx=3)

        # 강의페이지로 가기 버튼
        self.go_lms_btn = ctk.CTkButton(
            btn_frame,
            text="강의페이지",
            width=80,
            height=32,
            fg_color="#FF9800",
            hover_color="#F57C00",
            command=self._on_go_lms,
        )
        self.go_lms_btn.pack(side="right", padx=3)

        # 포털 열기 버튼
        self.login_btn = ctk.CTkButton(
            btn_frame,
            text="포털열기",
            width=70,
            height=32,
            fg_color="#2196F3",
            hover_color="#1976D2",
            command=self._on_login,
        )
        self.login_btn.pack(side="right", padx=3)

    def _create_toolbar(self) -> None:
        """재생 컨트롤 툴바 생성"""
        toolbar = ctk.CTkFrame(self, fg_color="#F0F0F0", height=42)
        toolbar.pack(fill="x", padx=0, pady=0)
        toolbar.pack_propagate(False)

        ctrl_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        ctrl_frame.pack(side="left", padx=15, pady=5)

        # 재생 버튼
        self.play_btn = ctk.CTkButton(
            ctrl_frame,
            text="▶ 재생",
            width=70,
            height=30,
            fg_color="#4CAF50",
            hover_color="#388E3C",
            font=ctk.CTkFont(size=13),
            command=self._on_all_courses,
        )
        self.play_btn.pack(side="left", padx=2)

        # 일시정지 버튼
        self.pause_btn = ctk.CTkButton(
            ctrl_frame,
            text="⏸ 일시정지",
            width=85,
            height=30,
            fg_color="#FF9800",
            hover_color="#F57C00",
            font=ctk.CTkFont(size=13),
            state="disabled",
            command=self._on_pause,
        )
        self.pause_btn.pack(side="left", padx=2)

        # 중지 버튼
        self.stop_btn = ctk.CTkButton(
            ctrl_frame,
            text="■ 중지",
            width=65,
            height=30,
            fg_color="#F44336",
            hover_color="#D32F2F",
            font=ctk.CTkFont(size=13),
            state="disabled",
            command=self._on_stop,
        )
        self.stop_btn.pack(side="left", padx=2)

    def _create_content(self) -> None:
        """컨텐츠 영역 생성"""
        # 스크롤 가능한 프레임
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#F5F5F5",
            corner_radius=0,
        )
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 안내 메시지 (초기 상태)
        self.empty_label = ctk.CTkLabel(
            self.scrollable_frame,
            text="로그인 버튼을 클릭하여 LMS에 접속하세요.",
            font=ctk.CTkFont(size=14),
            text_color="#888888",
        )
        self.empty_label.pack(pady=50)

    def _create_footer(self) -> None:
        """푸터 생성"""
        self.footer_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", height=40)
        self.footer_frame.pack(fill="x", side="bottom")
        self.footer_frame.pack_propagate(False)

        self.status_label = StatusLabel(self.footer_frame)
        self.status_label.pack(side="left", padx=20, pady=10)

        # 로그 뷰어 (초기에는 숨김, 푸터 바로 위에 배치)
        self.log_viewer = LogViewer(self, height=150)

    def _toggle_log(self) -> None:
        """로그 패널 표시/숨기기"""
        if self._log_visible:
            self.log_viewer.pack_forget()
            self._log_visible = False
        else:
            self.log_viewer.pack(fill="x", side="bottom", before=self.footer_frame)
            self._log_visible = True

    def add_log(self, message: str, level: str = "INFO") -> None:
        """로그 메시지 추가 (외부에서 호출)"""
        self.log_viewer.add_log(message, level)

    def _on_login(self) -> None:
        """로그인 버튼 클릭"""
        if self.on_login_click:
            self.on_login_click()

    def _on_refresh(self) -> None:
        """새로고침 버튼 클릭"""
        if self.on_refresh_click:
            self.on_refresh_click()

    def _on_go_lms(self) -> None:
        """강의페이지 버튼 클릭"""
        if self.on_go_lms_click:
            self.on_go_lms_click()

    def _on_all_courses(self) -> None:
        """재생 버튼 클릭"""
        if self.on_all_courses_click:
            self.on_all_courses_click()

    def _on_pause(self) -> None:
        """일시정지 버튼 클릭"""
        if self.on_pause_click:
            self.on_pause_click()

    def _on_stop(self) -> None:
        """중지 버튼 클릭"""
        if self.on_stop_click:
            self.on_stop_click()

    def set_playback_state(self, state: str) -> None:
        """재생 컨트롤 상태 설정 (idle, playing, paused)"""
        if state == "playing":
            self.play_btn.configure(state="disabled")
            self.pause_btn.configure(state="normal", text="⏸ 일시정지")
            self.stop_btn.configure(state="normal")
        elif state == "paused":
            self.play_btn.configure(state="disabled")
            self.pause_btn.configure(state="normal", text="▶ 재개")
            self.stop_btn.configure(state="normal")
        else:  # idle
            self.play_btn.configure(state="normal")
            self.pause_btn.configure(state="disabled", text="⏸ 일시정지")
            self.stop_btn.configure(state="disabled")

    def set_status(self, text: str, status_type: str = "normal") -> None:
        """상태 표시 업데이트"""
        if status_type == "loading":
            self.status_label.set_loading()
            self.status_label.configure(text=text)
        elif status_type == "success":
            self.status_label.set_success(text)
        elif status_type == "error":
            self.status_label.set_error(text)
        elif status_type == "waiting":
            self.status_label.set_waiting(text)
        else:
            self.status_label.set_status(text)

    def display_courses(self, courses: list[CourseInfo]) -> None:
        """과목 목록 표시"""
        # 기존 카드 삭제
        for card in self.course_cards:
            card.destroy()
        self.course_cards.clear()

        # 안내 메시지 숨기기
        self.empty_label.pack_forget()

        if not courses:
            self.empty_label.configure(text="수강 중인 과목이 없습니다.")
            self.empty_label.pack(pady=50)
            return

        # 미청취가 0인 과목 제외 및 미청취 적은 순 정렬
        filtered_courses = [c for c in courses if c.remaining_lectures > 0]
        filtered_courses.sort(key=lambda c: c.remaining_lectures)

        if not filtered_courses:
            self.empty_label.configure(text="모든 강의를 완료했습니다! 🎉")
            self.empty_label.pack(pady=50)
            return

        # 과목 카드 생성
        for course in filtered_courses:
            # 첫 로드 시에만 초기 미청취 수 저장
            if course.name not in self._initial_remaining:
                self._initial_remaining[course.name] = course.remaining_lectures

            initial = self._initial_remaining[course.name]
            card = CourseCard(
                self.scrollable_frame,
                course,
                initial_remaining=initial,
                on_click=self.on_course_click,
            )
            card.pack(fill="x", padx=5, pady=5)
            self.course_cards.append(card)

        hidden_count = len(courses) - len(filtered_courses)
        if hidden_count > 0:
            self.set_status(f"{len(filtered_courses)}개 과목 표시 (완료 {hidden_count}개 숨김)", "success")
        else:
            self.set_status(f"{len(filtered_courses)}개 과목 로드 완료", "success")

    def clear_courses(self) -> None:
        """과목 목록 초기화"""
        for card in self.course_cards:
            card.destroy()
        self.course_cards.clear()
        self.empty_label.configure(text="로그인 버튼을 클릭하여 LMS에 접속하세요.")
        self.empty_label.pack(pady=50)

    def set_buttons_enabled(
        self, login: bool = True, refresh: bool = True, go_lms: bool = True
    ) -> None:
        """버튼 활성화/비활성화"""
        self.login_btn.configure(state="normal" if login else "disabled")
        self.refresh_btn.configure(state="normal" if refresh else "disabled")
        self.go_lms_btn.configure(state="normal" if go_lms else "disabled")
