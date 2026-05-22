"""
Mirror Dungeon OCR Client - 화면 영역 설정
스크린샷 분석 기반 OCR 영역 정의 (비율 기반, 해상도 무관)
"""

# 화면 영역 정의 (비율: left%, top%, width%, height%)
# 게임 창 기준 상대 좌표

REGIONS = {
    # 이벤트 선택지 화면
    'event_choices': {
        'title': '선택지',
        'detect_keyword': '선택지',  # 이 텍스트가 보이면 이벤트 화면
        'choices': [
            # 선택지 1: 제목 + 설명
            {'name': (0.55, 0.18, 0.40, 0.06), 'desc': (0.55, 0.24, 0.40, 0.06)},
            # 선택지 2: 제목 + 설명
            {'name': (0.55, 0.38, 0.40, 0.06), 'desc': (0.55, 0.44, 0.40, 0.06)},
            # 선택지 3: 제목 + 설명
            {'name': (0.55, 0.58, 0.40, 0.06), 'desc': (0.55, 0.64, 0.40, 0.06)},
        ]
    },

    # 보유 E.G.O 기프트 화면
    'owned_gifts': {
        'title': '보유 E.G.O 기프트',
        'detect_keyword': '보유 E.G.O',  # 이 텍스트가 보이면 보유 화면
        'gift_name': (0.18, 0.14, 0.25, 0.06),  # 주황 배경 기프트 이름 영역
        'gift_desc': (0.05, 0.30, 0.40, 0.30),  # 기프트 설명 영역
    },

    # 특별한 상점 화면
    'special_shop': {
        'title': '특별한 상점',
        'detect_keyword': '특별한 상점',  # 이 텍스트가 보이면 상점 화면
        # 하단 구매 가능 기프트 이름들 (4개 슬롯)
        'gift_names': [
            (0.33, 0.78, 0.12, 0.04),  # 1번 기프트 이름
            (0.47, 0.78, 0.12, 0.04),  # 2번 기프트 이름
            (0.61, 0.78, 0.12, 0.04),  # 3번 기프트 이름
            (0.75, 0.78, 0.12, 0.04),  # 4번 기프트 이름
        ],
        # 가격 영역
        'prices': [
            (0.35, 0.74, 0.08, 0.03),
            (0.49, 0.74, 0.08, 0.03),
            (0.63, 0.74, 0.08, 0.03),
            (0.77, 0.74, 0.08, 0.03),
        ],
        # 상단 구매완료 기프트 이름들 (4개 슬롯)
        'purchased_names': [
            (0.33, 0.55, 0.12, 0.04),
            (0.47, 0.55, 0.12, 0.04),
            (0.61, 0.55, 0.12, 0.04),
            (0.75, 0.55, 0.12, 0.04),
        ]
    },

    # 일반 상점 (구조 유사, 기프트 수 적음)
    'normal_shop': {
        'title': '상점',
        'detect_keyword': '상점',
        'gift_names': [
            (0.35, 0.78, 0.12, 0.04),
            (0.50, 0.78, 0.12, 0.04),
            (0.65, 0.78, 0.12, 0.04),
        ]
    }
}

def get_pixel_region(ratio_region, window_width, window_height):
    """비율 기반 영역을 픽셀 좌표로 변환"""
    left_pct, top_pct, width_pct, height_pct = ratio_region
    return (
        int(window_width * left_pct),
        int(window_height * top_pct),
        int(window_width * width_pct),
        int(window_height * height_pct)
    )

def get_all_regions_for_screen(screen_type, window_width, window_height):
    """특정 화면 타입의 모든 OCR 영역을 픽셀 좌표로 반환"""
    config = REGIONS.get(screen_type)
    if not config:
        return {}

    result = {}
    if screen_type == 'event_choices':
        result['choices'] = []
        for choice in config['choices']:
            result['choices'].append({
                'name': get_pixel_region(choice['name'], window_width, window_height),
                'desc': get_pixel_region(choice['desc'], window_width, window_height),
            })
    elif screen_type == 'owned_gifts':
        result['gift_name'] = get_pixel_region(config['gift_name'], window_width, window_height)
        result['gift_desc'] = get_pixel_region(config['gift_desc'], window_width, window_height)
    elif screen_type in ('special_shop', 'normal_shop'):
        result['gift_names'] = [
            get_pixel_region(r, window_width, window_height) for r in config['gift_names']
        ]
        if 'prices' in config:
            result['prices'] = [
                get_pixel_region(r, window_width, window_height) for r in config['prices']
            ]

    return result
