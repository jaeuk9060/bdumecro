"""BDU LMS 트래커 - 진입점"""
import sys
import logging
from pathlib import Path


def setup_logging() -> None:
    """로깅 설정"""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> None:
    """메인 함수"""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("BDU LMS 트래커 시작")

        # src 디렉토리를 path에 추가 (exe 빌드 시 필요)
        src_path = Path(__file__).parent.parent
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        from src.app import BDUTrackerApp

        app = BDUTrackerApp()
        app.run()

    except Exception as e:
        logger.error(f"앱 실행 오류: {e}")
        raise


if __name__ == "__main__":
    main()
