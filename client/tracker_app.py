"""
Mirror Dungeon Tracker - 최종 통합 버전
OCR 스캔 + 수동 검색 + 추천 + 공략 가이드 + 서버 연동 + 피드백
"""
import sys
import os
import sqlite3
import threading
import uuid
import difflib
import unicodedata
import json
import time
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QListWidget, QTabWidget,
                              QLineEdit, QComboBox, QListWidgetItem, QSpinBox,
                              QFrame, QPlainTextEdit, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
import ctypes

if sys.platform == 'win32':
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x80000
    WS_EX_TRANSPARENT = 0x20
    user32 = ctypes.windll.user32

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(BASE_DIR, 'data', 'mirror_dungeon.db')
GENERAL_GIFT_GUIDE_PATH = os.path.join(BASE_DIR, 'data', 'general_ego_gift_guide.md')
SERVER_URL = os.environ.get("MD_SERVER_URL", "http://13.218.132.41:8080")


def _local_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_name(text):
    text = unicodedata.normalize("NFKC", text or "").lower()
    return ''.join(ch for ch in text if ch.isalnum())


def load_general_gift_guide():
    sections = {}
    current_section = None
    try:
        with open(GENERAL_GIFT_GUIDE_PATH, 'r', encoding='utf-8') as f:
            for raw_line in f:
                line = raw_line.strip()
                if line.startswith('## '):
                    current_section = line[3:].strip()
                    sections.setdefault(current_section, [])
                elif current_section and line.startswith('- '):
                    sections[current_section].append(line[2:].strip())
    except Exception:
        return {}
    return sections


