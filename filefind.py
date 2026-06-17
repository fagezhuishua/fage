#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件查询助手 - Modern GUI Edition (customtkinter)
功能：
1. 按目录、文件模式、大小范围、修改日期范围搜索本地文件
2. 支持递归/非递归搜索，多线程加速
3. 现代化界面，深色/浅色主题切换
4. 搜索结果支持点击打开文件、搜索高亮、导出、复制
"""

import os
import sys
import re
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import customtkinter as ctk
from customtkinter import (
    CTk, CTkFrame, CTkButton, CTkLabel, CTkTextbox,
    CTkEntry, CTkSwitch, CTkProgressBar, CTkToplevel,
    CTkCheckBox,
)
from tkinter import filedialog, messagebox, colorchooser

# 全局外观设置
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

SETTINGS_FILE = "file_query_settings.json"

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
        "app_title": "文件查询助手",
        "sidebar_title": "文件查询",
        "sidebar_subtitle": "本地文件智能检索工具",
        "search": "▶  开始搜索",
        "stop_search": "⏹  停止搜索",
        "clear_results": "🗑️ 清空结果",
        "settings": "⚙️ 设置",
        "theme": "外观主题",
        "dark_mode": "深色模式",
        "version": "v2.0 Modern Edition",
        "workbench": "本地文件查询工作台",
        "search_params": "🔍 搜索条件",
        "base_dir": "搜索目录",
        "browse": "浏览...",
        "file_pattern": "文件模式",
        "pattern_hint": "*.py 或 py",
        "file_size": "文件大小 (字节)",
        "min_size": "最小",
        "max_size": "最大",
        "modified_date": "修改日期",
        "date_hint": "YYYY-MM-DD",
        "recursive": "递归搜索子文件夹",
        "result_area": "📋 搜索结果",
        "export_txt": "导出 .txt",
        "copy_result": "复制结果",
        "search_box": "搜索",
        "clear_search": "清除高亮",
        "ready": "就绪",
        "searching": "搜索中...",
        "stopped": "搜索已停止",
        "no_match": "没有找到匹配的文件。",
        "no_content": "没有可导出的内容，请先执行搜索。",
        "export_success": "导出成功",
        "export_fail": "导出失败",
        "copy_done": "结果已复制到剪贴板 ✓",
        "file_saved_to": "文件已保存到:\n{}",
        "found_files": "完成！找到 {} 个文件",
        "error": "错误",
        "date_format_error": "日期格式错误，请使用 YYYY-MM-DD 格式",
        "search_failed": "搜索失败",
        "open_failed": "无法打开文件: {}",
        "cleared": "已清空",
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
        "search_not_found": "未找到: {}",
        "search_highlight": "高亮显示: {}",
        "search_cleared": "已清除搜索高亮",
    },
    "en": {
        "app_title": "File Query Assistant",
        "sidebar_title": "File Query",
        "sidebar_subtitle": "Local File Smart Search Tool",
        "search": "▶  Search",
        "stop_search": "⏹  Stop Search",
        "clear_results": "🗑️ Clear",
        "settings": "⚙️ Settings",
        "theme": "Theme",
        "dark_mode": "Dark Mode",
        "version": "v2.0 Modern Edition",
        "workbench": "Local File Query Workbench",
        "search_params": "🔍 Search Conditions",
        "base_dir": "Search Directory",
        "browse": "Browse...",
        "file_pattern": "File Pattern",
        "pattern_hint": "*.py or py",
        "file_size": "File Size (bytes)",
        "min_size": "Min",
        "max_size": "Max",
        "modified_date": "Modified Date",
        "date_hint": "YYYY-MM-DD",
        "recursive": "Search subfolders recursively",
        "result_area": "📋 Search Results",
        "export_txt": "Export .txt",
        "copy_result": "Copy Result",
        "search_box": "Search",
        "clear_search": "Clear Highlight",
        "ready": "Ready",
        "searching": "Searching...",
        "stopped": "Search stopped",
        "no_match": "No matching files found.",
        "no_content": "No content to export. Please search first.",
        "export_success": "Export Successful",
        "export_fail": "Export Failed",
        "copy_done": "Result copied to clipboard ✓",
        "file_saved_to": "File saved to:\n{}",
        "found_files": "Done! Found {} files",
        "error": "Error",
        "date_format_error": "Invalid date format. Please use YYYY-MM-DD.",
        "search_failed": "Search failed",
        "open_failed": "Unable to open file: {}",
        "cleared": "Cleared",
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
        "search_not_found": "Not found: {}",
        "search_highlight": "Highlighting: {}",
        "search_cleared": "Search highlight cleared",
    }
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


def parse_date(value: str) -> Optional[datetime]:
    """解析日期字符串，格式为 YYYY-MM-DD"""
    if not value or not value.strip():
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d")
    except ValueError:
        return None


def check_file(file_path: str, min_size: Optional[int], max_size: Optional[int],
               modified_after: Optional[datetime], modified_before: Optional[datetime]) -> bool:
    """检查单个文件是否符合条件"""
    try:
        stat = os.stat(file_path)
        if not os.path.isfile(file_path):
            return False
        if min_size is not None and stat.st_size < min_size:
            return False
        if max_size is not None and stat.st_size > max_size:
            return False
        if modified_after is not None or modified_before is not None:
            mtime = datetime.fromtimestamp(stat.st_mtime)
            if modified_after is not None and mtime < modified_after:
                return False
            if modified_before is not None and mtime > modified_before:
                return False
        return True
    except (OSError, IOError):
        return False


def query_local_files(
    base_dir: str,
    pattern: str = "*",
    recursive: bool = True,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    modified_after: Optional[datetime] = None,
    modified_before: Optional[datetime] = None,
    progress_callback=None,
    stop_event: Optional[threading.Event] = None,
) -> list[str]:
    """查询本地文件，返回绝对路径列表（使用多线程加速，支持中断）"""
    base = Path(base_dir).expanduser().resolve()
    if not base.exists():
        raise FileNotFoundError(f"目录不存在: {base_dir}")
    if not base.is_dir():
        raise NotADirectoryError(f"路径不是目录: {base_dir}")

    search_pattern = pattern
    if pattern and pattern != "*" and "*" not in pattern and "?" not in pattern:
        if "." not in pattern or pattern.startswith("."):
            ext = pattern if pattern.startswith(".") else f".{pattern}"
            search_pattern = f"*{ext}"

    all_files = []
    if recursive:
        for root, _, files in os.walk(str(base)):
            if stop_event and stop_event.is_set():
                break
            for f in files:
                if stop_event and stop_event.is_set():
                    break
                if search_pattern == "*" or Path(f).match(search_pattern):
                    all_files.append(os.path.join(root, f))
                    if progress_callback and len(all_files) % 100 == 0:
                        progress_callback(len(all_files))
            if stop_event and stop_event.is_set():
                break
    else:
        try:
            for item in os.listdir(str(base)):
                if stop_event and stop_event.is_set():
                    break
                item_path = os.path.join(str(base), item)
                if os.path.isfile(item_path) and (search_pattern == "*" or Path(item).match(search_pattern)):
                    all_files.append(item_path)
        except PermissionError:
            pass

    if stop_event and stop_event.is_set():
        return []

    if progress_callback:
        progress_callback(f"检查 {len(all_files)} 个文件...")

    results = []
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        futures = {
            executor.submit(check_file, f, min_size, max_size, modified_after, modified_before): f
            for f in all_files
        }
        for i, future in enumerate(as_completed(futures)):
            if stop_event and stop_event.is_set():
                # 取消剩余任务
                for future_to_cancel in futures:
                    future_to_cancel.cancel()
                break
            if future.result():
                results.append(futures[future])
            if progress_callback and i % 50 == 0:
                progress_callback(f"已检查 {i}/{len(all_files)} 个文件，找到 {len(results)} 个匹配")

    return results


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
        self._add_row_label(content, self.parent._t("language"))
        self.lang_combo = ctk.CTkComboBox(
            content, values=["zh_CN", "en"],
            state="readonly", width=200,
        )
        self.lang_combo.set(self.settings["language"])
        self.lang_combo.pack(anchor="w", pady=(0, 12))

        # 字体大小
        self._add_row_label(content, self.parent._t("font_size"))
        size_frame = CTkFrame(content, fg_color="transparent")
        size_frame.pack(fill="x", pady=(0, 12))
        self.size_slider = ctk.CTkSlider(size_frame, from_=10, to=20, number_of_steps=10, width=200)
        self.size_slider.set(self.settings["font_size"])
        self.size_slider.pack(side="left")
        self.size_label = CTkLabel(size_frame, text=str(int(self.settings["font_size"])), width=30)
        self.size_label.pack(side="left", padx=(10, 0))
        self.size_slider.configure(command=lambda v: self.size_label.configure(text=str(int(float(v)))))

        # 颜色设置
        self._add_color_row(content, self.parent._t("font_color_light"), "font_color_light")
        self._add_color_row(content, self.parent._t("font_color_dark"), "font_color_dark")
        self._add_color_row(content, self.parent._t("border_color_light"), "border_color_light")
        self._add_color_row(content, self.parent._t("border_color_dark"), "border_color_dark")

        # 边框粗细
        self._add_row_label(content, self.parent._t("border_width"))
        bw_frame = CTkFrame(content, fg_color="transparent")
        bw_frame.pack(fill="x", pady=(0, 12))
        self.bw_slider = ctk.CTkSlider(bw_frame, from_=0, to=3, number_of_steps=3, width=200)
        self.bw_slider.set(self.settings["border_width"])
        self.bw_slider.pack(side="left")
        self.bw_label = CTkLabel(bw_frame, text=str(int(self.settings["border_width"])), width=30)
        self.bw_label.pack(side="left", padx=(10, 0))
        self.bw_slider.configure(command=lambda v: self.bw_label.configure(text=str(int(float(v)))))

        # 预览区
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
        self.preview_text.insert("0.0", "C:\\Users\\Example\\file.txt")
        self.preview_text.configure(state="disabled")

        # 底部按钮
        bottom = CTkFrame(self, height=50, fg_color="transparent")
        bottom.pack(fill="x", padx=20, pady=(0, 15))
        bottom.pack_propagate(False)
        CTkButton(bottom, text=self.parent._t("save"), width=100, command=self._save).pack(side="right", padx=(5, 0))
        CTkButton(bottom, text=self.parent._t("cancel"), width=100, fg_color="transparent", border_width=1,
                  hover_color=("gray85", "gray25"), command=self._on_close).pack(side="right", padx=(5, 0))

        # 实时预览绑定
        for widget in (self.size_slider, self.bw_slider):
            widget.configure(command=lambda v, w=widget: self._update_preview())

    def _add_row_label(self, parent, text):
        CTkLabel(parent, text=text, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(8, 4))

    def _add_color_row(self, parent, label, key):
        row = CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 8))
        CTkLabel(row, text=label, font=ctk.CTkFont(size=13)).pack(side="left")
        color_btn = CTkButton(
            row, text=self.parent._t("choose_color"), width=90, height=28,
            command=lambda k=key: self._pick_color(k),
        )
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


class FileQueryApp(CTk):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.textboxes = []
        self.entries = []

        self.title(self._t("app_title"))
        self.geometry("1200x820")
        self.minsize(1000, 700)

        self._build_sidebar()
        self._build_main_area()
        self.apply_settings()

        self._settings_window = None
        self.current_results = []
        self.search_thread = None
        self.stop_event = None

    def _t(self, key):
        """获取当前语言的文本"""
        lang = self.settings.get("language", "zh_CN")
        return TEXTS.get(lang, TEXTS["zh_CN"]).get(key, key)

    def apply_settings(self):
        """将设置应用到所有已注册的文本框和输入框"""
        font = ctk.CTkFont(family="Consolas", size=self.settings["font_size"])
        text_color = (self.settings["font_color_light"], self.settings["font_color_dark"])
        border_color = (self.settings["border_color_light"], self.settings["border_color_dark"])
        bw = self.settings["border_width"]
        for tb in self.textboxes:
            try:
                tb.configure(
                    font=font,
                    text_color=text_color,
                    border_color=border_color,
                    border_width=bw,
                )
            except Exception:
                pass
        for entry in self.entries:
            try:
                entry.configure(
                    font=ctk.CTkFont(family="Microsoft YaHei UI", size=self.settings["font_size"]),
                    text_color=text_color,
                    border_color=border_color,
                    border_width=bw,
                )
            except Exception:
                pass

    def _register_textbox(self, tb):
        self.textboxes.append(tb)
        return tb

    def _register_entry(self, entry):
        self.entries.append(entry)
        return entry

    def _build_sidebar(self):
        self.sidebar = CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar.pack_propagate(False)

        CTkLabel(self.sidebar, text=self._t("sidebar_title"), font=ctk.CTkFont(size=26, weight="bold")).pack(pady=(30, 5))
        CTkLabel(self.sidebar, text=self._t("sidebar_subtitle"), font=ctk.CTkFont(size=12), text_color=("gray50", "gray60")).pack(pady=(0, 25))

        btn_primary = {"font": ctk.CTkFont(size=15, weight="bold"), "height": 45, "corner_radius": 10}
        btn_secondary = {"font": ctk.CTkFont(size=13), "height": 36, "corner_radius": 10, "fg_color": "transparent", "border_width": 2}

        self.search_btn = CTkButton(self.sidebar, text=self._t("search"), command=self.search_files, **btn_primary)
        self.search_btn.pack(fill="x", padx=15, pady=(20, 10))
        self.stop_btn = CTkButton(self.sidebar, text=self._t("stop_search"), command=self.stop_search,
                                  fg_color=("#c0392b", "#922b21"), hover_color=("#a93226", "#7b241c"),
                                  font=ctk.CTkFont(size=15, weight="bold"), height=45, corner_radius=10)
        self.stop_btn.pack(fill="x", padx=15, pady=(5, 10))
        self.stop_btn.configure(state="disabled")
        CTkButton(self.sidebar, text=self._t("clear_results"), command=self.clear_results, **btn_secondary).pack(fill="x", padx=15, pady=(5, 10))
        CTkButton(self.sidebar, text=self._t("settings"), command=self._open_settings, **btn_secondary).pack(fill="x", padx=15, pady=(5, 10))

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

        # ---------- 搜索条件卡片 ----------
        params_card = CTkFrame(content, corner_radius=16, fg_color=("white", "gray16"))
        params_card.pack(fill="x", pady=(0, 10))
        params_card.pack_propagate(False)
        params_card.configure(height=230)

        CTkLabel(params_card, text=self._t("search_params"), font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=15, pady=(10, 5))

        params_content = CTkFrame(params_card, fg_color="transparent")
        params_content.pack(fill="both", expand=True, padx=15, pady=5)

        # 搜索目录
        CTkLabel(params_content, text=self._t("base_dir"), font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, sticky="w", pady=8)
        dir_frame = CTkFrame(params_content, fg_color="transparent")
        dir_frame.grid(row=0, column=1, sticky="ew", pady=8, padx=(10, 0))
        dir_frame.columnconfigure(0, weight=1)
        self.dir_var = ctk.StringVar(value=".")
        self.dir_entry = self._register_entry(CTkEntry(dir_frame, textvariable=self.dir_var, placeholder_text="."))
        self.dir_entry.grid(row=0, column=0, sticky="ew")
        CTkButton(dir_frame, text=self._t("browse"), width=80, command=self.browse_directory).grid(row=0, column=1, padx=(8, 0))

        # 文件模式
        CTkLabel(params_content, text=self._t("file_pattern"), font=ctk.CTkFont(size=13, weight="bold")).grid(row=1, column=0, sticky="w", pady=8)
        self.pattern_var = ctk.StringVar()
        self.pattern_entry = self._register_entry(CTkEntry(params_content, textvariable=self.pattern_var, placeholder_text=self._t("pattern_hint")))
        self.pattern_entry.grid(row=1, column=1, sticky="ew", pady=8, padx=(10, 0))

        # 文件大小
        CTkLabel(params_content, text=self._t("file_size"), font=ctk.CTkFont(size=13, weight="bold")).grid(row=2, column=0, sticky="w", pady=8)
        size_frame = CTkFrame(params_content, fg_color="transparent")
        size_frame.grid(row=2, column=1, sticky="ew", pady=8, padx=(10, 0))
        size_frame.columnconfigure(0, weight=1)
        size_frame.columnconfigure(2, weight=1)
        self.min_size_var = ctk.StringVar()
        self.max_size_var = ctk.StringVar()
        self.min_size_entry = self._register_entry(CTkEntry(size_frame, textvariable=self.min_size_var, placeholder_text=self._t("min_size")))
        self.min_size_entry.grid(row=0, column=0, sticky="ew")
        CTkLabel(size_frame, text=" <= 大小 <= ", font=ctk.CTkFont(size=12)).grid(row=0, column=1, padx=5)
        self.max_size_entry = self._register_entry(CTkEntry(size_frame, textvariable=self.max_size_var, placeholder_text=self._t("max_size")))
        self.max_size_entry.grid(row=0, column=2, sticky="ew")

        # 修改日期
        CTkLabel(params_content, text=self._t("modified_date"), font=ctk.CTkFont(size=13, weight="bold")).grid(row=3, column=0, sticky="w", pady=8)
        date_frame = CTkFrame(params_content, fg_color="transparent")
        date_frame.grid(row=3, column=1, sticky="ew", pady=8, padx=(10, 0))
        date_frame.columnconfigure(0, weight=1)
        date_frame.columnconfigure(2, weight=1)
        self.after_date_var = ctk.StringVar()
        self.before_date_var = ctk.StringVar()
        self.after_date_entry = self._register_entry(CTkEntry(date_frame, textvariable=self.after_date_var, placeholder_text=self._t("date_hint")))
        self.after_date_entry.grid(row=0, column=0, sticky="ew")
        CTkLabel(date_frame, text=" <= 日期 <= ", font=ctk.CTkFont(size=12)).grid(row=0, column=1, padx=5)
        self.before_date_entry = self._register_entry(CTkEntry(date_frame, textvariable=self.before_date_var, placeholder_text=self._t("date_hint")))
        self.before_date_entry.grid(row=0, column=2, sticky="ew")

        params_content.columnconfigure(1, weight=1)

        # 递归选项
        self.recursive_var = ctk.BooleanVar(value=True)
        CTkCheckBox(params_card, text=self._t("recursive"), variable=self.recursive_var).pack(anchor="w", padx=15, pady=(0, 12))

        # ---------- 进度条 ----------
        self.progress_bar = CTkProgressBar(content, height=12, corner_radius=6)
        self.progress_bar.pack(fill="x", pady=(0, 10))
        self.progress_bar.set(0)

        # ---------- 搜索结果卡片 ----------
        result_card = CTkFrame(content, corner_radius=16, fg_color=("white", "gray16"))
        result_card.pack(fill="both", expand=True, pady=(0, 10))
        result_card.pack_propagate(False)
        result_card.configure(height=280)

        result_header = CTkFrame(result_card, corner_radius=0, fg_color="transparent", height=40)
        result_header.pack(fill="x", padx=15, pady=(10, 0))
        result_header.pack_propagate(False)

        CTkLabel(result_header, text=self._t("result_area"), font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=5)

        # 结果区搜索
        self.result_search_entry = self._register_entry(CTkEntry(result_header, width=140, placeholder_text=self._t("search_box")))
        self.result_search_entry.pack(side="right", padx=(5, 0))
        self.result_search_entry.bind("<Return>", lambda e: self._search_result())
        CTkButton(result_header, text="🔍", width=32, height=32, corner_radius=8,
                  command=self._search_result).pack(side="right", padx=(5, 0))
        CTkButton(result_header, text="✕", width=32, height=32, corner_radius=8, fg_color="transparent", border_width=1,
                  hover_color=("gray85", "gray25"),
                  command=self._clear_search).pack(side="right", padx=(5, 0))

        btn_style = {"width": 110, "height": 32, "corner_radius": 8, "font": ctk.CTkFont(size=12)}
        CTkButton(result_header, text=self._t("export_txt"), command=self._export_txt, **btn_style).pack(side="right", padx=(5, 0))
        CTkButton(result_header, text=self._t("copy_result"), command=self._copy_result,
                  fg_color="transparent", border_width=1, hover_color=("gray85", "gray25"), **btn_style).pack(side="right", padx=(5, 0))

        self.result_text = self._register_textbox(CTkTextbox(
            result_card, wrap="none",
            font=ctk.CTkFont(family="Consolas", size=self.settings["font_size"]),
            text_color=(self.settings["font_color_light"], self.settings["font_color_dark"]),
            border_color=(self.settings["border_color_light"], self.settings["border_color_dark"]),
            border_width=self.settings["border_width"],
            corner_radius=10, fg_color=("gray98", "gray14"),
        ))
        self.result_text.pack(fill="both", expand=True, padx=15, pady=(8, 15))

        _search_bg = "#b58900" if ctk.get_appearance_mode() == "Dark" else "#f1c40f"
        _search_fg = "white" if ctk.get_appearance_mode() == "Dark" else "black"
        tw = self.result_text._textbox
        tw.tag_configure("link", foreground="#0066cc", underline=True)
        tw.tag_configure("search", background=_search_bg, foreground=_search_fg)
        tw.tag_bind("link", "<Enter>", lambda e: tw.config(cursor="hand2"))
        tw.tag_bind("link", "<Leave>", lambda e: tw.config(cursor=""))
        tw.tag_bind("link", "<Button-1>", self.on_file_click)

        # 状态栏
        self.status_label = CTkLabel(content, text=self._t("ready"), font=ctk.CTkFont(size=12), text_color=("gray50", "gray60"))
        self.status_label.pack(anchor="w", padx=5)

        content.columnconfigure(0, weight=1)

    # ==================== 主题与设置 ====================

    def _toggle_theme(self):
        mode = "Dark" if self.theme_switch.get() == "dark" else "Light"
        ctk.set_appearance_mode(mode)

    def _open_settings(self):
        if self._settings_window and self._settings_window.winfo_exists():
            self._settings_window.lift()
            self._settings_window.focus_force()
            return
        self._settings_window = SettingsWindow(self)

    # ==================== 搜索高亮 ====================

    def _search_result(self):
        keyword = self.result_search_entry.get().strip()
        if not keyword:
            return
        tw = self.result_text._textbox
        tw.tag_remove("search", "1.0", "end")
        pos = "1.0"
        found = False
        while True:
            pos = tw.search(keyword, pos, stopindex="end", nocase=True)
            if not pos:
                break
            found = True
            end_pos = f"{pos}+{len(keyword)}c"
            tw.tag_add("search", pos, end_pos)
            tw.see(pos)
            pos = end_pos
        if not found:
            self.status_label.configure(text=self._t("search_not_found").format(keyword))
        else:
            self.status_label.configure(text=self._t("search_highlight").format(keyword))

    def _clear_search(self):
        tw = self.result_text._textbox
        tw.tag_remove("search", "1.0", "end")
        self.result_search_entry.delete(0, "end")
        self.status_label.configure(text=self._t("search_cleared"))

    # ==================== 业务逻辑 ====================

    def browse_directory(self):
        """打开目录选择对话框"""
        directory = filedialog.askdirectory(title=self._t("base_dir"))
        if directory:
            self.dir_var.set(directory)

    def parse_size(self, value: str) -> Optional[int]:
        """解析大小输入"""
        if not value or not value.strip():
            return None
        try:
            return int(value.strip())
        except ValueError:
            return None

    def _set_searching_ui(self, searching: bool):
        """切换搜索中/空闲状态的 UI"""
        if searching:
            self.search_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
        else:
            self.search_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")

    def _safe_progress(self, msg):
        """线程安全的进度更新（通过 after 投递到主线程）"""
        self.after(0, lambda: self._update_progress(msg))

    def _update_progress(self, msg):
        """在主线程更新进度条和状态栏"""
        if not self.winfo_exists():
            return
        if isinstance(msg, str):
            self.status_label.configure(text=msg)
            if "检查" in msg:
                self.progress_bar.set(0.3)
            elif "已检查" in msg:
                try:
                    parts = msg.split("，")
                    checked_part = parts[0].split("/")[0].replace("已检查 ", "").strip()
                    total_part = parts[0].split("/")[1].strip()
                    progress = float(checked_part) / float(total_part) * 0.7 + 0.3
                    self.progress_bar.set(min(progress, 1.0))
                except Exception:
                    pass
        else:
            self.status_label.configure(text=f"扫描中... 已发现 {msg} 个文件")
            self.progress_bar.set(0.2)

    def _search_worker(self, min_size, max_size, modified_after, modified_before):
        """在后台线程中执行文件搜索"""
        try:
            files = query_local_files(
                base_dir=self.dir_var.get(),
                pattern=self.pattern_var.get() or "*",
                recursive=self.recursive_var.get(),
                min_size=min_size,
                max_size=max_size,
                modified_after=modified_after,
                modified_before=modified_before,
                progress_callback=self._safe_progress,
                stop_event=self.stop_event,
            )
            self.after(0, lambda: self._on_search_finished(files))
        except Exception as e:
            self.after(0, lambda err=str(e): self._on_search_error(err))

    def _on_search_finished(self, files):
        """搜索完成或停止后的 UI 更新"""
        if not self.winfo_exists():
            return
        self.result_text.configure(state="normal")
        if self.stop_event and self.stop_event.is_set():
            self.status_label.configure(text=self._t("stopped"))
        elif not files:
            self.result_text.insert("0.0", self._t("no_match"))
            self.status_label.configure(text=self._t("no_match"))
        else:
            for file_path in files:
                self.result_text.insert("end", file_path, "link")
                self.result_text.insert("end", "\n")
            self.status_label.configure(text=self._t("found_files").format(len(files)))
        self.result_text.configure(state="disabled")
        self.current_results = files
        self.progress_bar.set(1.0 if files else 0)
        self._set_searching_ui(False)
        self.search_thread = None
        self.stop_event = None

    def _on_search_error(self, error_msg):
        """搜索出错后的 UI 更新"""
        if not self.winfo_exists():
            return
        messagebox.showerror(self._t("error"), f"{self._t('search_failed')}: {error_msg}")
        self.status_label.configure(text=self._t("search_failed"))
        self.progress_bar.set(0)
        self._set_searching_ui(False)
        self.search_thread = None
        self.stop_event = None

    def search_files(self):
        """执行文件搜索（启动后台线程）"""
        # 若已有搜索线程在运行，先停止
        if self.search_thread and self.search_thread.is_alive():
            self.stop_search()
            self.after(100, self.search_files)
            return

        self.result_text.configure(state="normal")
        self.result_text.delete("0.0", "end")
        self.result_text.configure(state="disabled")
        self.current_results = []
        self.status_label.configure(text=self._t("searching"))
        self.progress_bar.set(0)
        self._set_searching_ui(True)
        self.update()

        min_size = self.parse_size(self.min_size_var.get())
        max_size = self.parse_size(self.max_size_var.get())
        modified_after = parse_date(self.after_date_var.get())
        modified_before = parse_date(self.before_date_var.get())

        if self.after_date_var.get() and not modified_after:
            messagebox.showerror(self._t("error"), self._t("date_format_error"))
            self.status_label.configure(text=self._t("search_failed"))
            self._set_searching_ui(False)
            return
        if self.before_date_var.get() and not modified_before:
            messagebox.showerror(self._t("error"), self._t("date_format_error"))
            self.status_label.configure(text=self._t("search_failed"))
            self._set_searching_ui(False)
            return

        self.stop_event = threading.Event()
        self.search_thread = threading.Thread(
            target=self._search_worker,
            args=(min_size, max_size, modified_after, modified_before),
            daemon=True,
        )
        self.search_thread.start()

    def stop_search(self):
        """停止当前搜索"""
        if self.stop_event and not self.stop_event.is_set():
            self.stop_event.set()
            self.status_label.configure(text=self._t("stopped"))

    def on_file_click(self, event):
        """处理文件链接点击事件"""
        tw = self.result_text._textbox
        index = tw.index(f"@{event.x},{event.y}")
        tag_ranges = tw.tag_ranges("link")
        for start, end in zip(tag_ranges[0::2], tag_ranges[1::2]):
            if tw.compare(start, "<=", index) and tw.compare(index, "<", end):
                file_path = tw.get(start, end)
                self.open_file(file_path)
                break

    def open_file(self, file_path: str):
        """打开文件"""
        try:
            if os.name == 'nt':
                os.startfile(file_path)
            elif os.name == 'posix':
                if sys.platform == 'darwin':
                    import subprocess
                    subprocess.run(['open', file_path])
                else:
                    import subprocess
                    subprocess.run(['xdg-open', file_path])
        except Exception as e:
            messagebox.showerror(self._t("error"), self._t("open_failed").format(str(e)))

    def clear_results(self):
        """清空搜索结果（若正在搜索则先停止）"""
        if self.search_thread and self.search_thread.is_alive():
            self.stop_search()
        self.result_text.configure(state="normal")
        self.result_text.delete("0.0", "end")
        self.result_text.configure(state="disabled")
        self.current_results = []
        self.status_label.configure(text=self._t("cleared"))
        self.progress_bar.set(0)

    def _export_txt(self):
        """导出结果为 txt"""
        if not self.current_results:
            messagebox.showwarning(self._t("settings_title"), self._t("no_content"))
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.current_results))
            self.status_label.configure(text=self._t("file_saved_to").format(os.path.basename(path)))
            messagebox.showinfo(self._t("export_success"), self._t("file_saved_to").format(path))
        except Exception as e:
            messagebox.showerror(self._t("export_fail"), str(e))

    def _copy_result(self):
        """复制结果到剪贴板"""
        if not self.current_results:
            return
        self.clipboard_clear()
        self.clipboard_append("\n".join(self.current_results))
        self.status_label.configure(text=self._t("copy_done"))


def main() -> None:
    app = FileQueryApp()
    app.mainloop()


if __name__ == "__main__":
    main()
