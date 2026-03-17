"""재사용 가능한 UI 컴포넌트"""
import customtkinter as ctk
from datetime import datetime
from typing import Callable

from src.parser.lms_parser import CourseInfo


class LogViewer(ctk.CTkFrame):
    """실시간 로그 뷰어 컴포넌트"""

    # 로그 레벨별 색상
    LEVEL_COLORS = {
        "INFO": "#333333",
        "WARNING": "#FF9800",
        "ERROR": "#F44336",
        "DEBUG": "#9E9E9E",
        "CRITICAL": "#D32F2F",
    }

    def __init__(self, master, height: int = 200, **kwargs):
        super().__init__(master, fg_color="#FFFFFF", **kwargs)

        self._create_widgets(height)

    def _create_widgets(self, height: int) -> None:
        """위젯 생성"""
        # 헤더 (타이틀 + 지우기 버튼)
        header = ctk.CTkFrame(self, fg_color="transparent", height=30)
        header.pack(fill="x", padx=10, pady=(5, 0))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="로그",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#333333",
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="지우기",
            width=50,
            height=24,
            fg_color="#F1F3F4",
            hover_color="#E8EAED",
            text_color="#5F6368",
            font=ctk.CTkFont(size=11),
            corner_radius=4,
            command=self.clear,
        ).pack(side="right")

        # 로그 텍스트 영역
        self.textbox = ctk.CTkTextbox(
            self,
            height=height,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#FAFAFA",
            text_color="#333333",
            corner_radius=6,
            state="disabled",
            wrap="word",
        )
        self.textbox.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # 태그 색상 설정
        for level, color in self.LEVEL_COLORS.items():
            self.textbox._textbox.tag_configure(level, foreground=color)

    def add_log(self, message: str, level: str = "INFO") -> None:
        """로그 메시지 추가"""
        self.textbox.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] [{level}] {message}\n"
        self.textbox._textbox.insert("end", line, level)
        self.textbox._textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self) -> None:
        """로그 지우기"""
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")


class ProgressBar(ctk.CTkFrame):
    """진행률 바 컴포넌트"""

    def __init__(
        self,
        master,
        progress: float = 0,
        height: int = 20,
        **kwargs,
    ):
        super().__init__(master, height=height, **kwargs)

        self.progress_bar = ctk.CTkProgressBar(
            self,
            height=height,
            progress_color="#4CAF50",
            fg_color="#E0E0E0",
        )
        self.progress_bar.pack(fill="x", expand=True)
        self.set_progress(progress)

    def set_progress(self, value: float) -> None:
        """진행률 설정 (0-100)"""
        self.progress_bar.set(value / 100)


