"""LMS HTML 파싱 모듈"""
import json
import re
from dataclasses import dataclass
from bs4 import BeautifulSoup


@dataclass
class CourseInfo:
    """수강 과목 정보"""

    name: str  # 과목명
    progress: float  # 진도율 (0.0 ~ 100.0)
    total_lectures: int  # 전체 강의 수
    completed_lectures: int  # 완료한 강의 수
    remaining_lectures: int  # 남은 강의 수
    onclick_script: str = ""  # 강의실 이동 onclick 스크립트
    current_week: int = 0  # 현재 주차 (CURR_TIME_NO)
    current_week_lectures: int = 0  # 현재 주차 차시 수 (CH_TIME_DIST)

    @property
    def progress_text(self) -> str:
        """진도율 텍스트"""
        return f"{self.progress:.1f}%"

    @property
    def lecture_status(self) -> str:
        """강의 현황 텍스트"""
        return f"{self.completed_lectures}/{self.total_lectures}"


class LMSParser:
    """LMS 페이지 파서"""

    def __init__(self, html: str):
        self.soup = BeautifulSoup(html, "lxml")
        self.courses: list[CourseInfo] = []

    def parse(self, incomplete_only: bool = True) -> list[CourseInfo]:
        """HTML에서 수강 과목 정보 추출

        Args:
            incomplete_only: True면 미완료 강의만 반환 (진도율 < 100%)
        """
        self.courses = []

        # 방법 1: onclick 속성에서 JSON 추출
        self._parse_onclick_json()

        # 방법 2: 테이블/리스트에서 직접 추출 (onclick이 없는 경우)
        if not self.courses:
            self._parse_course_elements()

        # 미완료 강의만 필터링
        if incomplete_only:
            self.courses = [c for c in self.courses if c.progress < 100]

        # "(일반)" 강의 제외 (분반만 표시)
        self.courses = [c for c in self.courses if "(일반)" not in c.name]

        return self.courses

    def _parse_onclick_json(self) -> None:
        """onclick 속성에서 JSON 데이터 추출 (중복 제거)"""
        seen_courses: dict[str, CourseInfo] = {}  # 강의명 기준 중복 방지

        # active 상태인 card-list 내의 카드만 선택 (Grid/List 뷰 중복 방지)
        card_containers = self.soup.select("div.card-list.active")
        if card_containers:
            elements = []
            for container in card_containers:
                elements.extend(container.find_all(onclick=True))
        else:
            # fallback: 기존 방식
            elements = self.soup.find_all(onclick=True)

        for element in elements:
            onclick = element.get("onclick", "")
            json_data = self._extract_json_from_onclick(onclick)

            if json_data:
                course = self._json_to_course(json_data, onclick)
                if course and course.name not in seen_courses:
                    seen_courses[course.name] = course

        self.courses = list(seen_courses.values())

    def _extract_json_from_onclick(self, onclick: str) -> dict | None:
        """onclick 문자열에서 JSON 객체 추출"""
        # JSON 객체 패턴 찾기: {...}
        json_pattern = r"\{[^{}]*\}"
        matches = re.findall(json_pattern, onclick)

        for match in matches:
            try:
                # 작은따옴표를 큰따옴표로 변환
                json_str = match.replace("'", '"')
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue

        return None

    def _json_to_course(self, data: dict, onclick: str = "") -> CourseInfo | None:
        """JSON 데이터를 CourseInfo로 변환"""
        try:
            # BDU LMS 필드명
            name = data.get("LEC_NM", "")
            progress = float(data.get("TOT_PROGRESS") or 0)
            total = int(data.get("TOT_TIME_DIST") or 0)
            completed = int(data.get("ATND_TIME_DIST") or 0)
            # ATND_NOT_CNT: 실제 미청취 강의 수 (직접 사용)
            remaining = int(data.get("ATND_NOT_CNT") or 0)
            # 주차 정보
            current_week = int(data.get("CURR_TIME_NO") or 0)
            current_week_lectures = int(data.get("CH_TIME_DIST") or 0)

            if name:
                return CourseInfo(
                    name=name,
                    progress=progress,
                    total_lectures=total,
                    completed_lectures=completed,
                    remaining_lectures=remaining,
                    onclick_script=onclick,
                    current_week=current_week,
                    current_week_lectures=current_week_lectures,
                )
        except (ValueError, TypeError):
            pass

        return None

    def _parse_course_elements(self) -> None:
        """HTML 요소에서 직접 과목 정보 추출"""
        # 과목 카드/행 요소 찾기 (일반적인 클래스명)
        course_selectors = [
            ".course-item",
            ".subject-item",
            ".lecture-item",
            "tr.course",
            "[data-course]",
        ]

        for selector in course_selectors:
            elements = self.soup.select(selector)
            for element in elements:
                course = self._element_to_course(element)
                if course:
                    self.courses.append(course)

            if self.courses:
                break

    def _element_to_course(self, element) -> CourseInfo | None:
        """HTML 요소를 CourseInfo로 변환"""
        try:
            # 과목명 찾기
            name_elem = element.select_one(".course-name, .subject-name, .title")
            name = name_elem.get_text(strip=True) if name_elem else ""

            # 진도율 찾기
            progress_elem = element.select_one(".progress, .rate, .percent")
            progress_text = progress_elem.get_text(strip=True) if progress_elem else "0"
            progress = float(re.sub(r"[^0-9.]", "", progress_text) or 0)

            # 강의 수 찾기
            total = 0
            completed = 0
            count_elem = element.select_one(".count, .lecture-count")
            if count_elem:
                count_text = count_elem.get_text(strip=True)
                count_match = re.search(r"(\d+)\s*/\s*(\d+)", count_text)
                if count_match:
                    completed = int(count_match.group(1))
                    total = int(count_match.group(2))

            if name:
                return CourseInfo(
                    name=name,
                    progress=progress,
                    total_lectures=total,
                    completed_lectures=completed,
                    remaining_lectures=max(0, total - completed),
                )
        except (ValueError, TypeError):
            pass

        return None

    def get_courses(self) -> list[CourseInfo]:
        """파싱된 과목 목록 반환"""
        return self.courses
