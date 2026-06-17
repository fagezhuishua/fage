#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IP去重工具 - Modern GUI Edition (customtkinter)
功能：
1. 支持从文本、Excel、文件导入IP数据
2. 支持CIDR网段与单个IP的去重（去掉包含在网段内的主机地址），保持原始顺序
3. 支持多种输出格式（文本、Excel、直接显示）
4. 支持多种分隔符重新格式化输出
5. 现代化界面，支持深色/浅色主题切换
6. 支持输入/输出区域搜索高亮
7. 支持对比框查看源文件与去重结果差异
8. 支持设置：语言、字体颜色/大小、边框颜色/粗细
"""

import re
import os
import json
import ipaddress
import customtkinter as ctk
from customtkinter import (
    CTk, CTkFrame, CTkButton, CTkLabel, CTkTextbox,
    CTkComboBox, CTkSwitch, CTkEntry, CTkToplevel,
    CTkSlider,
)
from tkinter import filedialog, messagebox, colorchooser

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import pandas as pd
except ImportError:
    pd = None

# 全局外观设置
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

SETTINGS_FILE = "ip_tool_settings.json"

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
        "app_title": "IP去重工具",
        "sidebar_title": "IP 去重",
        "sidebar_subtitle": "智能网段与地址去重工具",
        "delimiter": "输出分隔符",
        "start_dedup": "▶  开始去重",
        "compare_view": "🔍 对比查看",
        "paste_sample": "粘贴示例数据",
        "clear_all": "清空全部",
        "settings": "⚙️ 设置",
        "theme": "外观主题",
        "dark_mode": "深色模式",
        "version": "v3.1  Settings Edition",
        "workbench": "IP 地址去重工作台",
        "input_area": "📥  输入区域",
        "import_txt": "导入 .txt",
        "import_excel": "导入 Excel",
        "clear_input": "清空输入",
        "output_area": "📤  去重结果",
        "export_txt": "导出 .txt",
        "export_excel": "导出 Excel",
        "copy_result": "复制结果",
        "search": "搜索",
        "placeholder_input": "在此粘贴 IP 地址，或点击右上角导入文件...\n支持 IPv4 / IPv6 及 CIDR 网段格式，如 192.168.1.0/24",
        "stats_waiting": "未执行去重  |  等待输入...",
        "ready": "就绪",
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
        "empty_input": "输入内容为空，请先输入或导入IP数据。",
        "no_ip_found": "未从输入内容中提取到有效的IP地址。",
        "dedup_done": "去重完成 ✓",
        "export_success": "导出成功",
        "export_fail": "导出失败",
        "import_fail": "导入失败",
        "no_content": "没有可导出的内容，请先执行去重。",
        "copy_done": "结果已复制到剪贴板 ✓",
        "imported_txt": "已导入文本: {}",
        "imported_excel": "已导入Excel: {}",
        "cleared": "已清空",
        "input_cleared": "输入已清空",
        "pasted_sample": "已填入示例数据，点击左侧「开始去重」查看效果",
        "compare_first": "请先执行去重操作，再打开对比窗口。",
        "missing_dep": "缺少依赖",
        "missing_excel_dep": "未安装 openpyxl 或 pandas，无法读取Excel文件。\n请执行: pip install openpyxl pandas",
        "missing_pandas": "未安装 pandas，无法导出Excel。\n请执行: pip install pandas openpyxl",
        "file_saved_to": "文件已保存到:\n{}",
        "search_not_found": "未找到: {}",
        "search_highlight": "高亮显示: {}",
        "search_cleared": "已清除搜索高亮",
        "stats_template": "原始: {} 条（网段 {} / 主机 {}）   去重后: {} 条   移除: {} 条",
        "compare_title": "源文件 vs 去重结果 对比",
        "raw_list": "原始 IP 列表",
        "deduped_list": "去重后 IP 列表",
        "keep": "■ 保留",
        "remove": "■ 移除（重复/被网段包含）",
        "close": "关闭",
        "clear_highlight": "清除高亮",
        "compare_search_placeholder": "输入IP或关键词搜索...",
    },
    "en": {
        "app_title": "IP Deduplication Tool",
        "sidebar_title": "IP Dedup",
        "sidebar_subtitle": "Smart Network & Address Deduplication",
        "delimiter": "Output Delimiter",
        "start_dedup": "▶  Start Dedup",
        "compare_view": "🔍 Compare",
        "paste_sample": "Paste Sample",
        "clear_all": "Clear All",
        "settings": "⚙️ Settings",
        "theme": "Theme",
        "dark_mode": "Dark Mode",
        "version": "v3.1  Settings Edition",
        "workbench": "IP Deduplication Workbench",
        "input_area": "📥  Input",
        "import_txt": "Import .txt",
        "import_excel": "Import Excel",
        "clear_input": "Clear Input",
        "output_area": "📤  Result",
        "export_txt": "Export .txt",
        "export_excel": "Export Excel",
        "copy_result": "Copy Result",
        "search": "Search",
        "placeholder_input": "Paste IP addresses here, or import a file...\nSupports IPv4 / IPv6 and CIDR formats, e.g. 192.168.1.0/24",
        "stats_waiting": "No dedup performed  |  Waiting for input...",
        "ready": "Ready",
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
        "empty_input": "Input is empty. Please enter or import IP data first.",
        "no_ip_found": "No valid IP addresses found in the input.",
        "dedup_done": "Dedup completed ✓",
        "export_success": "Export Successful",
        "export_fail": "Export Failed",
        "import_fail": "Import Failed",
        "no_content": "No content to export. Please perform deduplication first.",
        "copy_done": "Result copied to clipboard ✓",
        "imported_txt": "Imported text: {}",
        "imported_excel": "Imported Excel: {}",
        "cleared": "Cleared",
        "input_cleared": "Input cleared",
        "pasted_sample": "Sample data pasted. Click 'Start Dedup' on the left to see the result.",
        "compare_first": "Please perform deduplication before opening the compare window.",
        "missing_dep": "Missing Dependencies",
        "missing_excel_dep": "openpyxl or pandas is not installed. Cannot read Excel files.\nRun: pip install openpyxl pandas",
        "missing_pandas": "pandas is not installed. Cannot export to Excel.\nRun: pip install pandas openpyxl",
        "file_saved_to": "File saved to:\n{}",
        "search_not_found": "Not found: {}",
        "search_highlight": "Highlighting: {}",
        "search_cleared": "Search highlight cleared",
        "stats_template": "Original: {} (Networks {} / Hosts {})   Deduped: {}   Removed: {}",
        "compare_title": "Source vs Deduped Result",
        "raw_list": "Original IP List",
        "deduped_list": "Deduped IP List",
        "keep": "■ Keep",
        "remove": "■ Removed (Duplicate / Contained)",
        "close": "Close",
        "clear_highlight": "Clear Highlight",
        "compare_search_placeholder": "Enter IP or keyword to search...",
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
        self.lang_combo = CTkComboBox(
            content, values=["zh_CN", "en"],
            state="readonly", width=200,
        )
        self.lang_combo.set(self.settings["language"])
        self.lang_combo.pack(anchor="w", pady=(0, 12))

        # 字体大小
        self._add_row_label(content, self.parent._t("font_size"))
        size_frame = CTkFrame(content, fg_color="transparent")
        size_frame.pack(fill="x", pady=(0, 12))
        self.size_slider = CTkSlider(size_frame, from_=10, to=20, number_of_steps=10, width=200)
        self.size_slider.set(self.settings["font_size"])
        self.size_slider.pack(side="left")
        self.size_label = CTkLabel(size_frame, text=str(int(self.settings["font_size"])), width=30)
        self.size_label.pack(side="left", padx=(10, 0))
        self.size_slider.configure(command=lambda v: self.size_label.configure(text=str(int(float(v)))))

        # 字体颜色 - 浅色
        self._add_color_row(content, self.parent._t("font_color_light"), "font_color_light")
        # 字体颜色 - 深色
        self._add_color_row(content, self.parent._t("font_color_dark"), "font_color_dark")
        # 边框颜色 - 浅色
        self._add_color_row(content, self.parent._t("border_color_light"), "border_color_light")
        # 边框颜色 - 深色
        self._add_color_row(content, self.parent._t("border_color_dark"), "border_color_dark")

        # 边框粗细
        self._add_row_label(content, self.parent._t("border_width"))
        bw_frame = CTkFrame(content, fg_color="transparent")
        bw_frame.pack(fill="x", pady=(0, 12))
        self.bw_slider = CTkSlider(bw_frame, from_=0, to=3, number_of_steps=3, width=200)
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
        self.preview_text.insert("0.0", "192.168.1.1 / 255.255.255.0")
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


class CompareWindow(CTkToplevel):
    """对比框：左右分栏显示原始IP与去重后结果"""

    def __init__(self, parent, raw_ips, deduped_ips, settings, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.settings = settings
        self.title(parent._t("compare_title"))
        self.geometry("1000x700")
        self.minsize(800, 500)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.raw_ips = raw_ips
        self.deduped_ips = deduped_ips
        self.deduped_set = set(str(text) for text, _ in deduped_ips)

        self._build_ui(parent)
        self._populate()
        self.grab_set()
        self.focus_force()
        self.lift()

    def _build_ui(self, parent):
        header = CTkFrame(self, height=50, corner_radius=0, fg_color=("gray90", "gray13"))
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        CTkLabel(header, text=parent._t("compare_title"), font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20, pady=10)

        legend_frame = CTkFrame(header, fg_color="transparent")
        legend_frame.pack(side="right", padx=20)
        CTkLabel(legend_frame, text=parent._t("keep"), text_color="#2ecc71", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 10))
        CTkLabel(legend_frame, text=parent._t("remove"), text_color="#e74c3c", font=ctk.CTkFont(size=12)).pack(side="left")

        content = CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=10)

        # 左侧
        left_card = CTkFrame(content, corner_radius=12, fg_color=("white", "gray16"))
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 5))
        CTkLabel(left_card, text=parent._t("raw_list"), font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 5))
        self.left_text = CTkTextbox(
            left_card, wrap="none",
            font=ctk.CTkFont(family="Consolas", size=self.settings["font_size"]),
            text_color=(self.settings["font_color_light"], self.settings["font_color_dark"]),
            border_color=(self.settings["border_color_light"], self.settings["border_color_dark"]),
            border_width=self.settings["border_width"],
            corner_radius=10, fg_color=("gray98", "gray14"),
        )
        self.left_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 右侧
        right_card = CTkFrame(content, corner_radius=12, fg_color=("white", "gray16"))
        right_card.pack(side="right", fill="both", expand=True, padx=(5, 0))
        CTkLabel(right_card, text=parent._t("deduped_list"), font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 5))
        self.right_text = CTkTextbox(
            right_card, wrap="none",
            font=ctk.CTkFont(family="Consolas", size=self.settings["font_size"]),
            text_color=(self.settings["font_color_light"], self.settings["font_color_dark"]),
            border_color=(self.settings["border_color_light"], self.settings["border_color_dark"]),
            border_width=self.settings["border_width"],
            corner_radius=10, fg_color=("gray98", "gray14"),
        )
        self.right_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 底部搜索栏
        bottom = CTkFrame(self, height=50, fg_color="transparent")
        bottom.pack(fill="x", padx=15, pady=(0, 10))
        bottom.pack_propagate(False)
        CTkLabel(bottom, text=parent._t("search") + ":", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 8))
        self.search_entry = CTkEntry(bottom, width=250, placeholder_text=parent._t("compare_search_placeholder"))
        self.search_entry.pack(side="left", padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self._do_search())
        CTkButton(bottom, text=parent._t("search"), width=80, command=self._do_search).pack(side="left", padx=(0, 5))
        CTkButton(bottom, text=parent._t("clear_highlight"), width=80, fg_color="transparent", border_width=1,
                  hover_color=("gray85", "gray25"), command=self._clear_search).pack(side="left", padx=(0, 5))
        CTkButton(bottom, text=parent._t("close"), width=80, command=self._on_close).pack(side="right")

        for widget in (self.left_text, self.right_text):
            tw = widget._textbox
            tw.tag_configure("keep", background="#27ae60", foreground="white")
            tw.tag_configure("remove", background="#c0392b", foreground="white")
            _search_bg = "#b58900" if ctk.get_appearance_mode() == "Dark" else "#f1c40f"
            _search_fg = "white" if ctk.get_appearance_mode() == "Dark" else "black"
            tw.tag_configure("search", background=_search_bg, foreground=_search_fg)

    def _populate(self):
        left_tw = self.left_text._textbox
        right_tw = self.right_text._textbox
        for text, obj in self.raw_ips:
            line = str(text) + "\n"
            start = left_tw.index("end-1c")
            left_tw.insert("end", line)
            end = left_tw.index("end-1c")
            if str(text) in self.deduped_set:
                left_tw.tag_add("keep", start, end)
            else:
                left_tw.tag_add("remove", start, end)
        for text, obj in self.deduped_ips:
            line = str(text) + "\n"
            start = right_tw.index("end-1c")
            right_tw.insert("end", line)
            end = right_tw.index("end-1c")
            right_tw.tag_add("keep", start, end)
        left_tw.configure(state="disabled")
        right_tw.configure(state="disabled")

    def _do_search(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            return
        for widget in (self.left_text, self.right_text):
            tw = widget._textbox
            tw.tag_remove("search", "1.0", "end")
            pos = "1.0"
            while True:
                pos = tw.search(keyword, pos, stopindex="end", nocase=True)
                if not pos:
                    break
                end_pos = f"{pos}+{len(keyword)}c"
                tw.tag_add("search", pos, end_pos)
                pos = end_pos

    def _clear_search(self):
        for widget in (self.left_text, self.right_text):
            tw = widget._textbox
            tw.tag_remove("search", "1.0", "end")

    def _on_close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


class IPToolApp(CTk):
    IP_PATTERN = re.compile(
        r'\b(?:(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}'
        r'(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)'
        r'(?:\/(?:3[0-2]|[1-2]?\d))?\b'
    )

    DELIMITER_MAP = {
        "换行 (默认)": "\n",
        "逗号 (,)": ",",
        "分号 (;)": ";",
        "竖线 (|)": "|",
        "顿号 (、)": "、",
        "空格": " ",
    }

    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.textboxes = []

        self.title(self._t("app_title"))
        self.geometry("1200x820")
        self.minsize(1000, 700)

        self._build_sidebar()
        self._build_main_area()
        self.apply_settings()

        self.last_result_objects = []
        self.last_raw_objects = []
        self._compare_window = None
        self._settings_window = None

    def _t(self, key):
        """获取当前语言的文本"""
        lang = self.settings.get("language", "zh_CN")
        return TEXTS.get(lang, TEXTS["zh_CN"]).get(key, key)

    def apply_settings(self):
        """将设置应用到所有已注册的文本框"""
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

    def _register_textbox(self, tb):
        self.textboxes.append(tb)
        return tb

    def _build_sidebar(self):
        self.sidebar = CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        self.sidebar.pack_propagate(False)

        CTkLabel(self.sidebar, text=self._t("sidebar_title"), font=ctk.CTkFont(size=26, weight="bold")).pack(pady=(30, 5))
        CTkLabel(self.sidebar, text=self._t("sidebar_subtitle"), font=ctk.CTkFont(size=12), text_color=("gray50", "gray60")).pack(pady=(0, 25))

        delim_card = CTkFrame(self.sidebar, corner_radius=12, fg_color=("gray90", "gray17"))
        delim_card.pack(fill="x", padx=15, pady=(10, 10))
        CTkLabel(delim_card, text=self._t("delimiter"), font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 5))
        self.delim_var = ctk.StringVar(value="换行 (默认)")
        self.delim_combo = CTkComboBox(
            delim_card, values=list(self.DELIMITER_MAP.keys()),
            variable=self.delim_var, width=180, state="readonly",
            dropdown_hover_color=("gray70", "gray30"),
        )
        self.delim_combo.pack(padx=12, pady=(0, 12))

        btn_primary = {"font": ctk.CTkFont(size=15, weight="bold"), "height": 45, "corner_radius": 10}
        btn_secondary = {"font": ctk.CTkFont(size=13), "height": 36, "corner_radius": 10, "fg_color": "transparent", "border_width": 2}

        CTkButton(self.sidebar, text=self._t("start_dedup"), command=self._deduplicate, **btn_primary).pack(fill="x", padx=15, pady=(20, 10))
        CTkButton(self.sidebar, text=self._t("compare_view"), command=self._open_compare, **btn_secondary).pack(fill="x", padx=15, pady=(5, 10))
        CTkButton(self.sidebar, text=self._t("settings"), command=self._open_settings, **btn_secondary).pack(fill="x", padx=15, pady=(5, 10))
        CTkButton(self.sidebar, text=self._t("paste_sample"), command=self._paste_sample, **btn_secondary).pack(fill="x", padx=15, pady=(5, 10))
        CTkButton(self.sidebar, text=self._t("clear_all"), command=self._clear_all,
                  hover_color=("gray80", "gray25"), **btn_secondary).pack(fill="x", padx=15, pady=(5, 10))

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

        # ---------- 输入区域 ----------
        input_card = CTkFrame(content, corner_radius=16, fg_color=("white", "gray16"))
        input_card.pack(fill="both", expand=True, pady=(0, 10))
        input_card.pack_propagate(False)
        input_card.configure(height=280)

        input_header = CTkFrame(input_card, corner_radius=0, fg_color="transparent", height=40)
        input_header.pack(fill="x", padx=15, pady=(10, 0))
        input_header.pack_propagate(False)

        CTkLabel(input_header, text=self._t("input_area"), font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=5)

        # 输入区搜索
        self.input_search_entry = CTkEntry(input_header, width=140, placeholder_text=self._t("search"))
        self.input_search_entry.pack(side="right", padx=(5, 0))
        self.input_search_entry.bind("<Return>", lambda e: self._search_textbox(self.input_text, self.input_search_entry))
        CTkButton(input_header, text="🔍", width=32, height=32, corner_radius=8,
                  command=lambda: self._search_textbox(self.input_text, self.input_search_entry)).pack(side="right", padx=(5, 0))
        CTkButton(input_header, text="✕", width=32, height=32, corner_radius=8, fg_color="transparent", border_width=1,
                  hover_color=("gray85", "gray25"),
                  command=lambda: self._clear_search(self.input_text, self.input_search_entry)).pack(side="right", padx=(5, 0))

        btn_style = {"width": 110, "height": 32, "corner_radius": 8, "font": ctk.CTkFont(size=12)}
        CTkButton(input_header, text=self._t("import_txt"), command=self._import_txt, **btn_style).pack(side="right", padx=(5, 0))
        CTkButton(input_header, text=self._t("import_excel"), command=self._import_excel, **btn_style).pack(side="right", padx=(5, 0))
        CTkButton(input_header, text=self._t("clear_input"), command=self._clear_input,
                  fg_color="transparent", border_width=1, hover_color=("gray85", "gray25"), **btn_style).pack(side="right", padx=(5, 0))

        self.input_text = self._register_textbox(CTkTextbox(
            input_card, wrap="word",
            font=ctk.CTkFont(family="Consolas", size=self.settings["font_size"]),
            text_color=(self.settings["font_color_light"], self.settings["font_color_dark"]),
            border_color=(self.settings["border_color_light"], self.settings["border_color_dark"]),
            border_width=self.settings["border_width"],
            corner_radius=10, fg_color=("gray98", "gray14"),
        ))
        self.input_text.pack(fill="both", expand=True, padx=15, pady=(8, 15))
        self.input_text.insert("0.0", self._t("placeholder_input"))
        self.input_text.bind("<FocusIn>", lambda e: self._on_input_focus())

        _search_bg = "#b58900" if ctk.get_appearance_mode() == "Dark" else "#f1c40f"
        _search_fg = "white" if ctk.get_appearance_mode() == "Dark" else "black"
        self.input_text._textbox.tag_configure("search", background=_search_bg, foreground=_search_fg)

        # ---------- 统计栏 ----------
        self.stats_bar = CTkFrame(content, height=38, corner_radius=10, fg_color=("white", "gray16"))
        self.stats_bar.pack(fill="x", pady=(0, 10))
        self.stats_bar.pack_propagate(False)
        self.stats_label = CTkLabel(self.stats_bar, text=self._t("stats_waiting"), font=ctk.CTkFont(size=13), text_color=("gray40", "gray70"))
        self.stats_label.pack(side="left", padx=15)

        # ---------- 输出区域 ----------
        output_card = CTkFrame(content, corner_radius=16, fg_color=("white", "gray16"))
        output_card.pack(fill="both", expand=True, pady=(0, 10))
        output_card.pack_propagate(False)
        output_card.configure(height=280)

        output_header = CTkFrame(output_card, corner_radius=0, fg_color="transparent", height=40)
        output_header.pack(fill="x", padx=15, pady=(10, 0))
        output_header.pack_propagate(False)

        CTkLabel(output_header, text=self._t("output_area"), font=ctk.CTkFont(size=15, weight="bold")).pack(side="left", padx=5)

        # 输出区搜索
        self.output_search_entry = CTkEntry(output_header, width=140, placeholder_text=self._t("search"))
        self.output_search_entry.pack(side="right", padx=(5, 0))
        self.output_search_entry.bind("<Return>", lambda e: self._search_textbox(self.output_text, self.output_search_entry))
        CTkButton(output_header, text="🔍", width=32, height=32, corner_radius=8,
                  command=lambda: self._search_textbox(self.output_text, self.output_search_entry)).pack(side="right", padx=(5, 0))
        CTkButton(output_header, text="✕", width=32, height=32, corner_radius=8, fg_color="transparent", border_width=1,
                  hover_color=("gray85", "gray25"),
                  command=lambda: self._clear_search(self.output_text, self.output_search_entry)).pack(side="right", padx=(5, 0))

        CTkButton(output_header, text=self._t("export_txt"), command=self._export_txt, **btn_style).pack(side="right", padx=(5, 0))
        CTkButton(output_header, text=self._t("export_excel"), command=self._export_excel, **btn_style).pack(side="right", padx=(5, 0))
        CTkButton(output_header, text=self._t("copy_result"), command=self._copy_result,
                  fg_color="transparent", border_width=1, hover_color=("gray85", "gray25"), **btn_style).pack(side="right", padx=(5, 0))

        self.output_text = self._register_textbox(CTkTextbox(
            output_card, wrap="word",
            font=ctk.CTkFont(family="Consolas", size=self.settings["font_size"]),
            text_color=(self.settings["font_color_light"], self.settings["font_color_dark"]),
            border_color=(self.settings["border_color_light"], self.settings["border_color_dark"]),
            border_width=self.settings["border_width"],
            corner_radius=10, fg_color=("gray98", "gray14"),
        ))
        self.output_text.pack(fill="both", expand=True, padx=15, pady=(8, 15))
        self.output_text._textbox.tag_configure("search", background=_search_bg, foreground=_search_fg)

        # 状态栏
        self.status_label = CTkLabel(content, text=self._t("ready"), font=ctk.CTkFont(size=12), text_color=("gray50", "gray60"))
        self.status_label.pack(anchor="w", padx=5)

    # ==================== 搜索高亮 ====================

    def _search_textbox(self, textbox, entry):
        keyword = entry.get().strip()
        if not keyword:
            return
        tw = textbox._textbox
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

    def _clear_search(self, textbox, entry):
        tw = textbox._textbox
        tw.tag_remove("search", "1.0", "end")
        entry.delete(0, "end")
        self.status_label.configure(text=self._t("search_cleared"))

    # ==================== 业务逻辑 ====================

    def _on_input_focus(self):
        text = self.input_text.get("0.0", "end")
        if "在此粘贴" in text or "Paste IP" in text:
            self.input_text.delete("0.0", "end")
            self.input_text.unbind("<FocusIn>")

    def _toggle_theme(self):
        mode = "Dark" if self.theme_switch.get() == "dark" else "Light"
        ctk.set_appearance_mode(mode)

    def _clear_all(self):
        self.input_text.delete("0.0", "end")
        self.output_text.delete("0.0", "end")
        self.stats_label.configure(text=self._t("stats_waiting"))
        self.status_label.configure(text=self._t("cleared"))
        self.last_result_objects = []
        self.last_raw_objects = []
        if self._compare_window and self._compare_window.winfo_exists():
            self._compare_window.destroy()
            self._compare_window = None

    def _clear_input(self):
        self.input_text.delete("0.0", "end")
        self.status_label.configure(text=self._t("input_cleared"))

    def _paste_sample(self):
        sample = (
            "192.168.1.0/24\n"
            "192.168.1.5\n"
            "192.168.1.100\n"
            "10.0.0.0/8\n"
            "10.0.0.1\n"
            "172.16.0.0/16\n"
            "172.16.5.5\n"
            "8.8.8.8\n"
            "1.1.1.1\n"
            "192.168.1.5\n"
            "10.0.0.1\n"
        )
        self.input_text.delete("0.0", "end")
        self.input_text.insert("0.0", sample)
        self.status_label.configure(text=self._t("pasted_sample"))

    def _open_settings(self):
        if self._settings_window and self._settings_window.winfo_exists():
            self._settings_window.lift()
            self._settings_window.focus_force()
            return
        self._settings_window = SettingsWindow(self)

    def _open_compare(self):
        if not self.last_raw_objects or not self.last_result_objects:
            messagebox.showwarning(self._t("settings_title"), self._t("compare_first"))
            return
        if self._compare_window and self._compare_window.winfo_exists():
            self._compare_window.lift()
            self._compare_window.focus_force()
            return
        self._compare_window = CompareWindow(self, self.last_raw_objects, self.last_result_objects, self.settings)
        self._compare_window.lift()
        self._compare_window.focus_force()

    # ---------- 导入 ----------

    def _import_txt(self):
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.input_text.delete("0.0", "end")
            self.input_text.insert("0.0", content)
            self.status_label.configure(text=self._t("imported_txt").format(os.path.basename(path)))
        except Exception as e:
            messagebox.showerror(self._t("import_fail"), str(e))

    def _import_excel(self):
        if openpyxl is None and pd is None:
            messagebox.showerror(self._t("missing_dep"), self._t("missing_excel_dep"))
            return
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")])
        if not path:
            return
        try:
            texts = []
            if pd is not None:
                xl = pd.ExcelFile(path)
                for sheet in xl.sheet_names:
                    df = xl.parse(sheet)
                    for col in df.columns:
                        texts.append("\n".join(df[col].astype(str)))
            else:
                wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
                for sheet in wb.worksheets:
                    for row in sheet.iter_rows(values_only=True):
                        texts.append("\n".join(str(cell) for cell in row if cell is not None))
            content = "\n".join(texts)
            self.input_text.delete("0.0", "end")
            self.input_text.insert("0.0", content)
            self.status_label.configure(text=self._t("imported_excel").format(os.path.basename(path)))
        except Exception as e:
            messagebox.showerror(self._t("import_fail"), str(e))

    # ---------- 核心去重 ----------

    @staticmethod
    def extract_ips(text: str):
        raw = IPToolApp.IP_PATTERN.findall(text)
        result = []
        for item in raw:
            item = item.strip()
            if not item:
                continue
            try:
                if "/" in item:
                    net = ipaddress.ip_network(item, strict=False)
                    result.append((item, net))
                else:
                    addr = ipaddress.ip_address(item)
                    result.append((item, addr))
            except ValueError:
                continue
        return result

    @staticmethod
    def deduplicate_ips(ip_tuples):
        seen_nets = set()
        ordered_nets = []
        for text, obj in ip_tuples:
            if isinstance(obj, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
                if obj not in seen_nets:
                    seen_nets.add(obj)
                    ordered_nets.append(obj)

        result = []
        seen_nets_output = set()
        seen_hosts_output = set()
        for text, obj in ip_tuples:
            if isinstance(obj, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
                if obj not in seen_nets_output:
                    # 如果当前网段已经被其它更大的网段包含，则跳过
                    contained_by_other = any(
                        obj != net and type(obj) is type(net) and obj.subnet_of(net)
                        for net in ordered_nets
                    )
                    if not contained_by_other:
                        seen_nets_output.add(obj)
                        result.append((text, obj))
            else:
                if obj in seen_hosts_output:
                    continue
                contained = any(
                    type(obj) is type(net.network_address) and obj in net
                    for net in ordered_nets
                )
                if not contained:
                    seen_hosts_output.add(obj)
                    result.append((text, obj))
        return result

    @staticmethod
    def format_ip_tuples(ip_tuples, delimiter="\n"):
        return delimiter.join(text for text, obj in ip_tuples)

    def _deduplicate(self):
        raw_text = self.input_text.get("0.0", "end")
        if not raw_text.strip():
            messagebox.showwarning(self._t("settings_title"), self._t("empty_input"))
            return

        ip_tuples = self.extract_ips(raw_text)
        if not ip_tuples:
            messagebox.showwarning(self._t("settings_title"), self._t("no_ip_found"))
            return

        deduped = self.deduplicate_ips(ip_tuples)
        delimiter = self.DELIMITER_MAP.get(self.delim_var.get(), "\n")
        result_text = self.format_ip_tuples(deduped, delimiter)

        self.output_text.delete("0.0", "end")
        self.output_text.insert("0.0", result_text)

        self.last_raw_objects = ip_tuples
        self.last_result_objects = deduped

        total = len(ip_tuples)
        raw_nets = sum(1 for _, o in ip_tuples if isinstance(o, (ipaddress.IPv4Network, ipaddress.IPv6Network)))
        raw_hosts = total - raw_nets
        removed = total - len(deduped)

        self.stats_label.configure(text=self._t("stats_template").format(total, raw_nets, raw_hosts, len(deduped), removed))
        self.status_label.configure(text=self._t("dedup_done"))

        if self._compare_window and self._compare_window.winfo_exists():
            self._compare_window.destroy()
        self._compare_window = CompareWindow(self, self.last_raw_objects, self.last_result_objects, self.settings)
        self._compare_window.lift()
        self._compare_window.focus_force()

    # ---------- 导出 ----------

    def _export_txt(self):
        text = self.output_text.get("0.0", "end").strip()
        if not text:
            messagebox.showwarning(self._t("settings_title"), self._t("no_content"))
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.status_label.configure(text=self._t("exported_txt").format(os.path.basename(path)))
            messagebox.showinfo(self._t("export_success"), self._t("file_saved_to").format(path))
        except Exception as e:
            messagebox.showerror(self._t("export_fail"), str(e))

    def _export_excel(self):
        text = self.output_text.get("0.0", "end").strip()
        if not text:
            messagebox.showwarning(self._t("settings_title"), self._t("no_content"))
            return
        if pd is None:
            messagebox.showerror(self._t("missing_dep"), self._t("missing_pandas"))
            return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if not path:
            return
        try:
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            df = pd.DataFrame({"IP地址": lines})
            df.to_excel(path, index=False, engine="openpyxl")
            self.status_label.configure(text=self._t("exported_excel").format(os.path.basename(path)))
            messagebox.showinfo(self._t("export_success"), self._t("file_saved_to").format(path))
        except Exception as e:
            messagebox.showerror(self._t("export_fail"), str(e))

    def _copy_result(self):
        text = self.output_text.get("0.0", "end").strip()
        if not text:
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_label.configure(text=self._t("copy_done"))


def main():
    app = IPToolApp()
    app.mainloop()


if __name__ == "__main__":
    main()
