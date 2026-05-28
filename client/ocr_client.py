"""
Mirror Dungeon OCR Client - 업데이트 버전
화면 자동 감지 + 영역별 OCR
"""
import os
import mss
import cv2
import numpy as np
import requests
import easyocr
import win32gui
import win32con
from screen_regions import REGIONS, get_pixel_region, get_all_regions_for_screen

SERVER_URL = os.environ.get("MD_SERVER_URL", "http://54.175.210.238:8080")
ICON_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "egogift_icons")
ICON_MATCH_THRESHOLD = 0.72
RUN_RESULT_KEYWORDS = {
    "클리어": [
        "거울던전 클리어", "거울 던전 클리어", "탐사 완료", "던전 완료",
        "거울던전 완료", "정산", "보상 획득", "CLEAR", "Clear", "clear",
    ],
    "전복": [
        "거울던전 실패", "거울 던전 실패", "탐사 실패", "전복", "전멸",
        "패배", "DEFEAT", "Defeat", "defeat", "FAILED", "Failed", "도전 실패",
    ],
}
RUN_RESULT_CONTEXT_KEYWORDS = [
    "거울던전", "거울 던전", "Mirror Dungeon", "mirror dungeon",
    "탐사", "정산", "보상", "코스트", "별빛", "시즌",
]

