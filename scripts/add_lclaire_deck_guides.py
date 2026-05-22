import os
import sqlite3


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mirror_dungeon.db")


DECKS = [
    {
        "name": "파열·호흡덱",
        "keywords": "파열, 호흡, 참격, 관통",
        "description": (
            "LClaire 파열·호흡덱 소개(260506 수정) 기반. "
            "홍원 군주 홍루와 흑수 인격 중심의 파열/호흡 듀얼 키워드 덱. "
            "시작 기프트: 프레스티지 카드 + 귀신 들린 신발 + 깨진 안경 / 파열 시작. "
            "덱 코드: H4sIAAAAAAAAChWMMQqAQAwEvyT2FmPiYYRDVBB8QdArrjyfb2x2dprRgjd3chGdHPpmbDN6ElIwJIlAtxmHoQ/3DuRLSMHmFotWfLSIVPmVNyLrEmcYPhFZWM1gAAAA"
        ),
        "identities": [
            ("홍원 군주 홍루", "홍루", 1, "참격 / 파열·호흡", "스킬교환 105. 생강꽃 편지, 결의, 마음을 닫는 붉은 천. 시즌 6 핵심 인격."),
            ("흑수-사 로쟈", "로쟈", 2, "참격·관통 / 파열·호흡", "스킬교환 114. 생강꽃 편지, 결의. 3스킬 가중치를 앞 순번에서 활용."),
            ("흑수-유 필두 히스클리프", "히스클리프", 3, "참격 / 화상·파열", "스킬교환 015. 생강꽃 편지, 결의, 숫돌, 가지, 선고, 혈염도. 절차탁춘에서 혈염도 추천."),
            ("흑수-오 필두 이상", "이상", 4, "참격 / 진동·파열", "스킬교환 015. 결의, 가지, 선고, 메스, 가위, 흑철마갑. 흑수덱 딜탱."),
            ("홍원 방랑무사 료슈", "료슈", 5, "관통 / 파열·호흡", "스킬교환 105. 가지, 대못, 축복. 관통 기프트 효율이 좋은 5번 편성."),
            ("가주 후보 이스마엘", "이스마엘", 6, "타격·참격 / 파열·호흡", "스킬교환 105. 가지, 선고, 화평, 가위, 시간 굴레, 동티, 절차탁마. 회피로 고층 합 보조."),
            ("흑수-사 그레고르", "그레고르", 7, "참격·관통 / 파열·호흡", "스킬교환 114. 결의. 흑수 깔맞춤 및 호흡 5인 편성용, 섕뫼 대체 가능."),
        ],
        "packs": [
            (1, "사랑할 수 없는", "서릿발 발자국", 1, "얼어붙은 아우성 + 귀신 들린 신발."),
            (2, "헬스치킨", "탱고 닭양념장, 날카로운 실과 바늘, 목이 뻑뻑 가슴살, 뜨거운 육즙 다리살, 오염된 실과 바늘", 2, "초반 안정 보강."),
            (3, "낙화", "생강꽃, 안경 그리고 전해진 편지, 만화경", 1, "생강꽃 가지 + 깨진 안경 + 해진 우산. H사 5인 만화경."),
            (4, "탄환이 찍은 마침표", "흑염 파이프, 톱니 파편, 묵시적 계약 갱신, 평등", 2, "4층 추천 팩."),
            (5, "바라볼 수 밖에 없는", "물 속의 달, 거울 속의 꽃", 1, "호흡/파열 인격 지원. 5~10층 핵심."),
            (5, "2호선", "굴레, 메트로놈", 2, "생존 지원."),
            (5, "심야청소", "그림자 삿갓, 이전칠자, 찰랑이는 연료통, 묘각", 1, "참격/파열 인격 지원. 이전칠자는 새겨넣어진 괴문자 + 괴문자 부적."),
            (5, "절차탁춘", "마음을 닫는 붉은 천, 혈염도, 절차탁마, 흑철마갑, 소흥주", 1, "흑수 인격 지원. 유히스 혈염도 우선."),
            (5, "LCB 정기검진 복각", "강화제 Mk.4, 시험 추출 : 초롱, 가시 전투화, 잔가지, 재점화 플러그", 2, "화상/파열 보조 선택지."),
            (5, "20번구의 기적 복각", "기쁜 봉제인형", 2, "슬픈 봉제인형 + 거대한 선물 보따리 + 털방울 모자. 피해량 증가 및 호흡 수급."),
            (11, "5호선", "애달픈 날숨, 깨어질 화포", 2, "화포는 취향 선택."),
            (12, "3호선", "부화하지 않은 불씨, 경멸의 시선의 경멸", 1, "부화하지 않은 불씨는 합성으로라도 확보."),
            (13, "후반 선택", "N사 신 구인회, 어느 도서관의 어떤 책 속으로, 개화하는 녹림, 3호선-종착역, 영겁의 굴레", 2, "13~15층 후보."),
        ],
        "goods": [
            ("프레스티지 카드", 1, "시작 기프트."),
            ("귀신 들린 신발", 1, "시작 기프트. 서릿발 발자국 재료."),
            ("깨진 안경", 1, "시작 기프트. 생강꽃, 안경 그리고 전해진 편지 재료."),
            ("생강꽃, 안경 그리고 전해진 편지", 1, "생강꽃 가지 + 깨진 안경 + 해진 우산. 핵심 편지 루트."),
            ("결의", 1, "참격 스킬 2개 이상 인격 지원. 사로쟈/사그렉 등 핵심."),
            ("물 속의 달", 1, "파열/호흡 전체 지원."),
            ("거울 속의 꽃", 1, "파열/호흡 전체 지원."),
            ("마음을 닫는 붉은 천", 1, "군루/절차탁춘 핵심."),
            ("혈염도", 1, "유히스 전용무기급 추천."),
            ("절차탁마", 2, "덕목 지 + 덕목 용 + 덕목 인."),
            ("흑철마갑", 2, "흑수 인격 지원."),
            ("기쁜 봉제인형", 2, "피해량 증가 및 호흡 수급."),
            ("부화하지 않은 불씨", 1, "12층 핵심. 합성으로라도 확보."),
        ],
    },
    {
        "name": "호흡·관통덱",
        "keywords": "호흡, 관통, 파열, 화상",
        "description": (
            "LClaire 호흡·관통덱 소개(260407 수정) 기반. "
            "전원 관통 중심, 7인 중 5인 회피로 고층 합 안정성이 높은 P 딸깍형 덱. "
            "시작 기프트: 프레스티지 카드 + 귀신 들린 신발 + 깨진 안경 / 호흡 시작. "
            "덱 코드: H4sIAAAAAAAAChWKQQqAMBDE3uQDeki3lK4o0vqIQTwq9PuuucwQgtCUKFjJwDOd3igDwc3WrZrBK+d0bOEaUUVNjZ2hA2sou8ihf3acY42T0gfKJUvJYAAAAA=="
        ),
        "identities": [
            ("홍원 방랑무사 료슈", "료슈", 1, "관통 / 파열·호흡", "스킬교환 105. 생강꽃 편지, 분홍빛 꽃잎다발. 고층 합 안정과 원호공격 추가딜."),
            ("흑수-사 로쟈", "로쟈", 2, "참격·관통 / 파열·호흡", "스킬교환 114. 생강꽃 편지, 결의, 분홍빛 꽃잎다발. 덱의 가중치 인격."),
            ("동부 섕크 협회 3과 돈키호테", "돈키호테", 3, "관통 / 화상·호흡", "스킬교환 006. 생강꽃 편지, 고탄성강 신발, 가지, 분홍빛 꽃잎다발, 워킹 베이스."),
            ("서부 섕크 협회 3과 뫼르소", "뫼르소", 4, "관통 / 파열·호흡", "스킬교환 105. 가지, 대못, 분홍빛 꽃잎다발. 3스킬 재사용으로 잡몹전 강점."),
            ("마침표 사무소 해결사 히스클리프", "히스클리프", 5, "관통 / 호흡", "스킬교환 105. 가지, 대못, 분홍빛 꽃잎다발, 애달픈 날숨. 5호선 호흡 4티어 효율."),
            ("마침표 사무소 대표 홍루", "홍루", 6, "관통 / 호흡", "스킬교환 015. 가지, 분홍빛 꽃잎다발, 로열 젤리 퍼퓸. 탕히스 발사대."),
            ("남부 섕크 협회 4과 부장 싱클레어", "싱클레어", 7, "관통 / 호흡", "스킬교환 015. 분홍빛 꽃잎다발. 고층 불리한 합을 회피로 대신 받아주는 역할."),
        ],
        "packs": [
            (1, "사랑할 수 없는", "서릿발 발자국, 네뷸라이저", 1, "서릿발 발자국은 얼어붙은 아우성 + 귀신 들린 신발. 네뷸라이저는 있으면 좋음."),
            (2, "헬스치킨", "탱고 닭양념장, 날카로운 실과 바늘, 목이 뻑뻑 가슴살, 뜨거운 육즙 다리살, 오염된 실과 바늘", 2, "초반 안정 보강."),
            (3, "낙화", "생강꽃, 안경 그리고 전해진 편지, 만화경", 1, "생강꽃 가지 + 깨진 안경 + 해진 우산. 해결사 5명/H사 2명 만화경."),
            (4, "탄환이 찍은 마침표", "흑염 파이프, 근접 전술 교본, 톱니 파편, 묵시적 계약 갱신, 평등", 2, "4층 추천 팩."),
            (5, "바라볼 수 밖에 없는", "물 속의 달, 거울 속의 꽃", 1, "호흡/파열 인격 지원. 5~10층 핵심."),
            (5, "1호선", "거짓 광배, 뱀 허물", 2, "장기 전투 및 생존 지원."),
            (5, "2호선", "굴레, 메트로놈", 2, "생존 지원."),
            (5, "호박색 어스름의 시련", "분홍빛 꽃잎다발, 부리 모양 목걸이, 노이즈 섞인 무전기, 워킹 베이스, 로열 젤리 퍼퓸", 1, "탄환/관통 인격 지원. 분홍빛 꽃잎다발은 핵심 조합."),
            (5, "LCB 정기검진 복각", "강화제 Mk.4, 시험 추출 : 초롱, 가시 전투화, 잔가지, 재점화 플러그", 2, "관통/화상 보조 선택지."),
            (5, "20번구의 기적 복각", "기쁜 봉제인형", 2, "슬픈 봉제인형 + 털방울 모자 + 거대한 선물 보따리. 피해량 증가 및 호흡 수급."),
            (11, "5호선", "애달픈 날숨, 깨어질 화포", 1, "애달픈 날숨 우선. 화포는 취향 선택."),
            (12, "3호선", "부화하지 않은 불씨, 경멸의 시선의 경멸", 1, "부화하지 않은 불씨는 합성으로라도 확보."),
            (13, "후반 선택", "N사 신 구인회, 개화하는 녹림, 어느 도서관의 어떤 책 속으로, 3호선-종착역, 영겁의 굴레", 2, "13~15층 후보."),
        ],
        "goods": [
            ("프레스티지 카드", 1, "시작 기프트."),
            ("귀신 들린 신발", 1, "시작 기프트. 서릿발 발자국 재료."),
            ("깨진 안경", 1, "시작 기프트. 생강꽃, 안경 그리고 전해진 편지 재료."),
            ("생강꽃, 안경 그리고 전해진 편지", 1, "생강꽃 가지 + 깨진 안경 + 해진 우산. 핵심 편지 루트."),
            ("분홍빛 꽃잎다발", 1, "분홍 꽃잎 + 잔향 + 축복이었던. 관통/탄환 지원 핵심."),
            ("결의", 2, "사로쟈 가중치와 참격 보조용."),
            ("물 속의 달", 1, "호흡/파열 전체 지원."),
            ("거울 속의 꽃", 1, "호흡/파열 전체 지원."),
            ("네뷸라이저", 2, "호흡 시작 시 있으면 좋음."),
            ("애달픈 날숨", 1, "5호선 핵심. 탕히스 효율 높음."),
            ("로열 젤리 퍼퓸", 2, "탕루 추천 기프트."),
            ("워킹 베이스", 2, "동섕돈/관통 지원."),
            ("기쁜 봉제인형", 2, "피해량 증가 및 호흡 수급."),
            ("부화하지 않은 불씨", 1, "12층 핵심. 합성으로라도 확보."),
            ("데스페라도", 3, "합성 비추천. 효과 받는 인원이 2명뿐이라 만들지 말 것."),
        ],
    },
]