class CourseCard(ctk.CTkFrame):
    """과목 카드 컴포넌트"""

    def __init__(
        self,
        master,
        course: CourseInfo,
        initial_remaining: int = 0,
        on_click: Callable[["CourseInfo"], None] | None = None,
        **kwargs,
    ):
        super().__init__(
            master,
            corner_radius=10,
            fg_color="#FFFFFF",
            border_width=1,
            border_color="#E0E0E0",
            **kwargs,
        )

        self.course = course
        self.initial_remaining = initial_remaining if initial_remaining > 0 else course.remaining_lectures
        self.on_click = on_click
        self._create_widgets()
        self._bind_click_events()

    def _create_widgets(self) -> None:
        """위젯 생성"""
        # 미청취 진행 상황 계산
        completed_count = self.initial_remaining - self.course.remaining_lectures
        if self.initial_remaining > 0:
            progress_percent = (completed_count / self.initial_remaining) * 100
        else:
            progress_percent = 100.0  # 미청취가 없으면 100%

        # 과목명
        self.name_label = ctk.CTkLabel(
            self,
            text=self.course.name,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#333333",
            anchor="w",
        )
        self.name_label.pack(fill="x", padx=15, pady=(15, 5))

        # 진행률 프레임
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.pack(fill="x", padx=15, pady=5)

        # 진행률 텍스트 (미청취 기준)
        progress_label = ctk.CTkLabel(
            progress_frame,
            text=f"진도율: {progress_percent:.1f}%",
            font=ctk.CTkFont(size=13),
            text_color="#666666",
        )
        progress_label.pack(side="left")

        # 미청취 현황 텍스트 (완료한 미청취/초기 미청취)
        status_label = ctk.CTkLabel(
            progress_frame,
            text=f"({completed_count}/{self.initial_remaining})",
            font=ctk.CTkFont(size=12),
            text_color="#888888",
        )
        status_label.pack(side="right")

        # 진행률 바 (미청취 기준)
        self.progress_bar = ProgressBar(
            self,
            progress=progress_percent,
            height=12,
            fg_color="transparent",
        )
        self.progress_bar.pack(fill="x", padx=15, pady=(5, 10))

        # 미청취 강의 정보
        remaining_label = ctk.CTkLabel(
            self,
            text=f"미청취: {self.course.remaining_lectures}개",
            font=ctk.CTkFont(size=12),
            text_color="#FF6B6B" if self.course.remaining_lectures > 0 else "#4CAF50",
            anchor="w",
        )
        remaining_label.pack(fill="x", padx=15, pady=(0, 15))

    def _bind_click_events(self) -> None:
        """카드 클릭 이벤트 바인딩"""
        self.bind("<Button-1>", self._on_card_click)
        self.configure(cursor="hand2")

        # 모든 자식 위젯에도 클릭 이벤트 바인딩
        for widget in self.winfo_children():
            widget.bind("<Button-1>", self._on_card_click)
            try:
                widget.configure(cursor="hand2")
            except Exception:
                pass
            # 손자 위젯도 바인딩
            for child in widget.winfo_children():
                child.bind("<Button-1>", self._on_card_click)
                try:
                    child.configure(cursor="hand2")
                except Exception:
                    pass

    def _on_card_click(self, event=None) -> None:
        """카드 클릭 핸들러"""
        if self.on_click:
            self.on_click(self.course)

    def update_course(self, course: CourseInfo) -> None:
        """과목 정보 업데이트"""
        self.course = course
        self.name_label.configure(text=course.name)
        self.progress_bar.set_progress(course.progress)


class StatusLabel(ctk.CTkLabel):
    """상태 표시 레이블"""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            text="준비",
            font=ctk.CTkFont(size=12),
            text_color="#666666",
            **kwargs,
        )

    def set_status(self, text: str, color: str = "#666666") -> None:
        """상태 텍스트 및 색상 설정"""
        self.configure(text=text, text_color=color)

    def set_loading(self) -> None:
        """로딩 상태"""
        self.set_status("로딩 중...", "#2196F3")

    def set_success(self, message: str = "완료") -> None:
        """성공 상태"""
        self.set_status(message, "#4CAF50")

    def set_error(self, message: str = "오류") -> None:
        """오류 상태"""
        self.set_status(message, "#F44336")

    def set_waiting(self, message: str = "대기 중") -> None:
        """대기 상태"""
        self.set_status(message, "#FF9800")


