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

SERVER_URL = os.environ.get("MD_SERVER_URL", "http://3.83.159.179:8080")

class MirrorDungeonOCR:
    def __init__(self):
        print("EasyOCR 초기화 중... (최초 1회 모델 다운로드)")
        self.reader = easyocr.Reader(['ko', 'en'], gpu=False)
        self.sct = mss.mss()
        self.current_screen_type = None
        self.game_window = None
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
        return {'name': gift_name.strip(), 'desc': gift_desc.strip()}

    def scan_shop(self, img, window_info):
        """상점 화면 스캔"""
        config = REGIONS['special_shop']
        gifts = []
        for name_region in config['gift_names']:
            name = self.ocr_region(img, name_region, window_info)
            if name.strip():
                gifts.append(name.strip())
        return gifts

    def scan(self):
        """메인 스캔 함수 - 화면 감지 후 적절한 스캔 수행"""
        img, window_info = self.capture_game_window()
        if img is None:
            return {'error': '게임 창을 찾을 수 없습니다'}

        screen_type = self.detect_screen_type(img, window_info)
        self.current_screen_type = screen_type

        result = {'screen_type': screen_type}
        gift_texts = []

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
            gift_texts = [g for g in shop_gifts if g]
        else:
            result['message'] = '인식 가능한 화면이 아닙니다'

        # 화면 종류와 무관하게 매칭에 사용할 통일 필드
        result['gift_texts'] = gift_texts
        result['texts'] = gift_texts
        return result

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
