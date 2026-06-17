#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Translation Tool v2.1
Multi-language translation & Chinese dialect TTS
OA-style light theme UI
"""

import os
import sys
import tempfile
import asyncio
import threading
import json
import time
import random
from pathlib import Path

import customtkinter as ctk
from customtkinter import (
    CTk, CTkFrame, CTkButton, CTkLabel, CTkTextbox,
    CTkComboBox, CTkTabview, CTkSwitch,
)
from tkinter import messagebox
import tkinter as tk

import pygame

try:
    from PIL import Image, ImageDraw, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

try:
    import edge_tts
except ImportError:
    edge_tts = None

# ==================== OA Light Theme Colors ====================
SIDEBAR_BG = ("#ffffff", "#1e293b")
MAIN_BG = ("#f1f5f9", "#0f172a")
PANEL_BG = ("#ffffff", "#1e293b")
TEXTBOX_BG = ("#ffffff", "#334155")

TITLE_TEXT = ("#1e293b", "#e2e8f0")
SUBTITLE_TEXT = ("#64748b", "#94a3b8")
HEADER_TEXT = ("#0f172a", "#f8fafc")
BODY_TEXT = ("#334155", "#cbd5e1")
STATUS_TEXT = ("#94a3b8", "#64748b")

FONT_FAMILY = "Microsoft YaHei"
FONT_LOGO = (FONT_FAMILY, 24, "bold")
FONT_SUBLOGO = (FONT_FAMILY, 12)
FONT_HEADER = (FONT_FAMILY, 18, "bold")
FONT_LABEL_BOLD = (FONT_FAMILY, 12, "bold")
FONT_BODY = (FONT_FAMILY, 12)
FONT_SMALL = (FONT_FAMILY, 10)

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

# ==================== Language Data ====================
INTERNATIONAL_LANGS = {
    "Chinese(Simplified)":  {"code": "zh-CN", "tts": "zh-CN-XiaoxiaoNeural"},
    "Chinese(Traditional)": {"code": "zh-TW", "tts": "zh-TW-HsiaoChenNeural"},
    "English":              {"code": "en",    "tts": "en-US-AriaNeural"},
    "Spanish":              {"code": "es",    "tts": "es-ES-ElviraNeural"},
    "German":               {"code": "de",    "tts": "de-DE-KatjaNeural"},
    "French":               {"code": "fr",    "tts": "fr-FR-DeniseNeural"},
    "Russian":              {"code": "ru",    "tts": "ru-RU-SvetlanaNeural"},
    "Hindi":                {"code": "hi",    "tts": "hi-IN-MadhurNeural"},
    "Arabic":               {"code": "ar",    "tts": "ar-SA-ZariyahNeural"},
    "Bengali":              {"code": "bn",    "tts": "bn-IN-BashkarNeural"},
    "Portuguese":           {"code": "pt",    "tts": "pt-BR-FranciscaNeural"},
    "Urdu":                 {"code": "ur",    "tts": "ur-PK-AsadNeural"},
    "Japanese":             {"code": "ja",    "tts": "ja-JP-NanamiNeural"},
    "Korean":               {"code": "ko",    "tts": "ko-KR-SunHiNeural"},
    "Italian":              {"code": "it",    "tts": "it-IT-ElsaNeural"},
}

DIALECTS = {
    "Mandarin":   {"code": "zh-CN", "tts": "zh-CN-XiaoxiaoNeural"},
    "Cantonese":  {"code": "zh-CN", "tts": "zh-HK-HiuMaanNeural"},
    "Sichuan":    {"code": "zh-CN", "tts": "zh-CN-YunxiNeural"},
    "Shaanxi":    {"code": "zh-CN", "tts": "zh-CN-shaanxi-XiaoniNeural"},
    "Northeast":  {"code": "zh-CN", "tts": "zh-CN-liaoning-XiaobeiNeural"},
    "Taiwan":     {"code": "zh-TW", "tts": "zh-TW-HsiaoYuNeural"},
    "Minnan":     {"code": "zh-CN", "tts": "zh-CN-XiaoxiaoNeural"},
    "Jiangxi":    {"code": "zh-CN", "tts": "zh-CN-XiaoxiaoNeural"},
    "Tianjin":    {"code": "zh-CN", "tts": "zh-CN-XiaoxiaoNeural"},
}

TEXTS = {
    "zh_CN": {
        "title": "翻译与方言工具",
        "tab_intl": "国际翻译",
        "tab_dialect": "方言翻译",
        "source": "源语言",
        "target": "目标语言",
        "input_placeholder": "在此输入要翻译的文本...",
        "output_placeholder": "翻译结果将显示在这里...",
        "translate": "开始翻译",
        "swap": "交换",
        "play_source": "播放原文",
        "play_result": "播放译文",
        "clear": "清空",
        "copy": "复制结果",
        "hint": "提示",
        "please_input": "请输入要翻译的文本",
        "translating": "正在翻译...",
        "translate_done": "翻译完成",
        "translate_fail": "翻译失败",
        "playing": "正在播放...",
        "play_done": "播放完成",
        "dialect_note": "注：方言翻译基于标准中文识别，结果仅供参考",
        "no_network": "网络连接失败，请检查网络",
        "no_tts": "TTS引擎未安装，请安装 edge-tts",
        "theme": "外观主题",
        "dark_mode": "深色模式",
        "language": "界面语言",
        "restart_hint": "界面语言已更改，请重启应用生效",
        "lang_names": {
            "Chinese(Simplified)": "中文(简体)",
            "Chinese(Traditional)": "中文(繁体)",
            "Cantonese": "粤语",
            "English": "英语",
            "Spanish": "西班牙语",
            "German": "德语",
            "French": "法语",
            "Russian": "俄语",
            "Hindi": "印地语",
            "Arabic": "阿拉伯语",
            "Bengali": "孟加拉语",
            "Portuguese": "葡萄牙语",
            "Urdu": "乌尔都语",
            "Japanese": "日语",
            "Korean": "韩语",
            "Italian": "意大利语",
            "Mandarin": "普通话",
            "Sichuan": "四川话",
            "Shaanxi": "陕西话",
            "Northeast": "东北话",
            "Taiwan": "台湾国语",
            "Minnan": "闽南话",
            "Jiangxi": "江西话",
            "Tianjin": "天津话",
        },
    },
    "en": {
        "title": "Translation & Dialect Tool",
        "tab_intl": "International",
        "tab_dialect": "Dialect",
        "source": "Source",
        "target": "Target",
        "input_placeholder": "Enter text to translate...",
        "output_placeholder": "Translation will appear here...",
        "translate": "Translate",
        "swap": "Swap",
        "play_source": "Play Source",
        "play_result": "Play Result",
        "clear": "Clear",
        "copy": "Copy Result",
        "hint": "Hint",
        "please_input": "Please enter text to translate",
        "translating": "Translating...",
        "translate_done": "Translation complete",
        "translate_fail": "Translation failed",
        "playing": "Playing...",
        "play_done": "Playback complete",
        "dialect_note": "Note: Dialect translation uses standard Chinese recognition",
        "no_network": "Network error, please check your connection",
        "no_tts": "TTS engine not installed, please install edge-tts",
        "theme": "Theme",
        "dark_mode": "Dark Mode",
        "language": "UI Language",
        "restart_hint": "UI language changed. Please restart the app.",
        "lang_names": {
            "Chinese(Simplified)": "Chinese (Simplified)",
            "Chinese(Traditional)": "Chinese (Traditional)",
            "Cantonese": "Cantonese",
            "English": "English",
            "Spanish": "Spanish",
            "German": "German",
            "French": "French",
            "Russian": "Russian",
            "Hindi": "Hindi",
            "Arabic": "Arabic",
            "Bengali": "Bengali",
            "Portuguese": "Portuguese",
            "Urdu": "Urdu",
            "Japanese": "Japanese",
            "Korean": "Korean",
            "Italian": "Italian",
            "Mandarin": "Mandarin",
            "Sichuan": "Sichuan",
            "Shaanxi": "Shaanxi",
            "Northeast": "Northeast",
            "Taiwan": "Taiwan",
            "Minnan": "Minnan",
            "Jiangxi": "Jiangxi",
            "Tianjin": "Tianjin",
        },
    },
}

# ==================== Settings ====================
SETTINGS_FILE = "translation_settings.json"
DEFAULT_SETTINGS = {"language": "zh_CN", "theme": "Light"}


def _get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _settings_path():
    return os.path.join(_get_app_dir(), SETTINGS_FILE)


def load_settings():
    path = _settings_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                s = json.load(f)
            merged = DEFAULT_SETTINGS.copy()
            merged.update(s)
            return merged
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    path = _settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Save settings failed: {e}")


# ==================== Engines ====================
class TranslationEngine:
    """Translation wrapper"""
    @staticmethod
    def translate(text, source_code, target_code):
        if not GoogleTranslator:
            raise RuntimeError("deep-translator not installed")
        if not text or not text.strip():
            return ""
        try:
            translator = GoogleTranslator(source=source_code, target=target_code)
            return translator.translate(text)
        except Exception as e:
            raise RuntimeError(f"Translation failed: {e}")


class TTSEngine:
    """TTS wrapper using edge-tts + pygame"""
    _temp_dir = None
    _initialized = False

    @classmethod
    def init(cls):
        if not cls._initialized:
            pygame.mixer.init(frequency=24000, size=-16, channels=1)
            cls._temp_dir = os.path.join(tempfile.gettempdir(), "translation_tts")
            os.makedirs(cls._temp_dir, exist_ok=True)
            cls._initialized = True

    @classmethod
    async def _generate_async(cls, text, voice, out_path):
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(out_path)

    @classmethod
    def generate(cls, text, voice):
        if not edge_tts:
            raise RuntimeError("edge-tts not installed")
        cls.init()
        safe_text = text[:100] if text else "no text"
        filename = f"tts_{voice}_{hash(safe_text)}_{int(time.time()*1000)}.mp3"
        out_path = os.path.join(cls._temp_dir, filename)
        asyncio.run(cls._generate_async(text, voice, out_path))
        return out_path

    @classmethod
    def play(cls, audio_path, on_finish=None):
        cls.init()
        if not os.path.exists(audio_path):
            return
        def _play_worker():
            try:
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                if on_finish:
                    on_finish()
            except Exception as e:
                print(f"TTS play error: {e}")
                if on_finish:
                    on_finish()
        threading.Thread(target=_play_worker, daemon=True).start()

    @classmethod
    def stop(cls):
        if cls._initialized:
            pygame.mixer.music.stop()


# ==================== Main App ====================
class TranslationToolApp(CTk):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.lang = self.settings.get("language", "zh_CN")
        theme = self.settings.get("theme", "Light")
        if theme in ("Light", "Dark", "System"):
            ctk.set_appearance_mode(theme)

        self._bg_photo = None
        self._bg_label = None
        self._bg_job = None

        self._configure_window()
        self._init_ui()
        TTSEngine.init()
        self.after(200, self._draw_background)

    def _t(self, key):
        return TEXTS.get(self.lang, TEXTS["zh_CN"]).get(key, key)

    def _get_lang_display_name(self, key):
        names = self._t("lang_names")
        if isinstance(names, dict):
            return names.get(key, key)
        return key

    def _get_lang_key_from_display(self, display_name):
        names = self._t("lang_names")
        if isinstance(names, dict):
            for k, v in names.items():
                if v == display_name:
                    return k
        return display_name

    def _configure_window(self):
        self.title(self._t("title"))
        self.geometry("1200x800")
        self.minsize(1000, 700)

    # ---------- Background ----------
    def _draw_background(self):
        if not PIL_AVAILABLE:
            return
        width = self.winfo_width()
        height = self.winfo_height()
        if width < 200 or height < 200:
            return

        mode = ctk.get_appearance_mode()
        if mode == "Dark":
            top = (15, 23, 42)
            bot = (30, 41, 59)
            line = (51, 65, 85)
        else:
            top = (241, 245, 249)
            bot = (248, 250, 252)
            line = (226, 232, 240)

        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        # Very subtle gradient
        for y in range(height):
            r = int(top[0] + (bot[0] - top[0]) * y / height)
            g = int(top[1] + (bot[1] - top[1]) * y / height)
            b = int(top[2] + (bot[2] - top[2]) * y / height)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Subtle horizontal accent lines
        rng = random.Random(42)
        for _ in range(5):
            y = rng.randint(80, height - 80)
            draw.line([(0, y), (width, y)], fill=line, width=1)

        self._bg_photo = ImageTk.PhotoImage(img)
        if self._bg_label is None:
            self._bg_label = tk.Label(self, image=self._bg_photo)
            self._bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            self._bg_label.lower()
        else:
            self._bg_label.configure(image=self._bg_photo)

    def _on_resize(self, event):
        if event.widget is not self:
            return
        if self._bg_job:
            self.after_cancel(self._bg_job)
        self._bg_job = self.after(300, self._draw_background)

    # ---------- UI Building ----------
    def _init_ui(self):
        self.bind("<Configure>", self._on_resize)

        # ---- Sidebar ----
        self.sidebar = CTkFrame(self, width=200, corner_radius=0, fg_color=SIDEBAR_BG)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        CTkLabel(self.sidebar, text="Translate", font=FONT_LOGO, text_color=TITLE_TEXT).pack(pady=(30, 5))
        CTkLabel(self.sidebar, text="Multi-language", font=FONT_SUBLOGO, text_color=SUBTITLE_TEXT).pack()

        CTkLabel(self.sidebar, text=self._t("theme"), font=FONT_LABEL_BOLD, text_color=TITLE_TEXT).pack(pady=(30, 5), padx=20, anchor="w")
        self.theme_switch = CTkSwitch(self.sidebar, text=self._t("dark_mode"), font=FONT_BODY, command=self._toggle_theme)
        self.theme_switch.pack(pady=5, padx=20, anchor="w")
        self.theme_switch.select() if ctk.get_appearance_mode() == "Dark" else self.theme_switch.deselect()

        CTkLabel(self.sidebar, text=self._t("language"), font=FONT_LABEL_BOLD, text_color=TITLE_TEXT).pack(pady=(20, 5), padx=20, anchor="w")
        self.lang_combo = CTkComboBox(self.sidebar, values=["zh_CN", "en"], command=self._change_ui_lang, width=140, font=FONT_BODY)
        self.lang_combo.set(self.lang)
        self.lang_combo.pack(pady=5, padx=20, anchor="w")

        CTkLabel(self.sidebar, text="v2.1", font=FONT_SMALL, text_color="gray").pack(side="bottom", pady=20)

        # ---- Main Frame ----
        self.main_frame = CTkFrame(self, fg_color=MAIN_BG)
        self.main_frame.pack(side="left", fill="both", expand=True, padx=(0, 20), pady=20)

        CTkLabel(self.main_frame, text=self._t("title"), font=FONT_HEADER, text_color=HEADER_TEXT).pack(anchor="w", padx=10, pady=(0, 10))

        self.tabview = CTkTabview(
            self.main_frame,
            fg_color=PANEL_BG,
            segmented_button_fg_color=MAIN_BG,
            segmented_button_selected_color=("#3b82f6", "#3b82f6"),
            segmented_button_selected_hover_color=("#2563eb", "#2563eb"),
            segmented_button_unselected_color=("#e2e8f0", "#475569"),
            segmented_button_unselected_hover_color=("#cbd5e1", "#64748b"),
            text_color=BODY_TEXT,
        )
        self.tabview.pack(fill="both", expand=True)
        self.tabview.add(self._t("tab_intl"))
        self.tabview.add(self._t("tab_dialect"))
        self._build_intl_tab()
        self._build_dialect_tab()

    def _build_intl_tab(self):
        tab = self.tabview.tab(self._t("tab_intl"))
        tab.configure(fg_color=PANEL_BG)

        # Language selection row
        lang_row = CTkFrame(tab, fg_color=PANEL_BG, corner_radius=8, border_width=1, border_color=("#e2e8f0", "#475569"))
        lang_row.pack(fill="x", pady=(15, 10), padx=10)

        CTkLabel(lang_row, text=self._t("source"), font=FONT_LABEL_BOLD, text_color=TITLE_TEXT).pack(side="left", padx=(15, 8))

        intl_names = [self._get_lang_display_name(k) for k in INTERNATIONAL_LANGS.keys()]
        combo_opts = {
            "fg_color": TEXTBOX_BG,
            "border_color": ("#94a3b8", "#475569"),
            "border_width": 1,
            "button_color": ("#64748b", "#475569"),
            "button_hover_color": ("#475569", "#64748b"),
            "dropdown_fg_color": TEXTBOX_BG,
            "dropdown_text_color": BODY_TEXT,
            "dropdown_hover_color": ("#e2e8f0", "#334155"),
        }
        self.intl_src_combo = CTkComboBox(lang_row, values=intl_names, width=180, font=FONT_BODY, **combo_opts)
        self.intl_src_combo.set(self._get_lang_display_name("Chinese(Simplified)"))
        self.intl_src_combo.pack(side="left", padx=5)

        CTkButton(lang_row, text=self._t("swap"), width=70, font=FONT_BODY, command=self._swap_intl).pack(side="left", padx=15)

        CTkLabel(lang_row, text=self._t("target"), font=FONT_LABEL_BOLD, text_color=TITLE_TEXT).pack(side="left", padx=(0, 8))

        self.intl_tgt_combo = CTkComboBox(lang_row, values=intl_names, width=180, font=FONT_BODY, **combo_opts)
        self.intl_tgt_combo.set(self._get_lang_display_name("English"))
        self.intl_tgt_combo.pack(side="left", padx=5)

        # Text areas
        text_row = CTkFrame(tab, fg_color="transparent")
        text_row.pack(fill="both", expand=True, pady=5, padx=10)
        text_row.grid_columnconfigure(0, weight=1)
        text_row.grid_columnconfigure(1, weight=1)
        text_row.grid_rowconfigure(0, weight=1)

        # Source panel
        src_panel = CTkFrame(text_row, fg_color=PANEL_BG, corner_radius=8, border_width=1, border_color=("#e2e8f0", "#475569"))
        src_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        src_panel.grid_rowconfigure(1, weight=1)
        src_panel.grid_columnconfigure(0, weight=1)

        CTkLabel(src_panel, text=self._t("source"), font=FONT_LABEL_BOLD, text_color=SUBTITLE_TEXT).grid(row=0, column=0, sticky="nw", padx=10, pady=(8, 0))
        self.intl_src_text = CTkTextbox(src_panel, wrap="word", fg_color=TEXTBOX_BG, text_color=BODY_TEXT, font=FONT_BODY, border_color=("#cbd5e1", "#475569"), border_width=1)
        self.intl_src_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.intl_src_text.insert("1.0", self._t("input_placeholder"))
        CTkButton(src_panel, text=self._t("play_source"), font=FONT_BODY, width=120,
                  command=lambda: self._play_tts(self.intl_src_text, self.intl_src_combo, INTERNATIONAL_LANGS)).grid(row=2, column=0, pady=(0, 10))

        # Target panel
        tgt_panel = CTkFrame(text_row, fg_color=PANEL_BG, corner_radius=8, border_width=1, border_color=("#e2e8f0", "#475569"))
        tgt_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        tgt_panel.grid_rowconfigure(1, weight=1)
        tgt_panel.grid_columnconfigure(0, weight=1)

        CTkLabel(tgt_panel, text=self._t("target"), font=FONT_LABEL_BOLD, text_color=SUBTITLE_TEXT).grid(row=0, column=0, sticky="nw", padx=10, pady=(8, 0))
        self.intl_tgt_text = CTkTextbox(tgt_panel, wrap="word", fg_color=TEXTBOX_BG, text_color=BODY_TEXT, font=FONT_BODY, border_color=("#cbd5e1", "#475569"), border_width=1)
        self.intl_tgt_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.intl_tgt_text.insert("1.0", self._t("output_placeholder"))
        self.intl_tgt_text.configure(state="disabled")
        CTkButton(tgt_panel, text=self._t("play_result"), font=FONT_BODY, width=120,
                  command=lambda: self._play_tts(self.intl_tgt_text, self.intl_tgt_combo, INTERNATIONAL_LANGS)).grid(row=2, column=0, pady=(0, 10))

        # Buttons row
        btn_row = CTkFrame(tab, fg_color="transparent")
        btn_row.pack(fill="x", pady=(5, 10), padx=10)

        CTkButton(btn_row, text=self._t("clear"), font=FONT_BODY, width=100,
                  command=lambda: self._clear(self.intl_src_text, self.intl_tgt_text)).pack(side="left", padx=5)
        CTkButton(btn_row, text=self._t("copy"), font=FONT_BODY, width=120,
                  command=lambda: self._copy(self.intl_tgt_text)).pack(side="left", padx=5)
        self.intl_translate_btn = CTkButton(btn_row, text=self._t("translate"), font=FONT_BODY, width=140,
                                            fg_color="#3b82f6", hover_color="#2563eb",
                                            command=self._do_intl_translate)
        self.intl_translate_btn.pack(side="right", padx=5)

        self.intl_status = CTkLabel(tab, text="", text_color=STATUS_TEXT, font=FONT_SMALL)
        self.intl_status.pack(anchor="w", padx=10, pady=(0, 10))

    def _build_dialect_tab(self):
        tab = self.tabview.tab(self._t("tab_dialect"))
        tab.configure(fg_color=PANEL_BG)

        lang_row = CTkFrame(tab, fg_color=PANEL_BG, corner_radius=8, border_width=1, border_color=("#e2e8f0", "#475569"))
        lang_row.pack(fill="x", pady=(15, 10), padx=10)

        CTkLabel(lang_row, text=self._t("source"), font=FONT_LABEL_BOLD, text_color=TITLE_TEXT).pack(side="left", padx=(15, 8))

        dia_names = [self._get_lang_display_name(k) for k in DIALECTS.keys()]
        combo_opts = {
            "fg_color": TEXTBOX_BG,
            "border_color": ("#94a3b8", "#475569"),
            "border_width": 1,
            "button_color": ("#64748b", "#475569"),
            "button_hover_color": ("#475569", "#64748b"),
            "dropdown_fg_color": TEXTBOX_BG,
            "dropdown_text_color": BODY_TEXT,
            "dropdown_hover_color": ("#e2e8f0", "#334155"),
        }
        self.dia_src_combo = CTkComboBox(lang_row, values=dia_names, width=180, font=FONT_BODY, **combo_opts)
        self.dia_src_combo.set(self._get_lang_display_name("Mandarin"))
        self.dia_src_combo.pack(side="left", padx=5)

        CTkButton(lang_row, text=self._t("swap"), width=70, font=FONT_BODY, command=self._swap_dialect).pack(side="left", padx=15)

        CTkLabel(lang_row, text=self._t("target"), font=FONT_LABEL_BOLD, text_color=TITLE_TEXT).pack(side="left", padx=(0, 8))

        self.dia_tgt_combo = CTkComboBox(lang_row, values=dia_names, width=180, font=FONT_BODY, **combo_opts)
        self.dia_tgt_combo.set(self._get_lang_display_name("Cantonese"))
        self.dia_tgt_combo.pack(side="left", padx=5)

        # Text areas
        text_row = CTkFrame(tab, fg_color="transparent")
        text_row.pack(fill="both", expand=True, pady=5, padx=10)
        text_row.grid_columnconfigure(0, weight=1)
        text_row.grid_columnconfigure(1, weight=1)
        text_row.grid_rowconfigure(0, weight=1)

        src_panel = CTkFrame(text_row, fg_color=PANEL_BG, corner_radius=8, border_width=1, border_color=("#e2e8f0", "#475569"))
        src_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        src_panel.grid_rowconfigure(1, weight=1)
        src_panel.grid_columnconfigure(0, weight=1)

        CTkLabel(src_panel, text=self._t("source"), font=FONT_LABEL_BOLD, text_color=SUBTITLE_TEXT).grid(row=0, column=0, sticky="nw", padx=10, pady=(8, 0))
        self.dia_src_text = CTkTextbox(src_panel, wrap="word", fg_color=TEXTBOX_BG, text_color=BODY_TEXT, font=FONT_BODY, border_color=("#cbd5e1", "#475569"), border_width=1)
        self.dia_src_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.dia_src_text.insert("1.0", self._t("input_placeholder"))
        CTkButton(src_panel, text=self._t("play_source"), font=FONT_BODY, width=120,
                  command=lambda: self._play_tts(self.dia_src_text, self.dia_src_combo, DIALECTS)).grid(row=2, column=0, pady=(0, 10))

        tgt_panel = CTkFrame(text_row, fg_color=PANEL_BG, corner_radius=8, border_width=1, border_color=("#e2e8f0", "#475569"))
        tgt_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        tgt_panel.grid_rowconfigure(1, weight=1)
        tgt_panel.grid_columnconfigure(0, weight=1)

        CTkLabel(tgt_panel, text=self._t("target"), font=FONT_LABEL_BOLD, text_color=SUBTITLE_TEXT).grid(row=0, column=0, sticky="nw", padx=10, pady=(8, 0))
        self.dia_tgt_text = CTkTextbox(tgt_panel, wrap="word", fg_color=TEXTBOX_BG, text_color=BODY_TEXT, font=FONT_BODY, border_color=("#cbd5e1", "#475569"), border_width=1)
        self.dia_tgt_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.dia_tgt_text.insert("1.0", self._t("output_placeholder"))
        self.dia_tgt_text.configure(state="disabled")
        CTkButton(tgt_panel, text=self._t("play_result"), font=FONT_BODY, width=120,
                  command=lambda: self._play_tts(self.dia_tgt_text, self.dia_tgt_combo, DIALECTS)).grid(row=2, column=0, pady=(0, 10))

        # Buttons row
        btn_row = CTkFrame(tab, fg_color="transparent")
        btn_row.pack(fill="x", pady=(5, 10), padx=10)

        CTkButton(btn_row, text=self._t("clear"), font=FONT_BODY, width=100,
                  command=lambda: self._clear(self.dia_src_text, self.dia_tgt_text)).pack(side="left", padx=5)
        CTkButton(btn_row, text=self._t("copy"), font=FONT_BODY, width=120,
                  command=lambda: self._copy(self.dia_tgt_text)).pack(side="left", padx=5)
        self.dia_translate_btn = CTkButton(btn_row, text=self._t("translate"), font=FONT_BODY, width=140,
                                           fg_color="#3b82f6", hover_color="#2563eb",
                                           command=self._do_dialect_translate)
        self.dia_translate_btn.pack(side="right", padx=5)

        self.dia_status = CTkLabel(tab, text=self._t("dialect_note"), text_color=STATUS_TEXT, font=FONT_SMALL)
        self.dia_status.pack(anchor="w", padx=10, pady=(0, 10))

    # ---------- Actions ----------
    def _do_intl_translate(self):
        text = self.intl_src_text.get("1.0", "end").strip()
        if not text or text == self._t("input_placeholder"):
            messagebox.showwarning(self._t("hint"), self._t("please_input"))
            return
        src_name = self._get_lang_key_from_display(self.intl_src_combo.get())
        tgt_name = self._get_lang_key_from_display(self.intl_tgt_combo.get())
        src_code = INTERNATIONAL_LANGS[src_name]["code"]
        tgt_code = INTERNATIONAL_LANGS[tgt_name]["code"]
        self.intl_status.configure(text=self._t("translating"))
        self.intl_translate_btn.configure(state="disabled")
        def _worker():
            try:
                result = TranslationEngine.translate(text, src_code, tgt_code)
                self.after(0, lambda: self._set_result(self.intl_tgt_text, result, self.intl_status, self.intl_translate_btn))
            except Exception as e:
                self.after(0, lambda: self._set_error(self.intl_status, str(e), self.intl_translate_btn))
        threading.Thread(target=_worker, daemon=True).start()

    def _do_dialect_translate(self):
        text = self.dia_src_text.get("1.0", "end").strip()
        if not text or text == self._t("input_placeholder"):
            messagebox.showwarning(self._t("hint"), self._t("please_input"))
            return
        src_name = self._get_lang_key_from_display(self.dia_src_combo.get())
        tgt_name = self._get_lang_key_from_display(self.dia_tgt_combo.get())
        src_code = DIALECTS[src_name]["code"]
        tgt_code = DIALECTS[tgt_name]["code"]
        self.dia_status.configure(text=self._t("translating"))
        self.dia_translate_btn.configure(state="disabled")
        def _worker():
            try:
                result = TranslationEngine.translate(text, src_code, tgt_code)
                self.after(0, lambda: self._set_result(self.dia_tgt_text, result, self.dia_status, self.dia_translate_btn))
            except Exception as e:
                self.after(0, lambda: self._set_error(self.dia_status, str(e), self.dia_translate_btn))
        threading.Thread(target=_worker, daemon=True).start()

    def _set_result(self, textbox, result, status_label, btn):
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", result)
        textbox.configure(state="disabled")
        status_label.configure(text=self._t("translate_done"))
        btn.configure(state="normal")

    def _set_error(self, status_label, error, btn):
        status_label.configure(text=f"{self._t('translate_fail')}: {error}")
        btn.configure(state="normal")

    def _play_tts(self, textbox, combo, lang_map):
        text = textbox.get("1.0", "end").strip()
        if not text:
            return
        display_name = combo.get()
        name = self._get_lang_key_from_display(display_name)
        voice = lang_map[name]["tts"]
        tab = self._get_current_tab_status()
        tab.configure(text=self._t("playing"))
        def _worker():
            try:
                path = TTSEngine.generate(text, voice)
                TTSEngine.play(path, on_finish=lambda: self.after(0, lambda: tab.configure(text=self._t("play_done"))))
            except Exception as e:
                self.after(0, lambda: tab.configure(text=f"TTS Error: {e}"))
        threading.Thread(target=_worker, daemon=True).start()

    def _get_current_tab_status(self):
        current = self.tabview.get()
        if current == self._t("tab_intl"):
            return self.intl_status
        return self.dia_status

    def _swap_intl(self):
        s = self.intl_src_combo.get()
        t = self.intl_tgt_combo.get()
        self.intl_src_combo.set(t)
        self.intl_tgt_combo.set(s)

    def _swap_dialect(self):
        s = self.dia_src_combo.get()
        t = self.dia_tgt_combo.get()
        self.dia_src_combo.set(t)
        self.dia_tgt_combo.set(s)

    def _clear(self, src, tgt):
        src.delete("1.0", "end")
        tgt.configure(state="normal")
        tgt.delete("1.0", "end")
        tgt.configure(state="disabled")

    def _copy(self, tgt):
        text = tgt.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._get_current_tab_status().configure(text="Copied!")

    def _toggle_theme(self):
        mode = "Dark" if self.theme_switch.get() else "Light"
        ctk.set_appearance_mode(mode)
        self.settings["theme"] = mode
        save_settings(self.settings)
        self.after(200, self._draw_background)

    def _change_ui_lang(self, choice):
        self.settings["language"] = choice
        save_settings(self.settings)
        messagebox.showinfo(self._t("hint"), self._t("restart_hint"))


def main():
    app = TranslationToolApp()
    app.mainloop()


if __name__ == "__main__":
    main()