class CourseConfirmModal(ctk.CTkToplevel):
    """강의 수강 확인 모달창"""

    def __init__(
        self,
        master,
        course: CourseInfo,
        on_confirm: Callable[[], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
    ):
        super().__init__(master)

        self.course = course
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.result = False

        self._setup_window()
        self._create_widgets()

        # 모달 동작 설정
        self.transient(master)
        self.grab_set()
        self.focus_set()

    def _setup_window(self) -> None:
        """윈도우 설정"""
        self.title("강의 수강")
        self.geometry("420x340")
        self.resizable(False, False)
        self.configure(fg_color="#FFFFFF")

        # 윈도우 중앙 배치
        self.update_idletasks()
        x = self.master.winfo_x() + (self.master.winfo_width() - 420) // 2
        y = self.master.winfo_y() + (self.master.winfo_height() - 340) // 2
        self.geometry(f"420x340+{x}+{y}")

        # 닫기 버튼 동작
        self.protocol("WM_DELETE_WINDOW", self._on_cancel_click)

    def _create_widgets(self) -> None:
        """위젯 생성"""
        # ========== 상단 헤더 영역 ==========
        header_frame = ctk.CTkFrame(self, fg_color="#F8F9FA", corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)

        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="x", padx=20, pady=20)

        # 아이콘
        icon_frame = ctk.CTkFrame(
            header_content,
            width=50,
            height=50,
            fg_color="#E3F2FD",
            corner_radius=10,
        )
        icon_frame.pack(side="left")
        icon_frame.pack_propagate(False)

        icon_label = ctk.CTkLabel(
            icon_frame,
            text="🎧",
            font=ctk.CTkFont(size=24),
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # 과목 정보
        info_container = ctk.CTkFrame(header_content, fg_color="transparent")
        info_container.pack(side="left", padx=(15, 0), fill="y")

        course_name_label = ctk.CTkLabel(
            info_container,
            text=self.course.name,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1A1A2E",
            anchor="w",
        )
        course_name_label.pack(anchor="w")

        week_text = f"{self.course.current_week}주차 · {self.course.current_week_lectures}차시"
        week_label = ctk.CTkLabel(
            info_container,
            text=week_text,
            font=ctk.CTkFont(size=13),
            text_color="#6C757D",
            anchor="w",
        )
        week_label.pack(anchor="w", pady=(3, 0))

        # ========== 구분선 ==========
        separator = ctk.CTkFrame(self, height=1, fg_color="#E9ECEF")
        separator.pack(fill="x")

        # ========== 중앙 컨텐츠 영역 ==========
        content_frame = ctk.CTkFrame(self, fg_color="#FFFFFF")
        content_frame.pack(fill="both", expand=True, padx=25, pady=20)

        # 미청취 강의 라벨
        remaining_title = ctk.CTkLabel(
            content_frame,
            text="미청취 강의",
            font=ctk.CTkFont(size=13),
            text_color="#6C757D",
        )
        remaining_title.pack(pady=(10, 8))

        # 미청취 강의 수 강조 박스
        remaining_box = ctk.CTkFrame(
            content_frame,
            fg_color="#FFF5F5",
            corner_radius=12,
            border_width=1,
            border_color="#FFCDD2",
        )
        remaining_box.pack(fill="x", padx=20, pady=(0, 15))

        remaining_count = ctk.CTkLabel(
            remaining_box,
            text=f"{self.course.remaining_lectures}개",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#E53935",
        )
        remaining_count.pack(pady=15)

        # 질문 텍스트
        question_label = ctk.CTkLabel(
            content_frame,
            text="남은 강의를 모두 청취하시겠습니까?",
            font=ctk.CTkFont(size=14),
            text_color="#495057",
        )
        question_label.pack(pady=(5, 10))

        # ========== 하단 버튼 영역 ==========
        btn_separator = ctk.CTkFrame(self, height=1, fg_color="#E9ECEF")
        btn_separator.pack(fill="x")

        btn_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", height=70)
        btn_frame.pack(fill="x", side="bottom")
        btn_frame.pack_propagate(False)

        btn_container = ctk.CTkFrame(btn_frame, fg_color="transparent")
        btn_container.pack(expand=True)

        # 취소 버튼
        cancel_btn = ctk.CTkButton(
            btn_container,
            text="취소",
            width=140,
            height=42,
            fg_color="#F1F3F4",
            hover_color="#E8EAED",
            text_color="#5F6368",
            font=ctk.CTkFont(size=14),
            corner_radius=8,
            command=self._on_cancel_click,
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        # 확인 버튼
        confirm_btn = ctk.CTkButton(
            btn_container,
            text="확인",
            width=140,
            height=42,
            fg_color="#1A73E8",
            hover_color="#1557B0",
            font=ctk.CTkFont(size=14, weight="bold"),
            corner_radius=8,
            command=self._on_confirm_click,
        )
        confirm_btn.pack(side="left", padx=(10, 0))

    def _on_confirm_click(self) -> None:
        """확인 버튼 클릭 - 강의 청취 시작"""
        self.result = True
        self.destroy()
        if self.on_confirm:
            self.on_confirm()

    def _on_cancel_click(self) -> None:
        """취소 버튼 클릭 - LMS 페이지로 이동"""
        self.result = False
        if self.on_cancel:
            self.on_cancel()
        self.destroy()
