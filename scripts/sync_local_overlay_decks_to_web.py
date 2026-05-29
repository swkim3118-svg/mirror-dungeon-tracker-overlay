import os
import sqlite3


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mirror_dungeon.db")


DECKS = [
    {
        "name": "흑수호파덱",
        "keywords": "호흡,파열,화상,진동,참격",
        "description": "홍원 군주 홍루 중심. 흑수 소속 7인 편성. 합을 잘 쳐서 안정성 최고. 기프트 수집량이 많아 숙련도 필요.",
        "identities": [
            ("홍원 군주 홍루", "홍루", 1, "에이스", "군루. 스킬교환 105. 속도 1순위 고정. 핵심 딜러."),
            ("흑수-사 로쟈", "로쟈", 1, "딜러", "사로쟈. 스킬교환 114. 파열+호흡."),
            ("흑수-유 필두 히스클리프", "히스클리프", 1, "딜러", "유히스. 스킬교환 015. 혈염도 수혜."),
            ("흑수-오 필두 이상", "이상", 1, "딜탱", "말상. 스킬교환 015. 흑수덱 딜탱."),
            ("홍원 방랑무사 료슈", "료슈", 1, "딜러", "방슈. 스킬교환 105. 관통 기프트 최적."),
            ("가주 후보 이스마엘", "이스마엘", 1, "회피", "시춘마엘. 스킬교환 105. 유일한 회피 인격."),
            ("흑수-사 그레고르", "그레고르", 1, "서포터", "사그렉. 스킬교환 114. 흑수 깔맞춤+호흡 5인용."),
        ],
        "packs": [
            (1, "공장팩", "서릿발 발자국(아우성+신발 조합)", 1, "파열 스타트. 관측: 프레스티지/안경/아우성"),
            (2, "헬스치킨", "오실바(필수), 양념장(팩보상 베스트)", 1, "날실바 중요도 낮음(군루 속도 1순위 고정)"),
            (3, "낙화", "생강꽃(필수), 만화경(선택)", 1, "안경 관측 -> 생안편 조합 목표"),
            (4, "탄환이 찍은 마침표", "흑염 파이프, 톱니 파편, 평등", 1, "파열깊 수집 시작"),
            (5, "심야청소 복각", "그림자 삿갓(팩보상 베스트), 묘각", 1, "파열 리롤 집중. 파탄/황홀경 합성"),
            (6, "20번구의 기적 복각", "개추인형(필수), 선물, 그림자 괴물, 이전칠자", 1, "인형 팩보상 베스트. 충전형 장갑 합성"),
            (7, "2호선", "굴레", 1, "익스팩 후반 턴종료 짤딜 방어. 화상 리롤"),
            (8, "절차탁춘", "마음을 닫는 붉은 천, 혈염도, 절차탁마", 1, "흑철마갑 합성(선택). 진동 리롤"),
            (9, "바라볼 수밖에 없는", "물 속의 달, 거울 속의 꽃", 1, "전투 스테이지 많아 코스트 수급 좋음"),
            (10, "정기검진 복각", "강화제, 잔가지, 홍염살, 리뉴얼, 주화, 원반", 1, "화룡점정. 화상깊 사전 준비 필수"),
            (11, "3호선", "부화하지 않은 불씨, 경멸의 시선", 1, "고정"),
            (13, "5호선", "화포, 날숨, 가시", 1, ""),
            (14, "삽시호", "", 2, "14층 추천"),
            (15, "N사 신 구인회", "", 2, "15층 추천 (팩 꼬이면 녹림도 가능)"),
        ],
        "goods": [
            ("서릿발 발자국", 1, "아우성+신발 조합. 1층 공장팩."),
            ("생강꽃, 안경 그리고 전해진 편지", 1, "생안편. 합승리시 공렙감. 3층 낙화팩."),
            ("개추인형", 1, "6층 20번구 복각. 반드시 합성."),
            ("오실바", 1, "출혈합 99이상 육체미(위력+). 2층 헬스치킨."),
            ("그림자 삿갓", 1, "5층 심야청소. 참격인원 딜뻥."),
            ("묘각", 1, "5층 심야청소. 파열 지원."),
            ("마음을 닫는 붉은 천", 1, "8층 절차탁춘."),
            ("혈염도", 1, "8층 절차탁춘. 유히스 예열."),
            ("절차탁마", 1, "8층 절차탁춘. 덕목 지+용+인 조합."),
            ("물 속의 달", 1, "9층 바라볼 수밖에 없는."),
            ("거울 속의 꽃", 1, "9층 바라볼 수밖에 없는."),
            ("부화하지 않은 불씨", 1, "11층 3호선. 보험."),
            ("굴레", 2, "7층 2호선. 생존 지원."),
            ("이전칠자", 2, "6층 20번구 합성. 파열 5인 조건부."),
            ("흑철마갑", 2, "8층 절차탁춘 합성. 없어도 무방."),
            ("명경지수", 2, "파열 3티어 합성. 생존 보험."),
            ("파탄", 2, "5층 심야청소 합성."),
            ("황홀경", 2, "5층 심야청소 합성."),
        ],
    },
    {
        "name": "진침탕덱",
        "keywords": "진동,침잠,탄환,화상",
        "description": "잔향슈+정이스 발푸밤 듀오 중심. 탄환+진동+침잠 시너지. 현 메타 1티어. 필수파츠 많아 뉴비 비권장.",
        "identities": [
            ("잔향 료슈", "료슈", 1, "에이스", "잔슈. 스킬교환 006. 진동/침잠+탄환. 핵심 딜러. 1번 자리."),
            ("정오의 이스마엘", "이스마엘", 1, "에이스", "정이스. 스킬교환 006. 진동/침잠. 광 스택 -> 코오쟌 극딜."),
            ("우울한 오티스", "오티스", 1, "탱커", "우티스. 스킬교환 114. 진동/침잠+탄환. 우울 3공명 -> 가면 강화."),
            ("횡단 뫼르소", "뫼르소", 1, "딜러", "뫼횡. 스킬교환 114. 진동/화상+탄환. 맹호표탄 -> 초절맹호살격난참."),
            ("죽은 나비 싱클레어", "싱클레어", 1, "딜러", "죽나상. 스킬교환 015. 침잠/탄환. 먹장+데스페라도 양쪽 충족."),
            ("엄숙한 로쟈", "로쟈", 1, "딜러", "엄준싱. 스킬교환 006. 화상/진동+탄환. 예열전 뫼횡보다 딜 높음."),
            ("램프 그레고르", "그레고르", 1, "서포터", "램그렉. 스킬교환 015. 침잠/화상. 숲의 파수꾼(정신력 회복). 탱커."),
            ("검파우 파우스트", "파우스트", 2, "서폿패", "패시브용. 버파우로 대체 가능."),
            ("양돈 돈키호테", "돈키호테", 2, "서폿패", "패시브용. 증돈으로 대체 가능."),
            ("탕자 홍루", "홍루", 2, "서폿패", "패시브용."),
            ("와히스 히스클리프", "히스클리프", 2, "서폿패", "패시브용. 여히스 동기화 금지."),
            ("절쟈 로쟈", "로쟈", 2, "서폿패", "패시브용. 렘그렉 대신 절쟈도 가능."),
        ],
        "packs": [
            (1, "공장 자동화", "서릿발 발자국(아우성 관측시)", 1, "관측: 아우성->공장자동화 / 분홍구두->얼어붙은 마음"),
            (2, "헬스치킨", "탱고(필수), 날실바(필수), 오실바, 치킨 2개", 1, "물음표 방 중심으로 이동"),
            (3, "탄환이 찍은 마침표", "근접 전술교본(필수), 흑염 파이프(필수)", 1, "나머지 전용 에깊도 수집"),
            (4, "증오와 절망", "눈벼검(필수), 잿빛 별자리의 가호(필수), 선택받지 못한 자(필수)", 1, "충전 에깊도 수집"),
            (5, "호박빛 어스름의 시련", "분홍꽃잎(필수), 데스페라도(필수)", 1, "4층 전용 에깊 5개 이상 -> 커피 보너스"),
            (5, "20번구의 기적 복각", "기쁜 봉제인형(우선), 나머지 전부", 1, "만들 수 있는 건 다 만들기"),
            (5, "시살시/시살시 복각", "시침+시계케이스 교차 합성", 1, "색깔 교차해서 합성"),
            (5, "침잠쇄도/가라앉는 우울", "먹장구름(필수)", 1, "여기서만 먹장구름 획득 가능"),
            (5, "1호선", "광배, 뱀허물", 2, "선택"),
            (5, "2호선", "굴레", 2, "가능하면 수집"),
            (5, "3호선", "부화하지 않은 불씨", 1, "부활템"),
        ],
        "goods": [
            ("먹장구름", 1, "침잠 10인 조건. 침잠쇄도/가라앉는 우울팩에서만 획득."),
            ("데스페라도", 1, "탄환 5인 조건. 호박빛 어스름 필수."),
            ("분홍꽃잎", 1, "호박빛 어스름 필수."),
            ("근접 전술교본", 1, "3층 마침표팩 필수."),
            ("흑염 파이프", 1, "3층 마침표팩 필수."),
            ("눈벼검", 1, "4층 증절팩 필수."),
            ("잿빛 별자리의 가호", 1, "4층 증절팩 필수."),
            ("선택받지 못한 자", 1, "4층 증절팩 필수."),
            ("기쁜 봉제인형", 1, "20번구 복각. 우선 합성."),
            ("탱고 닭양념장", 1, "2층 헬스치킨 필수."),
            ("날실바", 1, "2층 헬스치킨 필수."),
            ("부화하지 않은 불씨", 1, "3호선. 부활 보험."),
            ("프티카", 2, "관측 추천. 초반 가격 체감 큼."),
            ("개추인형", 2, "관측 추천. 사기 에깊."),
            ("굴레", 2, "2호선. 생존 지원."),
            ("광배", 2, "1호선."),
            ("뱀허물", 2, "1호선."),
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