class MirrorDungeonOCR:
    def __init__(self):
        print("EasyOCR 초기화 중... (최초 1회 모델 다운로드)")
        self.reader = easyocr.Reader(['ko', 'en'], gpu=False)
        self.sct = mss.mss()
        self.current_screen_type = None
        self.game_window = None
        self.icon_matcher = GiftIconMatcher(ICON_DIR)
        print("OCR 준비 완료!")

    def find_game_window(self):
        """림버스컴퍼니 게임 창 찾기"""
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if 'LimbusCompany' in title or 'Limbus' in title:
                    windows.append(hwnd)
            return True

        windows = []
        win32gui.EnumWindows(callback, windows)

        if windows:
            self.game_window = windows[0]
            rect = win32gui.GetWindowRect(self.game_window)
            return {
                'left': rect[0], 'top': rect[1],
                'width': rect[2] - rect[0], 'height': rect[3] - rect[1]
            }
        return None

    def capture_game_window(self):
        """게임 창만 캡처"""
        window_info = self.find_game_window()
        if not window_info:
            print("게임 창을 찾을 수 없습니다.")
            return None, None

        monitor = {
            "top": window_info['top'],
            "left": window_info['left'],
            "width": window_info['width'],
            "height": window_info['height']
        }
        screenshot = self.sct.grab(monitor)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img, window_info

    def crop_region(self, img, region, window_info):
        """이미지에서 특정 영역 크롭 (비율 기반)"""
        w, h = window_info['width'], window_info['height']
        left, top, width, height = get_pixel_region(region, w, h)
        cropped = img[top:top+height, left:left+width]
        return cropped

    def preprocess_for_ocr(self, img):
        """OCR 전처리"""
        # 크기 확대 (작은 텍스트 인식률 향상)
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        # 그레이스케일
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 대비 향상
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        return enhanced

    def ocr_region(self, img, region, window_info):
        """특정 영역의 텍스트 인식"""
        cropped = self.crop_region(img, region, window_info)
        if cropped.size == 0:
            return ""
        processed = self.preprocess_for_ocr(cropped)
        results = self.reader.readtext(processed)
        texts = [text for (_, text, conf) in results if conf > 0.4]
        return ' '.join(texts)

    def detect_screen_type(self, img, window_info):
        """현재 화면 타입 자동 감지"""
        # 화면 상단 영역에서 키워드 검색
        header_region = (0.0, 0.0, 1.0, 0.15)
        header_text = self.ocr_region(img, header_region, window_info)

        for screen_type, config in REGIONS.items():
            keyword = config.get('detect_keyword', '')
            if keyword and keyword in header_text:
                return screen_type

        # 우측 상단도 체크 (선택지는 우측에 있음)
        right_header = (0.50, 0.05, 0.45, 0.12)
        right_text = self.ocr_region(img, right_header, window_info)
        for screen_type, config in REGIONS.items():
            keyword = config.get('detect_keyword', '')
            if keyword and keyword in right_text:
                return screen_type

        return None

    def detect_run_result(self, img, window_info):
        """클리어/전복 결과 화면을 넓은 영역 OCR로 감지."""
        regions = [
            (0.05, 0.05, 0.90, 0.25),
            (0.10, 0.25, 0.80, 0.35),
            (0.10, 0.60, 0.80, 0.25),
        ]
        text_parts = []
        for region in regions:
            text = self.ocr_region(img, region, window_info)
            if text:
                text_parts.append(text)
        combined = " ".join(text_parts)
        compact = combined.replace(" ", "").lower()
        has_md_context = any(
            keyword.replace(" ", "").lower() in compact
            for keyword in RUN_RESULT_CONTEXT_KEYWORDS
        )
        for result, keywords in RUN_RESULT_KEYWORDS.items():
            for keyword in keywords:
                normalized_keyword = keyword.replace(" ", "").lower()
                if normalized_keyword in compact and (has_md_context or "거울" in normalized_keyword):
                    return {
                        "result": result,
                        "cause": "OCR result screen",
                        "text": combined[:500],
                    }
        return None

    def scan_event_choices(self, img, window_info):
        """이벤트 선택지 화면 스캔"""
        config = REGIONS['event_choices']
        choices = []
        for choice_region in config['choices']:
            name = self.ocr_region(img, choice_region['name'], window_info)
            desc = self.ocr_region(img, choice_region['desc'], window_info)
            if name.strip():
                choices.append({'name': name.strip(), 'desc': desc.strip()})
        return choices

    def scan_owned_gifts(self, img, window_info):
        """보유 기프트 화면 스캔 (현재 선택된 기프트 이름)"""
        config = REGIONS['owned_gifts']
        gift_name = self.ocr_region(img, config['gift_name'], window_info)
        gift_desc = self.ocr_region(img, config['gift_desc'], window_info)
        gift_icon = None
        if not gift_name.strip():
            gift_icon = self.icon_match_region(img, config.get('gift_icon'), window_info)
        return {'name': gift_name.strip(), 'desc': gift_desc.strip(), 'icon_match': gift_icon}

    def scan_shop(self, img, window_info):
        """상점 화면 스캔"""
        config = REGIONS.get(self.current_screen_type) or REGIONS['special_shop']
        gifts = []
        icon_regions = config.get('gift_icons') or []
        for idx, name_region in enumerate(config['gift_names']):
            name = self.ocr_region(img, name_region, window_info)
            icon_match = None
            if not name.strip():
                icon_match = self.icon_match_region(
                    img,
                    icon_regions[idx] if idx < len(icon_regions) else None,
                    window_info,
                )
            if name.strip() or icon_match:
                gifts.append({'name': name.strip(), 'icon_match': icon_match})
        return gifts

    def icon_match_region(self, img, region, window_info):
        if not region:
            return None
        cropped = self.crop_region(img, region, window_info)
        return self.icon_matcher.match(cropped)

    def scan(self):
        """메인 스캔 함수 - 화면 감지 후 적절한 스캔 수행"""
        img, window_info = self.capture_game_window()
        if img is None:
            return {'error': '게임 창을 찾을 수 없습니다'}

        screen_type = self.detect_screen_type(img, window_info)
        self.current_screen_type = screen_type

        result = {'screen_type': screen_type}
        gift_texts = []
        run_result = self.detect_run_result(img, window_info)
        if run_result:
            result['run_result'] = run_result

        if screen_type == 'event_choices':
            choices = self.scan_event_choices(img, window_info)
            result['choices'] = choices
            gift_texts = [c['name'] for c in choices if c.get('name')]
        elif screen_type == 'owned_gifts':
            gift = self.scan_owned_gifts(img, window_info)
            result['gift'] = gift
            if gift.get('name'):
                gift_texts = [gift['name']]
        elif screen_type in ('special_shop', 'normal_shop'):
            shop_gifts = self.scan_shop(img, window_info)
            result['shop_gifts'] = shop_gifts
            gift_texts = [g['name'] for g in shop_gifts if g.get('name')]
        else:
            result['message'] = '인식 가능한 화면이 아닙니다'

        # 화면 종류와 무관하게 매칭에 사용할 통일 필드
        result['gift_texts'] = gift_texts
        result['texts'] = gift_texts
        result['icon_matches'] = self.collect_icon_matches(result)
        return result

    def collect_icon_matches(self, result):
        matches = []
        gift = result.get('gift') or {}
        if gift.get('icon_match'):
            matches.append(gift['icon_match'])
        for gift in result.get('shop_gifts') or []:
            if isinstance(gift, dict) and gift.get('icon_match'):
                matches.append(gift['icon_match'])
        return matches

    def match_gift_name(self, ocr_text):
        """OCR 결과를 DB의 기프트 이름과 매칭"""
        try:
            r = requests.get(f"{SERVER_URL}/gifts", params={'search': ocr_text}, timeout=3)
            if r.status_code == 200:
                gifts = r.json()
                if gifts:
                    return gifts[0]  # 가장 유사한 결과
        except:
            pass
        return None