def ensure_tables(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS decks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            keywords TEXT,
            description TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS deck_identities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deck_id INTEGER NOT NULL,
            identity_name TEXT NOT NULL,
            character TEXT,
            priority INTEGER DEFAULT 1,
            role TEXT,
            notes TEXT,
            FOREIGN KEY (deck_id) REFERENCES decks(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS deck_floor_packs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deck_id INTEGER NOT NULL,
            floor_number INTEGER NOT NULL,
            pack_name TEXT NOT NULL,
            key_gifts TEXT,
            priority INTEGER DEFAULT 1,
            notes TEXT,
            FOREIGN KEY (deck_id) REFERENCES decks(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS deck_goods_gifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deck_id INTEGER NOT NULL,
            gift_name TEXT NOT NULL,
            priority INTEGER DEFAULT 1,
            notes TEXT,
            FOREIGN KEY (deck_id) REFERENCES decks(id)
        )
        """
    )


def sync_deck(conn, deck):
    conn.execute(
        """
        INSERT INTO decks (name, keywords, description)
        VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            keywords = excluded.keywords,
            description = excluded.description
        """,
        (deck["name"], deck["keywords"], deck["description"]),
    )
    deck_id = conn.execute("SELECT id FROM decks WHERE name = ?", (deck["name"],)).fetchone()[0]

    conn.execute("DELETE FROM deck_identities WHERE deck_id = ?", (deck_id,))
    conn.executemany(
        """
        INSERT INTO deck_identities
            (deck_id, identity_name, character, priority, role, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [(deck_id, *row) for row in deck["identities"]],
    )

    conn.execute("DELETE FROM deck_floor_packs WHERE deck_id = ?", (deck_id,))
    conn.executemany(
        """
        INSERT INTO deck_floor_packs
            (deck_id, floor_number, pack_name, key_gifts, priority, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [(deck_id, *row) for row in deck["packs"]],
    )

    conn.execute("DELETE FROM deck_goods_gifts WHERE deck_id = ?", (deck_id,))
    conn.executemany(
        """
        INSERT INTO deck_goods_gifts
            (deck_id, gift_name, priority, notes)
        VALUES (?, ?, ?, ?)
        """,
        [(deck_id, *row) for row in deck["goods"]],
    )

    return deck_id, len(deck["identities"]), len(deck["packs"]), len(deck["goods"])


def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_tables(conn)
        results = [sync_deck(conn, deck) for deck in DECKS]
        conn.commit()
    finally:
        conn.close()

    for deck, result in zip(DECKS, results):
        deck_id, identity_count, pack_count, gift_count = result
        print(
            f"{deck['name']} synced: deck_id={deck_id}, "
            f"identities={identity_count}, floor_packs={pack_count}, goods_gifts={gift_count}"
        )


if __name__ == "__main__":
    main()
