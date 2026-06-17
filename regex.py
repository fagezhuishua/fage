#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正则表达式验证工具 - Modern GUI Edition (customtkinter)
功能：
1. 支持多种预设正则模板（IP、域名、URL、UA、邮箱等）
2. 实时正则匹配验证，区分编译错误 / 匹配成功 / 未匹配
3. 高亮显示匹配结果，未匹配时给出明确提示
4. 支持 Python re 标志位配置
5. 现代化界面，支持深色/浅色主题切换
6. 支持多语言（中文 / 英文）
7. 支持设置：字体颜色/大小、边框颜色/粗细
"""

import re
import json
import os
import customtkinter as ctk
from customtkinter import (
    CTk, CTkFrame, CTkButton, CTkLabel, CTkTextbox,
    CTkComboBox, CTkSwitch, CTkEntry, CTkCheckBox,
    CTkToplevel, CTkSlider,
)
from tkinter import messagebox, colorchooser

# 全局外观设置
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# ==================== 配置与多语言 ====================

SETTINGS_FILE = "regex_tool_settings.json"

DEFAULT_SETTINGS = {
    "language": "zh_CN",
    "font_size": 13,
    "font_color_light": "#000000",
    "font_color_dark": "#ffffff",
    "border_color_light": "#cccccc",
    "border_color_dark": "#333333",
    "border_width": 1,
}

TEXTS = {
    "zh_CN": {
        "app_title": "正则验证工具",
        "sidebar_title": "Regex Lab",
        "sidebar_subtitle": "正则表达式验证工作台",
        "preset": "预设模板",
        "run_match": "运行匹配",
        "clear_all": "清空全部",
        "paste_sample": "粘贴示例",
        "settings": "⚙️ 设置",
        "theme": "外观主题",
        "dark_mode": "深色模式",
        "version": "v1.1  Settings Edition",
        "workbench": "正则表达式匹配工作台",
        "regex_input": "🔧 正则表达式",
        "ignore_case": "忽略大小写",
        "multiline": "多行模式",
        "dotall": ".匹配换行",
        "regex_placeholder": "在此输入正则表达式...",
        "content_input": "📝 测试内容（每行一条）",
        "content_placeholder": "在此粘贴待匹配的文本内容，每行一条...",
        "result": "✅ 匹配结果",
        "waiting": "等待输入...",
        "empty_regex": "请输入正则表达式",
        "empty_content": "测试内容为空",
        "compile_error": "❌ 正则编译错误:\n{}",
        "error_at_pos": "\n👉 错误位置: 第 {} 个字符附近",
        "match_success": "✅ {}",
        "match_fail": "❌ {}   ⬅ 未匹配",
        "capture": "   └─ 捕获组: {}",
        "match_stat": "匹配: {} / 未匹配: {} / 总计: {}",
        "ready": "就绪",
        "cleared": "已清空",
        "pasted_sample": "已填入手机号验证示例",
        "settings_title": "设置",
        "language": "界面语言",
        "font_size": "字体大小",
        "font_color_light": "浅色模式字体颜色",
        "font_color_dark": "深色模式字体颜色",
        "border_color_light": "浅色模式边框颜色",
        "border_color_dark": "深色模式边框颜色",
        "border_width": "边框粗细",
        "choose_color": "选择颜色",
        "save": "保存",
        "cancel": "取消",
        "restart_required": "语言设置已更改，重启程序后生效。",
        "match": "匹配",
        "no_match": "未匹配",
        "compile_fail": "编译失败",
    },
    "en": {
        "app_title": "Regex Validator",
        "sidebar_title": "Regex Lab",
        "sidebar_subtitle": "Regex Expression Workbench",
        "preset": "Presets",
        "run_match": "Run Match",
        "clear_all": "Clear All",
        "paste_sample": "Paste Sample",
        "settings": "⚙️ Settings",
        "theme": "Theme",
        "dark_mode": "Dark Mode",
        "version": "v1.1  Settings Edition",
        "workbench": "Regex Matching Workbench",
        "regex_input": "🔧 Regex Pattern",
        "ignore_case": "Ignore Case",
        "multiline": "Multiline",
        "dotall": "Dot matches newline",
        "regex_placeholder": "Enter regex pattern here...",
        "content_input": "📝 Test Content (one per line)",
        "content_placeholder": "Paste test content here, one item per line...",
        "result": "✅ Match Results",
        "waiting": "Waiting for input...",
        "empty_regex": "Please enter a regex pattern",
        "empty_content": "Test content is empty",
        "compile_error": "❌ Regex Compile Error:\n{}",
        "error_at_pos": "\n👉 Error near position: {}",
        "match_success": "✅ {}",
        "match_fail": "❌ {}   ⬅ No match",
        "capture": "   └─ Captured: {}",
        "match_stat": "Matched: {} / Unmatched: {} / Total: {}",
        "ready": "Ready",
        "cleared": "Cleared",
        "pasted_sample": "Sample phone number pattern pasted",
        "settings_title": "Settings",
        "language": "Language",
        "font_size": "Font Size",
        "font_color_light": "Light Mode Font Color",
        "font_color_dark": "Dark Mode Font Color",
        "border_color_light": "Light Mode Border Color",
        "border_color_dark": "Dark Mode Border Color",
        "border_width": "Border Width",
        "choose_color": "Choose Color",
        "save": "Save",
        "cancel": "Cancel",
        "restart_required": "Language changed. Please restart the application.",
        "match": "Match",
        "no_match": "No Match",
        "compile_fail": "Compile Failed",
    }
}

# ==================== 预设正则模板 ====================
PRESETS = {
    "Custom / 自定义": "",
    "IPv4 Address": r"^(?:(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)$",
    "IPv6 Address": r"^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::$",
    "Domain Name": r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$",
    "URL": r"^https?://(?:[\w-]+\.)+[\w-]+(?:/[\w./?%&=]*)?$",
    "Email": r"^[\w.-]+@[\w.-]+\.\w+$",
    "China Mobile": r"^1[3-9]\d{9}$",
    "China ID Card": r"^\d{6}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]$",
    "User-Agent": r"Mozilla/[\d.]+\s+\([^)]+\)",
    "MAC Address": r"^(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$",
    "Port Number": r"^([1-9]\d{0,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])$",
}


def _settings_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), SETTINGS_FILE)


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


class SettingsWindow(CTkToplevel):
    """设置窗口"""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.settings = parent.settings.copy()
        self.lang_changed = False

        self.title(parent._t("settings_title"))
        self.geometry("520x620")
        self.minsize(450, 500)
        self.transient(parent)
        self.grab_set()
        self.focus_force()
        self.lift()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()

    def _build_ui(self):
        header = CTkFrame(self, height=50, corner_radius=0, fg_color=("gray90", "gray13"))
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        CTkLabel(header, text=self.parent._t("settings_title"), font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20, pady=10)

        content = CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=15)

        # 语言
        self._add_label(content, self.parent._t("language"))
        self.lang_combo = CTkComboBox(content, values=["zh_CN", "en"], state="readonly", width=200)
        self.lang_combo.set(self.settings["language"])
        self.lang_combo.pack(anchor="w", pady=(0, 12))

        # 字体大小
        self._add_label(content, self.parent._t("font_size"))
        size_frame = CTkFrame(content, fg_color="transparent")
        size_frame.pack(fill="x", pady=(0, 12))
        self.size_slider = CTkSlider(size_frame, from_=10, to=20, number_of_steps=10, width=200)
        self.size_slider.set(self.settings["font_size"])
        self.size_slider.pack(side="left")
        self.size_label = CTkLabel(size_frame, text=str(int(self.settings["font_size"])), width=30)
        self.size_label.pack(side="left", padx=(10, 0))
        self.size_slider.configure(command=lambda v: self.size_label.configure(text=str(int(float(v)))))

        # 颜色行
        self._add_color_row(content, self.parent._t("font_color_light"), "font_color_light")
        self._add_color_row(content, self.parent._t("font_color_dark"), "font_color_dark")
        self._add_color_row(content, self.parent._t("border_color_light"), "border_color_light")
        self._add_color_row(content, self.parent._t("border_color_dark"), "border_color_dark")

        # 边框粗细
        self._add_label(content, self.parent._t("border_width"))
        bw_frame = CTkFrame(content, fg_color="transparent")
        bw_frame.pack(fill="x", pady=(0, 12))
        self.bw_slider = CTkSlider(bw_frame, from_=0, to=3, number_of_steps=3, width=200)
        self.bw_slider.set(self.settings["border_width"])
        self.bw_slider.pack(side="left")
        self.bw_label = CTkLabel(bw_frame, text=str(int(self.settings["border_width"])), width=30)
        self.bw_label.pack(side="left", padx=(10, 0))
        self.bw_slider.configure(command=lambda v: self.bw_label.configure(text=str(int(float(v)))))

        # 预览
        preview_card = CTkFrame(content, corner_radius=12, fg_color=("gray90", "gray17"))
        preview_card.pack(fill="x", pady=(10, 0))
        CTkLabel(preview_card, text="Preview / 预览", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10, 5))
        self.preview_text = CTkTextbox(
            preview_card, height=60, wrap="word",
            font=ctk.CTkFont(family="Consolas", size=self.settings["font_size"]),
            text_color=(self.settings["font_color_light"], self.settings["font_color_dark"]),
            border_color=(self.settings["border_color_light"], self.settings["border_color_dark"]),
            border_width=self.settings["border_width"],
        )
        self.preview_text.pack(fill="x", padx=12, pady=(0, 12))
        self.preview_text.insert("0.0", "192.168.1.1 / 255.255.255.0")
        self.preview_text.configure(state="disabled")

        # 底部按钮
        bottom = CTkFrame(self, height=50, fg_color="transparent")
        bottom.pack(fill="x", padx=20, pady=(0, 15))
        bottom.pack_propagate(False)
        CTkButton(bottom, text=self.parent._t("save"), width=100, command=self._save).pack(side="right", padx=(5, 0))
        CTkButton(bottom, text=self.parent._t("cancel"), width=100, fg_color="transparent", border_width=1,
                  hover_color=("gray85", "gray25"), command=self._on_close).pack(side="right", padx=(5, 0))

        for widget in (self.size_slider, self.bw_slider):
            widget.configure(command=lambda v, w=widget: self._update_preview())

    def _add_label(self, parent, text):
        CTkLabel(parent, text=text, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(8, 4))

    def _add_color_row(self, parent, label, key):
        row = CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 8))
        CTkLabel(row, text=label, font=ctk.CTkFont(size=13)).pack(side="left")
        color_btn = CTkButton(row, text=self.parent._t("choose_color"), width=90, height=28,
                              command=lambda k=key: self._pick_color(k))
        color_btn.pack(side="right")
        preview = CTkFrame(row, width=28, height=28, corner_radius=6, fg_color=self.settings[key])
        preview.pack(side="right", padx=(0, 8))
        preview.pack_propagate(False)
        setattr(self, f"_{key}_preview", preview)

    def _pick_color(self, key):
        current = self.settings.get(key, "#000000")
        result = colorchooser.askcolor(color=current, title=self.parent._t("choose_color"))
        if result and result[1]:
            self.settings[key] = result[1]
            preview = getattr(self, f"_{key}_preview", None)
            if preview:
                preview.configure(fg_color=result[1])
            self._update_preview()

    def _update_preview(self):
        self.preview_text.configure(state="normal")
        self.preview_text.configure(
            font=ctk.CTkFont(family="Consolas", size=int(self.size_slider.get())),
            text_color=(self.settings["font_color_light"], self.settings["font_color_dark"]),
            border_color=(self.settings["border_color_light"], self.settings["border_color_dark"]),
            border_width=int(self.bw_slider.get()),
        )
        self.preview_text.configure(state="disabled")

    def _save(self):
        old_lang = self.parent.settings.get("language")
        new_lang = self.lang_combo.get()
        if old_lang != new_lang:
            self.lang_changed = True

        self.parent.settings["language"] = new_lang
        self.parent.settings["font_size"] = int(self.size_slider.get())
        self.parent.settings["border_width"] = int(self.bw_slider.get())
        save_settings(self.parent.settings)
        self.parent.apply_settings()
        self.parent.status_label.configure(text=self.parent._t("save"))
        if self.lang_changed:
            messagebox.showinfo(self.parent._t("settings_title"), self.parent._t("restart_required"))
        self._on_close()

    def _on_close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


class RegexToolApp(CTk):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.textboxes = []

        self.title(self._t("app_title"))
        self.geometry("1200x820")
        self.minsize(1000, 700)

        self._compile_error = None
        self._settings_window = None

        self._build_sidebar()
        self._build_main_area()
        self.apply_settings()

    def _t(self, key, *args):
        lang = self.settings.get("language", "zh_CN")
        text = TEXTS.get(lang, TEXTS["zh_CN"]).get(key, key)
        if args:
            return text.format(*args)
        return text

    def apply_settings(self):
        font = ctk.CTkFont(family="Consolas", size=self.settings["font_size"])
        text_color = (self.settings["font_color_light"], self.settings["font_color_dark"])
        border_color = (self.settings["border_color_light"], self.settings["border_color_dark"])
        bw = self.settings["border_width"]
        for tb in self.textboxes:
            try:
                tb.configure(font=font, text_color=text_color, border_color=border_color, border_width=bw)
            except Exception:
                pass

    def _register_textbox(self, tb):
        self.textboxes.append(tb)
        return tb

    def _build_sidebar(self):
        self.sidebar = CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar.pack_propagate(False)

        CTkLabel(self.sidebar, text=self._t("sidebar_title"), font=ctk.CTkFont(size=26, weight="bold")).pack(pady=(30, 5))
        CTkLabel(self.sidebar, text=self._t("sidebar_subtitle"), font=ctk.CTkFont(size=12), text_color=("gray50", "gray60")).pack(pady=(0, 25))

        # 预设模板
        preset_card = CTkFrame(self.sidebar, corner_radius=12, fg_color=("gray90", "gray17"))
        preset_card.pack(fill="x", padx=15, pady=(10, 10))
        CTkLabel(preset_card, text=self._t("preset"), font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 5))
        self.preset_combo = CTkComboBox(
            preset_card, values=list(PRESETS.keys()),
            state="readonly", width=200,
            command=self._on_preset_selected,
            dropdown_hover_color=("gray70", "gray30"),
        )
        self.preset_combo.set(list(PRESETS.keys())[0])
        self.preset_combo.pack(padx=12, pady=(0, 12))

        # 常用操作
        btn_primary = {"font": ctk.CTkFont(size=15, weight="bold"), "height": 45, "corner_radius": 10}
        btn_secondary = {"font": ctk.CTkFont(size=13), "height": 36, "corner_radius": 10, "fg_color": "transparent", "border_width": 2}

        CTkButton(self.sidebar, text=self._t("run_match"), command=self._run_match, **btn_primary).pack(fill="x", padx=15, pady=(20, 10))
        CTkButton(self.sidebar, text=self._t("settings"), command=self._open_settings, **btn_secondary).pack(fill="x", padx=15, pady=(5, 10))
        CTkButton(self.sidebar, text=self._t("paste_sample"), command=self._paste_sample, **btn_secondary).pack(fill="x", padx=15, pady=(5, 10))
        CTkButton(self.sidebar, text=self._t("clear_all"), command=self._clear_all,
                  hover_color=("gray80", "gray25"), **btn_secondary).pack(fill="x", padx=15, pady=(5, 10))

        # 主题切换
        theme_card = CTkFrame(self.sidebar, corner_radius=12, fg_color=("gray90", "gray17"))
        theme_card.pack(fill="x", padx=15, pady=(20, 10))
        CTkLabel(theme_card, text=self._t("theme"), font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 5))
        self.theme_switch = CTkSwitch(theme_card, text=self._t("dark_mode"), command=self._toggle_theme, onvalue="dark", offvalue="light")
        self.theme_switch.pack(anchor="w", padx=12, pady=(0, 12))
        current = ctk.get_appearance_mode().lower()
        self.theme_switch.select() if current == "dark" else self.theme_switch.deselect()

        CTkLabel(self.sidebar, text=self._t("version"), font=ctk.CTkFont(size=11), text_color=("gray50", "gray60")).pack(side="bottom", pady=15)

    def _build_main_area(self):
        self.main_area = CTkFrame(self, corner_radius=0, fg_color=("gray95", "gray10"))
        self.main_area.pack(side="right", fill="both", expand=True, padx=0, pady=0)

        header = CTkFrame(self.main_area, height=60, corner_radius=0, fg_color=("gray90", "gray13"))
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        CTkLabel(header, text=self._t("workbench"), font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=25, pady=10)

        content = CTkFrame(self.main_area, corner_radius=0, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=15)

        # ---------- 正则输入区域 ----------
        regex_card = CTkFrame(content, corner_radius=16, fg_color=("white", "gray16"))
        regex_card.pack(fill="x", pady=(0, 10))
        regex_card.pack_propagate(False)
        regex_card.configure(height=110)

        regex_header = CTkFrame(regex_card, corner_radius=0, fg_color="transparent", height=36)
        regex_header.pack(fill="x", padx=15, pady=(8, 0))
        regex_header.pack_propagate(False)
        CTkLabel(regex_header, text=self._t("regex_input"), font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=5)

        self.flag_ignorecase = ctk.BooleanVar(value=False)
        self.flag_multiline = ctk.BooleanVar(value=False)
        self.flag_dotall = ctk.BooleanVar(value=False)
        CTkCheckBox(regex_header, text=self._t("ignore_case"), variable=self.flag_ignorecase, command=self._run_match,
                    font=ctk.CTkFont(size=11), checkbox_width=16, checkbox_height=16).pack(side="right", padx=(8, 0))
        CTkCheckBox(regex_header, text=self._t("multiline"), variable=self.flag_multiline, command=self._run_match,
                    font=ctk.CTkFont(size=11), checkbox_width=16, checkbox_height=16).pack(side="right", padx=(8, 0))
        CTkCheckBox(regex_header, text=self._t("dotall"), variable=self.flag_dotall, command=self._run_match,
                    font=ctk.CTkFont(size=11), checkbox_width=16, checkbox_height=16).pack(side="right", padx=(8, 0))

        self.regex_entry = CTkEntry(
            regex_card, placeholder_text=self._t("regex_placeholder"),
            font=ctk.CTkFont(family="Consolas", size=14),
            height=40, corner_radius=10,
            border_width=1, border_color=("gray80", "gray28"),
        )
        self.regex_entry.pack(fill="x", padx=15, pady=(6, 12))
        self.regex_entry.bind("<KeyRelease>", lambda e: self._run_match())

        # ---------- 内容输入区域 ----------
        input_card = CTkFrame(content, corner_radius=16, fg_color=("white", "gray16"))
        input_card.pack(fill="both", expand=True, pady=(0, 10))
        input_card.pack_propagate(False)
        input_card.configure(height=260)

        input_header = CTkFrame(input_card, corner_radius=0, fg_color="transparent", height=36)
        input_header.pack(fill="x", padx=15, pady=(10, 0))
        input_header.pack_propagate(False)
        CTkLabel(input_header, text=self._t("content_input"), font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=5)
        CTkButton(input_header, text="✕", width=32, height=28, corner_radius=8,
                  command=lambda: self.content_text.delete("0.0", "end")).pack(side="right")

        self.content_text = self._register_textbox(CTkTextbox(
            input_card, wrap="word",
            font=ctk.CTkFont(family="Consolas", size=self.settings["font_size"]),
            text_color=(self.settings["font_color_light"], self.settings["font_color_dark"]),
            border_color=(self.settings["border_color_light"], self.settings["border_color_dark"]),
            border_width=self.settings["border_width"],
            corner_radius=10, fg_color=("gray98", "gray14"),
        ))
        self.content_text.pack(fill="both", expand=True, padx=15, pady=(8, 12))
        self.content_text.insert("0.0", self._t("content_placeholder"))
        self.content_text.bind("<FocusIn>", lambda e: self._on_content_focus())
        self.content_text.bind("<KeyRelease>", lambda e: self._run_match())

        # ---------- 结果区域 ----------
        result_card = CTkFrame(content, corner_radius=16, fg_color=("white", "gray16"))
        result_card.pack(fill="both", expand=True, pady=(0, 10))
        result_card.pack_propagate(False)
        result_card.configure(height=260)

        result_header = CTkFrame(result_card, corner_radius=0, fg_color="transparent", height=36)
        result_header.pack(fill="x", padx=15, pady=(10, 0))
        result_header.pack_propagate(False)
        CTkLabel(result_header, text=self._t("result"), font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=5)
        self.stats_label = CTkLabel(result_header, text=self._t("waiting"), font=ctk.CTkFont(size=12), text_color=("gray50", "gray60"))
        self.stats_label.pack(side="right", padx=5)

        self.result_text = self._register_textbox(CTkTextbox(
            result_card, wrap="word",
            font=ctk.CTkFont(family="Consolas", size=self.settings["font_size"]),
            text_color=(self.settings["font_color_light"], self.settings["font_color_dark"]),
            border_color=(self.settings["border_color_light"], self.settings["border_color_dark"]),
            border_width=self.settings["border_width"],
            corner_radius=10, fg_color=("gray98", "gray14"),
        ))
        self.result_text.pack(fill="both", expand=True, padx=15, pady=(8, 12))
        self.result_text.configure(state="disabled")

        # 配置 tag 颜色（底层 tkinter.Text 不支持元组颜色）
        tw = self.result_text._textbox
        _search_bg = "#b58900" if ctk.get_appearance_mode() == "Dark" else "#f1c40f"
        _search_fg = "white" if ctk.get_appearance_mode() == "Dark" else "black"
        tw.tag_configure("match", background="#27ae60", foreground="white")
        tw.tag_configure("nomatch", background="#c0392b", foreground="white")
        tw.tag_configure("group", background="#2980b9", foreground="white")
        tw.tag_configure("info", foreground=("gray40" if ctk.get_appearance_mode() == "Light" else "gray70"))
        tw.tag_configure("warn", background=_search_bg, foreground=_search_fg)

        # 状态栏
        self.status_label = CTkLabel(content, text=self._t("ready"), font=ctk.CTkFont(size=12), text_color=("gray50", "gray60"))
        self.status_label.pack(anchor="w", padx=5)

    # ==================== 事件处理 ====================

    def _on_preset_selected(self, choice):
        pattern = PRESETS.get(choice, "")
        self.regex_entry.delete(0, "end")
        self.regex_entry.insert(0, pattern)
        self._run_match()

    def _on_content_focus(self):
        text = self.content_text.get("0.0", "end")
        if "在此粘贴" in text or "Paste" in text:
            self.content_text.delete("0.0", "end")
            self.content_text.unbind("<FocusIn>")

    def _toggle_theme(self):
        mode = "Dark" if self.theme_switch.get() == "dark" else "Light"
        ctk.set_appearance_mode(mode)

    def _clear_all(self):
        self.regex_entry.delete(0, "end")
        self.content_text.delete("0.0", "end")
        self.result_text.configure(state="normal")
        self.result_text.delete("0.0", "end")
        self.result_text.configure(state="disabled")
        self.stats_label.configure(text=self._t("waiting"))
        self.status_label.configure(text=self._t("cleared"))
        self._compile_error = None

    def _paste_sample(self):
        sample_regex = r"^1[3-9]\d{9}$"
        sample_content = (
            "13800138000\n"
            "13912345678\n"
            "12345678901\n"
            "15088886666\n"
            "abcdefg\n"
            "19999999999\n"
            "110\n"
        )
        self.regex_entry.delete(0, "end")
        self.regex_entry.insert(0, sample_regex)
        self.content_text.delete("0.0", "end")
        self.content_text.insert("0.0", sample_content)
        self._run_match()
        self.status_label.configure(text=self._t("pasted_sample"))

    def _open_settings(self):
        if self._settings_window and self._settings_window.winfo_exists():
            self._settings_window.lift()
            self._settings_window.focus_force()
            return
        self._settings_window = SettingsWindow(self)

    def _build_flags(self):
        flags = 0
        if self.flag_ignorecase.get():
            flags |= re.IGNORECASE
        if self.flag_multiline.get():
            flags |= re.MULTILINE
        if self.flag_dotall.get():
            flags |= re.DOTALL
        return flags

    def _run_match(self):
        pattern = self.regex_entry.get().strip()
        content = self.content_text.get("0.0", "end").strip()

        self.result_text.configure(state="normal")
        self.result_text.delete("0.0", "end")
        tw = self.result_text._textbox

        # 情况1：正则为空
        if not pattern:
            self.result_text.insert("0.0", self._t("empty_regex"))
            tw.tag_add("info", "1.0", "end")
            self.stats_label.configure(text=self._t("waiting"))
            self.status_label.configure(text=self._t("empty_regex"))
            self.result_text.configure(state="disabled")
            return

        flags = self._build_flags()

        # 情况2：正则编译错误
        try:
            regex = re.compile(pattern, flags)
            self._compile_error = None
        except re.error as e:
            self._compile_error = e
            msg = self._t("compile_error", str(e))
            if hasattr(e, "pos") and e.pos is not None:
                msg += self._t("error_at_pos", e.pos)
            self.result_text.insert("0.0", msg)
            tw.tag_add("nomatch", "1.0", "end")
            self.stats_label.configure(text=self._t("compile_fail"))
            self.status_label.configure(text=f"Regex Error: {e}")
            self.result_text.configure(state="disabled")
            return

        # 情况3：测试内容为空
        if not content:
            self.result_text.insert("0.0", self._t("empty_content"))
            tw.tag_add("info", "1.0", "end")
            self.stats_label.configure(text=self._t("empty_content"))
            self.status_label.configure(text=self._t("empty_content"))
            self.result_text.configure(state="disabled")
            return

        lines = content.splitlines()
        match_count = 0
        no_match_count = 0
        total = len(lines)

        for line in lines:
            line_stripped = line.rstrip("\r")
            if not line_stripped:
                self.result_text.insert("end", "\n")
                continue

            match = regex.search(line_stripped)
            if match:
                match_count += 1
                start_idx = self.result_text.index("end-1c")
                groups = match.groups()
                if groups:
                    group_str = " | ".join(str(g) for g in groups if g is not None)
                    display = self._t("match_success", line_stripped) + "\n" + self._t("capture", group_str) + "\n"
                else:
                    display = self._t("match_success", line_stripped) + "\n"
                self.result_text.insert("end", display)
                end_idx = self.result_text.index("end-1c")
                tw.tag_add("match", start_idx, end_idx)
            else:
                no_match_count += 1
                start_idx = self.result_text.index("end-1c")
                display = self._t("match_fail", line_stripped) + "\n"
                self.result_text.insert("end", display)
                end_idx = self.result_text.index("end-1c")
                tw.tag_add("nomatch", start_idx, end_idx)

        self.stats_label.configure(text=self._t("match_stat", match_count, no_match_count, total))
        self.status_label.configure(text=self._t("match_stat", match_count, no_match_count, total))
        self.result_text.configure(state="disabled")


def main():
    app = RegexToolApp()
    app.mainloop()


if __name__ == "__main__":
    main()