class GiftIconMatcher:
    """Template-based E.G.O gift icon matcher.

    It is intentionally used as a fallback/boost for OCR, because OCR handles
    new gifts better while icon matching is stronger when the icon DB is complete.
    """

    def __init__(self, icon_dir):
        self.icon_dir = icon_dir
        self.templates = []
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        self._loaded = True
        if not os.path.isdir(self.icon_dir):
            return
        for fname in os.listdir(self.icon_dir):
            if not fname.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            gift_id = os.path.splitext(fname)[0].split("_")[0]
            if not gift_id.isdigit():
                continue
            path = os.path.join(self.icon_dir, fname)
            img = cv2.imread(path, cv2.IMREAD_COLOR)
            if img is None or img.size == 0:
                continue
            self.templates.append((int(gift_id), self.prepare(img)))

    def prepare(self, img):
        if img is None or img.size == 0:
            return None
        square = self.center_square(img)
        resized = cv2.resize(square, (64, 64), interpolation=cv2.INTER_AREA)
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        h_hist = cv2.calcHist([hsv], [0, 1], None, [24, 24], [0, 180, 0, 256])
        cv2.normalize(h_hist, h_hist, 0, 1, cv2.NORM_MINMAX)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        return {"hist": h_hist, "gray": gray}

    def center_square(self, img):
        h, w = img.shape[:2]
        side = min(h, w)
        y = max((h - side) // 2, 0)
        x = max((w - side) // 2, 0)
        return img[y:y + side, x:x + side]

    def match(self, crop):
        self.load()
        if not self.templates or crop is None or crop.size == 0:
            return None
        prepared = self.prepare(crop)
        if not prepared:
            return None

        best = None
        for gift_id, template in self.templates:
            hist_score = cv2.compareHist(prepared["hist"], template["hist"], cv2.HISTCMP_CORREL)
            edge_score = self.edge_similarity(prepared["gray"], template["gray"])
            score = (hist_score * 0.65) + (edge_score * 0.35)
            if best is None or score > best["confidence"]:
                best = {"gift_id": gift_id, "confidence": float(score)}

        if best and best["confidence"] >= ICON_MATCH_THRESHOLD:
            return best
        return None

    def edge_similarity(self, a, b):
        a_edges = cv2.Canny(a, 80, 160)
        b_edges = cv2.Canny(b, 80, 160)
        result = cv2.matchTemplate(a_edges, b_edges, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        if np.isnan(max_val):
            return 0.0
        return float(max_val)


if __name__ == '__main__':
    ocr = MirrorDungeonOCR()
    print("\n=== Mirror Dungeon OCR 테스트 ===")
    print("게임 창을 찾는 중...")

    result = ocr.scan()
    if 'error' in result:
        print(f"에러: {result['error']}")
        print("게임을 실행한 후 다시 시도하세요.")
    else:
        print(f"감지된 화면: {result.get('screen_type', '알 수 없음')}")
        if result.get('choices'):
            print("선택지:")
            for c in result['choices']:
                print(f"  - {c['name']}: {c['desc']}")
        if result.get('gift'):
            print(f"보유 기프트: {result['gift']['name']}")
        if result.get('shop_gifts'):
            print(f"상점 기프트: {result['shop_gifts']}")