class DataClient:
    """서버 API 우선, 실패 시 로컬 SQLite 폴백.

    검색/매칭은 전체 기프트 목록을 1회 로드해 메모리에서 처리한다.
    세션 로그/피드백은 서버 전용(오프라인 시 조용히 스킵).
    """

    def __init__(self):
        self.online = False
        self._name_index = {}
        self._normalized_name_index = {}
        self._normalized_names = []
        self.session_id = None
        self._gifts = []          # 전체 기프트 dict 리스트
        self._name_index = {}     # 표시이름 -> gift dict
        self._names = []          # 퍼지 매칭용 이름 리스트
        self.session_id = None
        self._web_decks = None
        self._deck_detail_cache = {}
        self._general_gift_guide = load_general_gift_guide()
        self.user_id = self._load_user_id()
        self._load_gifts()

    # --- user id (재실행 시 동일 사용자 유지) ---
    def _load_user_id(self):
        path = os.path.join(BASE_DIR, 'data', '.user_id')
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    uid = f.read().strip()
                    if uid:
                        return uid
            uid = uuid.uuid4().hex[:12]
            with open(path, 'w', encoding='utf-8') as f:
                f.write(uid)
            return uid
        except Exception:
            return uuid.uuid4().hex[:12]

    def _api_get(self, path, params=None, timeout=3):
        r = requests.get(f"{SERVER_URL}{path}", params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()

    def _api_post(self, path, json, timeout=3):
        r = requests.post(f"{SERVER_URL}{path}", json=json, timeout=timeout)
        r.raise_for_status()
        return r.json()

    # --- 전체 기프트 로드 (API -> 로컬 폴백) ---
    def _load_gifts(self):
        rows = None
        try:
            rows = self._api_get("/gifts")
            self.online = True
        except Exception:
            self.online = False
            try:
                conn = _local_db()
                rows = [dict(r) for r in conn.execute("SELECT * FROM ego_gifts").fetchall()]
                conn.close()
            except Exception:
                rows = []
        self._gifts = rows or []
        self._name_index = {}
        self._normalized_name_index = {}
        self._names = []
        self._normalized_names = []
        for g in self._gifts:
            for name in (g.get('name_kr'), g.get('name')):
                if not name:
                    continue
                self._name_index.setdefault(name, g)
                if name not in self._names:
                    self._names.append(name)
                normalized = normalize_name(name)
                if normalized:
                    self._normalized_name_index.setdefault(normalized, g)
                    if normalized not in self._normalized_names:
                        self._normalized_names.append(normalized)

    @property
    def status_text(self):
        mode = "Server" if self.online else "Local"
        return f"{mode} | {len(self._gifts)} gifts | user {self.user_id}"

    # --- 검색 (메모리) ---
    def search_gifts(self, text, keyword='All', limit=25):
        text = normalize_name(text)
        out = []
        for g in self._gifts:
            if keyword != 'All':
                kw = (g.get('keyword') or '')
                if keyword.lower() not in kw.lower():
                    continue
            if text:
                hay = normalize_name(f"{g.get('name','')} {g.get('name_kr','')}")
                if text not in hay:
                    continue
            out.append(g)
        out.sort(key=lambda x: -(x.get('tier') or 0))
        return out[:limit]

    def gift_by_name(self, name):
        return self._name_index.get(name)

    def gift_by_id(self, gift_id):
        try:
            gift_id = int(gift_id)
        except (TypeError, ValueError):
            return None
        for gift in self._gifts:
            if gift.get('id') == gift_id:
                return gift
        return None

    # --- OCR 텍스트 -> 기프트 퍼지 매칭 ---
    def match_gift(self, ocr_text, cutoff=0.55):
        ocr_text = (ocr_text or '').strip()
        normalized = normalize_name(ocr_text)
        if not normalized or not self._normalized_names:
            return None
        if normalized in self._normalized_name_index:
            return self._normalized_name_index[normalized]
        # 1) 부분 포함 (가장 신뢰도 높음)
        for name in self._names:
            normalized_name = normalize_name(name)
            if normalized_name and (normalized_name in normalized or normalized in normalized_name) and len(normalized_name) >= 2:
                return self._name_index[name]
        # 2) 퍼지 매칭
        m = difflib.get_close_matches(normalized, self._normalized_names, n=1, cutoff=cutoff)
        if m:
            return self._normalized_name_index[m[0]]
        return None

    # --- 추천 (보유 기프트 키워드 시너지) ---
    def recommend(self, owned_names, floor=None, deck=None):
        try:
            data = self._api_post("/recommend/ai", {
                "current_gifts": owned_names,
                "current_floor": floor or 1,
                "deck": None if not deck or deck == "All" else deck,
                "limit": 5,
            }, timeout=25)
            recs = data.get("gift_recommendations") or []
            if recs:
                summary = data.get("summary") or "Gemini"
                return [("AI", summary)], recs[:5]
        except Exception:
            pass

        kws = {}
        owned_set = set(owned_names)
        for n in owned_names:
            g = self._name_index.get(n)
            if g and g.get('keyword'):
                for k in g['keyword'].split(','):
                    k = k.strip()
                    if k and k != 'General':
                        kws[k] = kws.get(k, 0) + 1
        if not kws:
            return [], []
        top = max(kws, key=kws.get)
        recs = []
        guide_sections = {
            'Rupture': '파열', 'Tremor': '진동', 'Poise': '호흡',
            'Charge': '충전', 'Burn': '화상', 'Sinking': '침잠',
            'Bleed': '출혈',
        }
        guide_names = (
            self._general_gift_guide.get(guide_sections.get(top), [])
            + self._general_gift_guide.get('범용', [])
            + self._general_gift_guide.get('참관타 에깊', [])
        )
        guided = {normalize_name(name.split('(')[0]): i for i, name in enumerate(guide_names)}
        for g in self._gifts:
            disp = g.get('name_kr') or g.get('name')
            if disp in owned_set:
                continue
            if top.lower() in (g.get('keyword') or '').lower():
                recs.append(g)
        recs.sort(key=lambda x: (
            guided.get(normalize_name(x.get('name_kr') or x.get('name')), len(guided) + 1),
            -(x.get('tier') or 0),
        ))
        kw_summary = sorted(kws.items(), key=lambda x: -x[1])
        return kw_summary, recs[:5]

    # --- 가이드 테이블 (API -> 로컬) ---
    def _table(self, api_path, sql):
        try:
            data = self._api_get(api_path)
            self.online = True
            return data
        except Exception:
            try:
                conn = _local_db()
                rows = [dict(r) for r in conn.execute(sql).fetchall()]
                conn.close()
                return rows
            except Exception:
                return []

    def web_decks(self):
        if self._web_decks is not None:
            return self._web_decks
        try:
            self._web_decks = self._api_get("/decks")
            self.online = True
            return self._web_decks
        except Exception:
            try:
                conn = _local_db()
                self._web_decks = [dict(r) for r in conn.execute(
                    "SELECT * FROM decks ORDER BY id"
                ).fetchall()]
                conn.close()
                return self._web_decks
            except Exception:
                self._web_decks = []
                return []

    def _web_deck_by_name(self, deck_name):
        if not deck_name or deck_name == "All":
            return None
        for deck in self.web_decks():
            if deck.get("name") == deck_name:
                return deck
        return None

    def deck_detail(self, deck_name):
        deck = self._web_deck_by_name(deck_name)
        if not deck:
            return None
        deck_id = deck.get("id")
        if deck_id in self._deck_detail_cache:
            return self._deck_detail_cache[deck_id]
        try:
            detail = self._api_get(f"/decks/{deck_id}")
            self.online = True
        except Exception:
            try:
                conn = _local_db()
                deck_row = conn.execute("SELECT * FROM decks WHERE id=?", (deck_id,)).fetchone()
                detail = {
                    "deck": dict(deck_row) if deck_row else deck,
                    "identities": [dict(r) for r in conn.execute(
                        "SELECT * FROM deck_identities WHERE deck_id=? ORDER BY priority, id",
                        (deck_id,),
                    ).fetchall()],
                    "floor_packs": [dict(r) for r in conn.execute(
                        "SELECT * FROM deck_floor_packs WHERE deck_id=? ORDER BY floor_number, priority",
                        (deck_id,),
                    ).fetchall()],
                }
                conn.close()
            except Exception:
                detail = None
        if detail:
            self._deck_detail_cache[deck_id] = detail
        return detail

    def floor_recommendations(self, floor, deck=None):
        deck = None if not deck or deck == "All" else deck
        detail = self.deck_detail(deck) if deck else None
        if detail is not None:
            rows = []
            for p in detail.get("floor_packs", []):
                if (p.get("floor_number") or 0) <= floor:
                    rows.append(dict(p))
            return sorted(rows, key=lambda x: (-(x.get("floor_number") or 0), x.get("priority") or 1))
        try:
            data = self._api_get(f"/floor/{floor}/recommendations")
            if deck:
                data = [p for p in data if deck in (p.get('notes') or '')]
            return data
        except Exception:
            try:
                conn = _local_db()
                if deck:
                    rows = [dict(r) for r in conn.execute(
                        "SELECT * FROM floor_recommendations WHERE floor_number<=? AND notes LIKE ? "
                        "ORDER BY floor_number DESC, priority ASC", (floor, f'%{deck}%')).fetchall()]
                else:
                    rows = [dict(r) for r in conn.execute(
                        "SELECT * FROM floor_recommendations WHERE floor_number<=? "
                        "ORDER BY floor_number DESC, priority ASC", (floor,)).fetchall()]
                conn.close()
                return rows
            except Exception:
                return []

    def formation(self):
        web_rows = []
        for deck in self.web_decks():
            detail = self.deck_detail(deck.get("name"))
            if not detail:
                continue
            for i, row in enumerate(detail.get("identities", []), start=1):
                d = dict(row)
                web_rows.append({
                    "deck_name": deck.get("name"),
                    "position": d.get("priority") or i,
                    "character_name": d.get("identity_name") or "",
                    "character_nickname": d.get("character") or "",
                    "attack_type": d.get("role") or "",
                    "skill_exchange": d.get("notes") or "",
                    "recommended_gifts": "",
                    "keywords": deck.get("keywords") or "",
                    "notes": d.get("notes") or "",
                })
        if web_rows:
            return web_rows
        return self._table("/formation",
                           "SELECT * FROM formation_guide ORDER BY deck_name, position")

    def combinations(self, deck=None):
        deck = None if not deck or deck == "All" else deck
        try:
            data = self._api_get("/combinations")
            self.online = True
            if deck:
                data = [c for c in data if c.get('deck_name') == deck]
            return data
        except Exception:
            try:
                conn = _local_db()
                if deck:
                    rows = [dict(r) for r in conn.execute(
                        "SELECT * FROM gift_combinations WHERE deck_name=?",
                        (deck,)
                    ).fetchall()]
                else:
                    rows = [dict(r) for r in conn.execute("SELECT * FROM gift_combinations").fetchall()]
                conn.close()
                return rows
            except Exception:
                return []

    # --- 세션 / 로그 / 피드백 (서버 전용) ---
    def ensure_session(self):
        if self.session_id is not None:
            return self.session_id
        try:
            res = self._api_post("/sessions",
                                  {"user_id": self.user_id, "difficulty": "normal"})
            self.session_id = res.get("session_id")
            self.online = True
        except Exception:
            self.session_id = None
        return self.session_id

    def log_gift(self, floor, gift_name, gift_id=None, was_recommended=False):
        sid = self.ensure_session()
        if sid is None:
            return False
        try:
            self._api_post(f"/sessions/{sid}/gifts", {
                "session_id": sid,
                "floor_number": floor,
                "gift_id": gift_id,
                "gift_name": gift_name,
                "was_recommended": was_recommended,
            })
            return True
        except Exception:
            return False

    def submit_feedback(self, feedback_type, content, rating=None):
        try:
            self._api_post("/feedback", {
                "user_id": self.user_id,
                "session_id": self.session_id,
                "feedback_type": feedback_type,
                "content": content,
                "rating": rating,
            })
            return True
        except Exception:
            return False

    def submit_run_result(self, payload):
        self.ensure_session()
        result = payload.get("result")
        return self.submit_feedback(
            "런 결과",
            json.dumps(payload, ensure_ascii=False),
            5 if result == "클리어" else 1,
        )


class TitleBar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_widget = parent
        self.setFixedHeight(26)
        self.setStyleSheet("background-color: #0d1117; border-bottom: 1px solid #f8c200; border-radius: 0;")
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 0, 4, 0)
        title = QLabel("Mirror Dungeon Tracker")
        title.setStyleSheet("color: #f8c200; font-size: 9pt; font-weight: bold; border: none;")
        layout.addWidget(title)
        layout.addStretch()
        self.pin_btn = QPushButton(chr(0x1F4CC))
        self.pin_btn.setFixedSize(22, 22)
        self.pin_btn.setStyleSheet("border: none; font-size: 11pt; background: transparent;")
        self.pin_btn.clicked.connect(parent.toggle_click_through)
        layout.addWidget(self.pin_btn)
        min_btn = QPushButton(chr(0x2500))
        min_btn.setFixedSize(22, 22)
        min_btn.setStyleSheet("border: none; color: #e0e0e0; background: transparent;")
        min_btn.clicked.connect(parent.showMinimized)
        layout.addWidget(min_btn)
        close_btn = QPushButton(chr(0x2715))
        close_btn.setFixedSize(22, 22)
        close_btn.setStyleSheet("border: none; color: #ff5555; background: transparent;")
        close_btn.clicked.connect(parent.close)
        layout.addWidget(close_btn)
        self.setLayout(layout)
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.parent_widget.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.parent_widget.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class MirrorDungeonTracker(QWidget):
    def __init__(self):
        super().__init__()
        self.owned_gifts = []
        self.click_through = False
        self.scan_running = False
        self.last_auto_run_key = None
        self.last_auto_run_at = 0
        self.data = DataClient()
        self.initUI()
        self.load_formation()
        self.load_floor_recommendations()
        self.load_combinations()
        self.status_label.setText(self.data.status_text)

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(50, 100, 360, 680)
        self.setMinimumSize(300, 400)

        self.container = QFrame(self)
        self.container.setStyleSheet("QFrame { background-color: rgba(13, 17, 23, 235); border: 1px solid #f8c200; border-radius: 6px; }")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

        cl = QVBoxLayout(self.container)
        cl.setContentsMargins(0, 0, 0, 4)
        cl.setSpacing(2)

        self.title_bar = TitleBar(self)
        cl.addWidget(self.title_bar)

        content = QWidget()
        content.setStyleSheet("""
            QWidget { background: transparent; color: #e0e0e0; font-family: 'Malgun Gothic'; font-size: 9pt; }
            QLabel { color: #ccc; border: none; }
            QPushButton { background-color: #161b22; border: 1px solid #30363d; padding: 3px 8px; border-radius: 3px; color: #e0e0e0; }
            QPushButton:hover { border-color: #f8c200; }
            QLineEdit { background-color: #161b22; border: 1px solid #30363d; padding: 3px; color: #e0e0e0; border-radius: 3px; }
            QPlainTextEdit { background-color: #161b22; border: 1px solid #30363d; color: #e0e0e0; border-radius: 3px; }
            QListWidget { background-color: rgba(13,17,23,200); border: 1px solid #30363d; border-radius: 3px; }
            QListWidget::item { padding: 2px; }
            QListWidget::item:selected { background-color: #1f2937; }
            QTabWidget::pane { border: 1px solid #30363d; border-radius: 3px; background: transparent; }
            QTabBar::tab { background: #161b22; padding: 4px 8px; color: #8b949e; border: 1px solid #30363d; margin-right: 1px; }
            QTabBar::tab:selected { background: #0d1117; color: #f8c200; }
            QComboBox { background: #161b22; border: 1px solid #30363d; padding: 2px; color: #e0e0e0; }
            QSpinBox { background: #161b22; border: 1px solid #30363d; padding: 2px; color: #e0e0e0; }
        """)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(6, 2, 6, 2)
        content_layout.setSpacing(3)

        # 상단: 층 + 스캔 버튼
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel('Floor:'))
        self.floor_spin = QSpinBox()
        self.floor_spin.setRange(1, 15)
        self.floor_spin.setValue(15)
        self.floor_spin.setFixedWidth(45)
        self.floor_spin.valueChanged.connect(self.on_floor_change)
        ctrl.addWidget(self.floor_spin)
        ctrl.addStretch()
        self.scan_btn = QPushButton('Scan')
        self.scan_btn.setStyleSheet("QPushButton { background: #238636; border-color: #2ea043; } QPushButton:hover { background: #2ea043; }")
        self.scan_btn.clicked.connect(self.do_scan)
        ctrl.addWidget(self.scan_btn)
        self.opacity_combo = QComboBox()
        self.opacity_combo.addItems(['100', '90', '80', '70'])
        self.opacity_combo.setCurrentIndex(1)
        self.opacity_combo.setFixedWidth(45)
        self.opacity_combo.currentIndexChanged.connect(self.change_opacity)
        ctrl.addWidget(self.opacity_combo)
        content_layout.addLayout(ctrl)

        # 상태 라벨
        self.status_label = QLabel('Ready')
        self.status_label.setStyleSheet('color: #8b949e; font-size: 8pt; border: none;')
        content_layout.addWidget(self.status_label)

        # 탭
        tabs = QTabWidget()
        tabs.setDocumentMode(True)

        # 탭 1: 보유 + 추천
        ot = QWidget()
        ot.setStyleSheet("background: transparent;")
        ol = QVBoxLayout(ot)
        ol.setContentsMargins(2, 2, 2, 2)
        ol.addWidget(QLabel('Owned (double-click to remove):'))
        self.owned_list = QListWidget()
        self.owned_list.setMaximumHeight(140)
        self.owned_list.itemDoubleClicked.connect(self.remove_from_owned)
        ol.addWidget(self.owned_list)
        rb = QPushButton('Get Recommendations')
        rb.clicked.connect(self.get_recommendations)
        ol.addWidget(rb)
        self.rec_list = QListWidget()
        self.rec_list.itemDoubleClicked.connect(self.add_to_owned)
        ol.addWidget(self.rec_list)
        tabs.addTab(ot, "Owned")

        # 탭 2: 검색
        st = QWidget()
        st.setStyleSheet("background: transparent;")
        sl = QVBoxLayout(st)
        sl.setContentsMargins(2, 2, 2, 2)
        sr = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Search gift...')
        self.search_input.returnPressed.connect(self.search_gifts)
        sr.addWidget(self.search_input)
        self.keyword_combo = QComboBox()
        self.keyword_combo.addItems(['All', 'Burn', 'Bleed', 'Tremor', 'Rupture', 'Sinking', 'Poise', 'Charge'])
        self.keyword_combo.setFixedWidth(65)
        sr.addWidget(self.keyword_combo)
        sl.addLayout(sr)
        self.search_results = QListWidget()
        self.search_results.itemDoubleClicked.connect(self.add_to_owned)
        sl.addWidget(self.search_results)
        sl.addWidget(QLabel('Double-click to add'))
        tabs.addTab(st, "Search")

        # 탭 3: 팩
        pt = QWidget()
        pt.setStyleSheet("background: transparent;")
        pl = QVBoxLayout(pt)
        pl.setContentsMargins(2, 2, 2, 2)
        pl.setSpacing(3)
        pack_deck_row = QHBoxLayout()
        pack_deck_row.addWidget(QLabel("덱:"))
        self.pack_deck_combo = QComboBox()
        self.pack_deck_combo.currentTextChanged.connect(self.load_floor_recommendations)
        pack_deck_row.addWidget(self.pack_deck_combo)
        pl.addLayout(pack_deck_row)
        self.pack_list = QListWidget()
        pl.addWidget(self.pack_list)
        tabs.addTab(pt, "Pack")

        # 탭 4: 편성
        ft = QWidget()
        ft.setStyleSheet("background: transparent;")
        fl = QVBoxLayout(ft)
        fl.setContentsMargins(2, 2, 2, 2)
        fl.setSpacing(3)

        # 덱 선택
        deck_row = QHBoxLayout()
        deck_row.addWidget(QLabel("덱:"))
        self.deck_combo = QComboBox()
        self.deck_combo.currentTextChanged.connect(self.on_deck_changed)
        deck_row.addWidget(self.deck_combo)
        fl.addLayout(deck_row)

        # 인격 선택 목록 (체크박스)
        fl.addWidget(QLabel("인격 선택 (보유한 인격 체크):"))
        from PyQt5.QtWidgets import QScrollArea
        self.persona_list = QListWidget()
        self.persona_list.setMaximumHeight(160)
        self.persona_list.itemChanged.connect(self.on_persona_changed)
        fl.addWidget(self.persona_list)

        # 선택된 인격 공략
        fl.addWidget(QLabel("선택 인격 공략:"))
        self.form_list = QListWidget()
        fl.addWidget(self.form_list)
        tabs.addTab(ft, "Team")

        # 탭 5: 조합
        ct = QWidget()
        ct.setStyleSheet("background: transparent;")
        cbl = QVBoxLayout(ct)
        cbl.setContentsMargins(2, 2, 2, 2)
        cbl.setSpacing(3)
        combo_deck_row = QHBoxLayout()
        combo_deck_row.addWidget(QLabel("덱:"))
        self.combo_deck_combo = QComboBox()
        self.combo_deck_combo.currentTextChanged.connect(self.load_combinations)
        combo_deck_row.addWidget(self.combo_deck_combo)
        cbl.addLayout(combo_deck_row)
        self.combo_list = QListWidget()
        cbl.addWidget(self.combo_list)
        tabs.addTab(ct, "Combo")

        # 탭 6: 피드백
        fbt = QWidget()
        fbt.setStyleSheet("background: transparent;")
        fbl = QVBoxLayout(fbt)
        fbl.setContentsMargins(2, 2, 2, 2)
        fbl.addWidget(QLabel('피드백 종류:'))
        self.fb_type = QComboBox()
        self.fb_type.addItems(['OCR 인식', '추천 정확도', '사용성', '버그', '기타'])
        fbl.addWidget(self.fb_type)
        fbr = QHBoxLayout()
        fbr.addWidget(QLabel('별점:'))
        self.fb_rating = QComboBox()
        self.fb_rating.addItems(['5', '4', '3', '2', '1'])
        self.fb_rating.setFixedWidth(50)
        fbr.addWidget(self.fb_rating)
        fbr.addStretch()
        fbl.addLayout(fbr)
        fbl.addWidget(QLabel('내용:'))
        self.fb_text = QPlainTextEdit()
        self.fb_text.setPlaceholderText('의견을 적어주세요...')
        self.fb_text.setMaximumHeight(90)
        fbl.addWidget(self.fb_text)
        self.fb_send = QPushButton('피드백 보내기')
        self.fb_send.setStyleSheet("QPushButton { background: #1f6feb; border-color: #388bfd; } QPushButton:hover { background: #388bfd; }")
        self.fb_send.clicked.connect(self.send_feedback)
        fbl.addWidget(self.fb_send)
        self.fb_status = QLabel('')
        self.fb_status.setStyleSheet('color: #8b949e; font-size: 8pt; border: none;')
        fbl.addWidget(self.fb_status)
        fbl.addStretch()
        tabs.addTab(fbt, "Feedback")

        # Run result logging. Uses the existing feedback API so no DB schema change is needed.
        rt = QWidget()
        self.run_panel = rt
        rt.setStyleSheet("background: transparent;")
        rl = QVBoxLayout(rt)
        rl.setContentsMargins(2, 2, 2, 2)
        rl.setSpacing(3)
        rl.addWidget(QLabel('Result:'))
        self.run_result = QComboBox()
        self.run_result.addItems(['클리어', '전복'])
        rl.addWidget(self.run_result)
        rl.addWidget(QLabel('Difficulty:'))
        self.run_difficulty = QComboBox()
        self.run_difficulty.addItems(['normal', 'hard', 'ritornello', 'other'])
        rl.addWidget(self.run_difficulty)
        rl.addWidget(QLabel('Deck / build:'))
        self.run_deck = QLineEdit()
        self.run_deck.setPlaceholderText('Bleed, Poise, Sinking...')
        rl.addWidget(self.run_deck)
        rl.addWidget(QLabel('Condition / cause:'))
        self.run_cause = QLineEdit()
        self.run_cause.setPlaceholderText('Boss, pack, missing key gift...')
        rl.addWidget(self.run_cause)
        rl.addWidget(QLabel('Memo:'))
        self.run_note = QPlainTextEdit()
        self.run_note.setMaximumHeight(95)
        rl.addWidget(self.run_note)
        self.run_auto_save = QCheckBox('Auto-save detected Mirror Dungeon result')
        self.run_auto_save.setChecked(True)
        rl.addWidget(self.run_auto_save)
        self.run_auto_watch = QCheckBox('Watch screen every 15s')
        self.run_auto_watch.stateChanged.connect(self.toggle_auto_watch)
        rl.addWidget(self.run_auto_watch)
        self.run_send = QPushButton('Save Run Result')
        self.run_send.setStyleSheet("QPushButton { background: #1f6feb; border-color: #388bfd; } QPushButton:hover { background: #388bfd; }")
        self.run_send.clicked.connect(self.send_run_result)
        rl.addWidget(self.run_send)
        self.run_status = QLabel('')
        self.run_status.setStyleSheet('color: #8b949e; font-size: 8pt; border: none;')
        rl.addWidget(self.run_status)
        rl.addStretch()
        self.auto_watch_timer = QTimer(self)
        self.auto_watch_timer.setInterval(15000)
        self.auto_watch_timer.timeout.connect(self.do_scan)

        content_layout.addWidget(tabs)
        cl.addWidget(content)

    def do_scan(self):
        """OCR 스캔 실행 (별도 스레드)"""
        if self.scan_running:
            return
        self.scan_running = True
        self.scan_btn.setEnabled(False)
        self.status_label.setText("Scanning...")
        self.status_label.setStyleSheet('color: #f8c200; font-size: 8pt; border: none;')

        def run_scan():
            try:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from ocr_client import MirrorDungeonOCR
                if not hasattr(self, '_ocr'):
                    self._ocr = MirrorDungeonOCR()
                result = self._ocr.scan()
                QTimer.singleShot(0, lambda: self.on_scan_done(result))
            except Exception as e:
                QTimer.singleShot(0, lambda: self.on_scan_done({'error': str(e), 'texts': []}))

        threading.Thread(target=run_scan, daemon=True).start()

    def _add_owned_gift(self, gift, was_recommended=False):
        if not gift:
            return False
        name = gift.get('name_kr') or gift.get('name')
        if not name or name in self.owned_gifts:
            return False
        self.owned_gifts.append(name)
        item = QListWidgetItem(f"[T{gift.get('tier', '?')}] {name}")
        item.setData(Qt.UserRole, gift)
        self.owned_list.addItem(item)
        self.data.log_gift(self.floor_spin.value(), name, gift.get('id'), was_recommended=was_recommended)
        return True

    def on_scan_done(self, result):
        """스캔 완료 콜백: OCR 텍스트를 DB 기프트와 매칭"""
        self.scan_running = False
        self.scan_btn.setEnabled(True)
        if result.get('error'):
            self.status_label.setText(f"Error: {str(result['error'])[:40]}")
            self.status_label.setStyleSheet('color: #ff5555; font-size: 8pt; border: none;')
            return

        screen = result.get('screen_type') or 'unknown'
        texts = result.get('gift_texts') or result.get('texts') or []
        floor = self.floor_spin.value()

        added = 0
        unmatched = []
        matched_ids = set()

        for t in texts:
            g = self.data.match_gift(t)
            if not g:
                unmatched.append(t)
                continue
            if g.get('id') in matched_ids:
                continue
            if self._add_owned_gift(g, was_recommended=False):
                added += 1
                matched_ids.add(g.get('id'))

        icon_added = 0
        for match in result.get('icon_matches') or []:
            g = self.data.gift_by_id(match.get('gift_id'))
            if not g:
                continue
            if g.get('id') in matched_ids:
                continue
            if self._add_owned_gift(g, was_recommended=False):
                added += 1
                icon_added += 1
                matched_ids.add(g.get('id'))

        icon_count = len(result.get('icon_matches') or [])
        total_seen = len(texts) + icon_count
        msg = f"[{screen}] {added}/{total_seen} matched & added"
        if icon_count:
            msg += f" | icon fallback {icon_added}/{icon_count}"
        if unmatched:
            msg += f" | missed: {', '.join(unmatched[:2])[:28]}"
        auto_msg = self.auto_save_detected_run_result(result.get('run_result'))
        if auto_msg:
            msg += f" | {auto_msg}"
        self.status_label.setText(msg)
        self.status_label.setStyleSheet('color: #4caf50; font-size: 8pt; border: none;')

    def auto_save_detected_run_result(self, detected):
        if not detected or not self.run_auto_save.isChecked():
            return ""
        text = detected.get("text") or ""
        result = detected.get("result") or "미분류"
        key = (
            result,
            self.floor_spin.value(),
            len(self.owned_gifts),
            text[:120],
        )
        now = time.time()
        if key == self.last_auto_run_key and now - self.last_auto_run_at < 900:
            return "run already saved"

        idx = self.run_result.findText(result)
        if idx >= 0:
            self.run_result.setCurrentIndex(idx)
        if not self.run_cause.text().strip():
            self.run_cause.setText(detected.get("cause") or "Mirror Dungeon result OCR")
        if not self.run_note.toPlainText().strip() and text:
            self.run_note.setPlainText(text[:300])

        payload = self.current_run_conditions()
        payload.update({
            "result": result,
            "difficulty": self.run_difficulty.currentText(),
            "deck": self.infer_run_deck(),
            "cause": self.run_cause.text().strip() or detected.get("cause") or "Mirror Dungeon result OCR",
            "note": self.run_note.toPlainText().strip(),
            "auto_detected": True,
            "ocr_text": text[:500],
        })
        ok = self.data.submit_run_result(payload)
        if ok:
            self.last_auto_run_key = key
            self.last_auto_run_at = now
            self.run_status.setText('Auto-saved run result')
            self.run_status.setStyleSheet('color: #4caf50; font-size: 8pt; border: none;')
            return "run auto-saved"
        self.run_status.setText('Auto-save failed')
        self.run_status.setStyleSheet('color: #ff5555; font-size: 8pt; border: none;')
        return "run save failed"

    def toggle_auto_watch(self, state):
        if state == Qt.Checked:
            self.auto_watch_timer.start()
            self.run_status.setText('Watching every 15s')
            self.run_status.setStyleSheet('color: #8b949e; font-size: 8pt; border: none;')
        else:
            self.auto_watch_timer.stop()
            self.run_status.setText('Watch stopped')
            self.run_status.setStyleSheet('color: #8b949e; font-size: 8pt; border: none;')

    def toggle_click_through(self):
        if sys.platform != 'win32':
            return
        hwnd = int(self.winId())
        self.click_through = not self.click_through
        if self.click_through:
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_TRANSPARENT | WS_EX_LAYERED)
            self.title_bar.pin_btn.setText(chr(0x1F513))
        else:
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style & ~WS_EX_TRANSPARENT)
            self.title_bar.pin_btn.setText(chr(0x1F4CC))

    def change_opacity(self, idx):
        self.setWindowOpacity([1.0, 0.9, 0.8, 0.7][idx])

    def search_gifts(self):
        self.search_results.clear()
        kw = self.keyword_combo.currentText()
        s = self.search_input.text().strip()
        for g in self.data.search_gifts(s, kw):
            dn = g.get('name_kr') or g.get('name')
            item = QListWidgetItem(f"[T{g.get('tier', '?')}] {dn}")
            item.setToolTip((g.get('simple_desc') or '')[:120])
            item.setData(Qt.UserRole, g)
            self.search_results.addItem(item)

    def add_to_owned(self, item):
        g = item.data(Qt.UserRole)
        was_recommended = bool(item.data(Qt.UserRole + 1))
        if self._add_owned_gift(g, was_recommended=was_recommended):
            self.status_label.setText("Added to owned")

    def remove_from_owned(self, item):
        row = self.owned_list.row(item)
        self.owned_list.takeItem(row)
        if row < len(self.owned_gifts):
            self.owned_gifts.pop(row)

    def get_recommendations(self):
        self.rec_list.clear()
        if not self.owned_gifts:
            self.rec_list.addItem("Add gifts first (Scan or Search)")
            return
        deck = self.pack_deck_combo.currentText()
        kw_summary, recs = self.data.recommend(self.owned_gifts, self.floor_spin.value(), deck)
        if not kw_summary:
            self.rec_list.addItem("No keyword synergy found")
            return
        h = QListWidgetItem(', '.join(f'{k}({v})' for k, v in kw_summary))
        h.setForeground(QColor('#4caf50'))
        self.rec_list.addItem(h)
        for g in recs:
            dn = g.get('name_kr') or g.get('name')
            item = QListWidgetItem(f"  [T{g.get('tier', '?')}] {dn}")
            item.setData(Qt.UserRole, g)
            item.setData(Qt.UserRole + 1, True)
            tip = g.get('reason') or g.get('simple_desc') or g.get('description') or ''
            item.setToolTip(tip[:240])
            self.rec_list.addItem(item)

    def on_floor_change(self, v):
        self.load_floor_recommendations()

    def load_floor_recommendations(self, *_):
        self.pack_list.clear()
        f = self.floor_spin.value()
        deck = self.pack_deck_combo.currentText()
        packs = self.data.floor_recommendations(f, deck)
        if not packs:
            self.pack_list.addItem("No pack guide for this filter")
            return
        for p in packs:
            h = f"[{p.get('floor_number')}F] {p.get('pack_name')}"
            if p.get('notes'):
                h += f" ({p['notes']})"
            item = QListWidgetItem(h)
            item.setForeground(QColor('#f8c200'))
            self.pack_list.addItem(item)
            if p.get('key_gifts'):
                self.pack_list.addItem(f"  {p['key_gifts']}")

    def load_formation(self):
        # 덱 목록 로드
        all_formations = self.data.formation()
        deck_names = []
        self._formations_by_deck = {}
        for f in all_formations:
            deck = f.get('deck_name') or '기본덱'
            if deck not in self._formations_by_deck:
                self._formations_by_deck[deck] = []
                deck_names.append(deck)
            self._formations_by_deck[deck].append(f)

        self.deck_combo.blockSignals(True)
        self.deck_combo.clear()
        self.deck_combo.addItems(deck_names)
        self.deck_combo.blockSignals(False)

        for combo in (self.pack_deck_combo, self.combo_deck_combo):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(["All"] + deck_names)
            combo.blockSignals(False)

        if deck_names:
            self.on_deck_changed(deck_names[0])
        self.load_floor_recommendations()
        self.load_combinations()

    def on_deck_changed(self, deck_name):
        formations = self._formations_by_deck.get(deck_name, [])
        self.persona_list.blockSignals(True)
        self.persona_list.clear()
        for f in formations:
            item = QListWidgetItem(f"{f.get('character_nickname')} ({f.get('character_name')})")
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, f)
            self.persona_list.addItem(item)
        self.persona_list.blockSignals(False)
        self.on_persona_changed()

    def on_persona_changed(self, *_):
        self.form_list.clear()
        for i in range(self.persona_list.count()):
            item = self.persona_list.item(i)
            if item.checkState() != Qt.Checked:
                continue
            f = item.data(Qt.UserRole)
            header = QListWidgetItem(f"{f.get('position', i+1)}. {f.get('character_nickname')} ({f.get('attack_type')})")
            header.setForeground(QColor('#f8c200'))
            self.form_list.addItem(header)
            guide = f.get('skill_exchange') or f.get('notes')
            if guide:
                self.form_list.addItem(f"  {guide}")

    def load_combinations(self, *_):
        self.combo_list.clear()
        deck = self.combo_deck_combo.currentText()
        combos = self.data.combinations(deck)
        if not combos:
            self.combo_list.addItem("No combinations for this filter")
            return
        for c in combos:
            title = c.get('result_gift')
            if deck == "All" and c.get('deck_name'):
                title = f"[{c.get('deck_name')}] {title}"
            item = QListWidgetItem(f"{title}")
            item.setForeground(QColor('#f8c200'))
            self.combo_list.addItem(item)
            if c.get('required_gifts'):
                self.combo_list.addItem(f"  = {c.get('required_gifts')}")
            if c.get('notes'):
                self.combo_list.addItem(f"  ({c.get('notes')})")

    def current_run_conditions(self):
        keywords = {}
        for name in self.owned_gifts:
            gift = self.data.gift_by_name(name)
            if not gift:
                continue
            for kw in (gift.get('keyword') or '').split(','):
                kw = kw.strip()
                if kw and kw != 'General':
                    keywords[kw] = keywords.get(kw, 0) + 1

        identities = []
        for i in range(self.persona_list.count()):
            item = self.persona_list.item(i)
            if item.checkState() != Qt.Checked:
                continue
            formation = item.data(Qt.UserRole) or {}
            name = formation.get('character_name') or ''
            nick = formation.get('character_nickname') or ''
            identities.append(f"{nick} ({name})".strip())

        return {
            "floor": self.floor_spin.value(),
            "gift_count": len(self.owned_gifts),
            "gifts": list(self.owned_gifts),
            "keywords": dict(sorted(keywords.items(), key=lambda x: -x[1])),
            "identity_count": len(identities),
            "identities": identities,
        }

    def infer_run_deck(self):
        manual = self.run_deck.text().strip()
        if manual:
            return manual

        for combo in (self.pack_deck_combo, self.deck_combo, self.combo_deck_combo):
            deck = combo.currentText().strip()
            if deck and deck != "All":
                return deck

        payload = self.current_run_conditions()
        keywords = payload.get("keywords") or {}
        if keywords:
            top = sorted(keywords.items(), key=lambda x: -x[1])[:3]
            return " / ".join(k for k, _ in top)
        return ""

    def send_run_result(self):
        payload = self.current_run_conditions()
        payload.update({
            "result": self.run_result.currentText(),
            "difficulty": self.run_difficulty.currentText(),
            "deck": self.infer_run_deck(),
            "cause": self.run_cause.text().strip(),
            "note": self.run_note.toPlainText().strip(),
        })
        ok = self.data.submit_run_result(payload)
        if ok:
            self.run_note.clear()
            self.run_status.setText('Run result saved')
            self.run_status.setStyleSheet('color: #4caf50; font-size: 8pt; border: none;')
        else:
            self.run_status.setText('Server save failed')
            self.run_status.setStyleSheet('color: #ff5555; font-size: 8pt; border: none;')

    def send_feedback(self):
        content = self.fb_text.toPlainText().strip()
        if not content:
            self.fb_status.setText('내용을 입력하세요.')
            self.fb_status.setStyleSheet('color: #ff5555; font-size: 8pt; border: none;')
            return
        ftype = self.fb_type.currentText()
        rating = int(self.fb_rating.currentText())
        ok = self.data.submit_feedback(ftype, content, rating)
        if ok:
            self.fb_text.clear()
            self.fb_status.setText('피드백 전송 완료. 감사합니다!')
            self.fb_status.setStyleSheet('color: #4caf50; font-size: 8pt; border: none;')
        else:
            self.fb_status.setText('서버 연결 실패 - 잠시 후 다시 시도하세요.')
            self.fb_status.setStyleSheet('color: #ff5555; font-size: 8pt; border: none;')


def main():
    import signal
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)
    t = MirrorDungeonTracker()
    t.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
