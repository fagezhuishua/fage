#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wireshark 抓包分析工具 (Modern customtkinter GUI 版)
支持 pcap / pcapng 格式
功能：
  - 拖拽或选择抓包文件
  - 深度分析：协议识别、TCP三次握手、TLS证书、错误告警
  - 分步骤展示分析结果
  - 一键重新分析
  - 深色/浅色主题、设置持久化、导出/复制/搜索高亮
"""

import os
import sys
import re
import json
import threading
from collections import Counter, defaultdict
from datetime import datetime

import customtkinter as ctk
from customtkinter import (
    CTk, CTkFrame, CTkButton, CTkLabel, CTkTextbox,
    CTkSwitch, CTkEntry, CTkToplevel, CTkSlider,
    CTkComboBox, CTkProgressBar, CTkTabview,
)
from tkinter import filedialog, messagebox, colorchooser

# ===================== 全局外观设置 =====================
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# ===================== 依赖检查（延迟导入） =====================
# scapy 在 64 位 Windows 下先于 CTk 导入会触发 ctypes OverflowError 打印，
# 因此在应用窗口创建后再延迟导入。
SCAPY_AVAILABLE = False
TLS_AVAILABLE = False
rdpcap = IP = IPv6 = TCP = UDP = ARP = ICMP = DNS = DNSQR = Raw = Ether = None
HTTPRequest = HTTPResponse = None
TLS = TLSClientHello = TLSServerHello = TLSCertificate = TLS_Ext_ServerName = None


def ensure_scapy():
    """延迟导入 scapy，避免与 customtkinter.CTk 初始化冲突。"""
    global SCAPY_AVAILABLE, TLS_AVAILABLE
    global rdpcap, IP, IPv6, TCP, UDP, ARP, ICMP, DNS, DNSQR, Raw, Ether
    global HTTPRequest, HTTPResponse
    global TLS, TLSClientHello, TLSServerHello, TLSCertificate, TLS_Ext_ServerName
    if SCAPY_AVAILABLE:
        return
    try:
        from scapy.all import rdpcap, IP, IPv6, TCP, UDP, ARP, ICMP, DNS, DNSQR, Raw, Ether
        try:
            from scapy.layers.http import HTTPRequest, HTTPResponse
        except ImportError:
            HTTPRequest = HTTPResponse = None
        try:
            from scapy.layers.tls.record import TLS
            from scapy.layers.tls.handshake import TLSClientHello, TLSServerHello, TLSCertificate
            from scapy.layers.tls.extensions import TLS_Ext_ServerName
            TLS_AVAILABLE = True
        except ImportError:
            TLS = TLSClientHello = TLSServerHello = TLSCertificate = TLS_Ext_ServerName = None
            TLS_AVAILABLE = False
        SCAPY_AVAILABLE = True
    except ImportError:
        SCAPY_AVAILABLE = False
        TLS_AVAILABLE = False


# ===================== 配置与多语言 =====================
SETTINGS_FILE = "packet_settings.json"

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
        "app_title": "抓包分析工具",
        "sidebar_title": "抓包分析",
        "sidebar_subtitle": "pcap / pcapng 深度分析工具",
        "choose_file": "📁 选择文件",
        "reanalyze": "🔄 重新分析",
        "analysis_config": "⚙️ 分析需求",
        "clear_results": "🗑️ 清空结果",
        "settings": "⚙️ 设置",
        "theme": "外观主题",
        "dark_mode": "深色模式",
        "version": "v2.0 Modern Edition",
        "workbench": "抓包分析工作台",
        "welcome_card_title": "导入抓包文件",
        "drop_hint": "点击选择文件\n或将 pcap / pcapng 文件拖拽到此处",
        "drop_hint_ok": "点击选择文件\n或将 pcap / pcapng 文件拖拽到此处 ✓",
        "supported_formats": "支持 .pcap / .pcapng 格式 | 需要安装 scapy",
        "missing_scapy": "未安装 scapy，请执行：pip install scapy",
        "config_title": "分析需求配置",
        "target_ips": "重点分析 IP（多个用逗号分隔）：",
        "focus_errors": "关注错误类型（多个用逗号分隔，如 RST,重传,TLS）：",
        "question": "具体问题描述（用于结论针对性分析）：",
        "save": "保存",
        "cancel": "取消",
        "ready": "就绪",
        "analyzing": "正在深度分析抓包数据...",
        "loading": "正在加载文件...",
        "please_select_file": "请选择抓包文件开始分析",
        "current_step": "当前步骤：{}  ({}/{})",
        "file_overview": "文件概览",
        "protocol_stats": "协议统计",
        "tcp_analysis": "TCP 连接分析",
        "tls_analysis": "TLS/证书分析",
        "errors": "错误与异常",
        "communication": "通信详情",
        "conclusion": "综合结论",
        "export_txt": "导出 .txt",
        "copy_result": "复制结果",
        "search": "搜索",
        "clear_highlight": "清除高亮",
        "search_not_found": "未找到: {}",
        "search_highlight": "高亮显示: {}",
        "search_cleared": "已清除搜索高亮",
        "copy_done": "结果已复制到剪贴板 ✓",
        "no_content": "没有可导出的内容，请先执行分析。",
        "export_success": "导出成功",
        "export_fail": "导出失败",
        "file_saved_to": "文件已保存到:\n{}",
        "analysis_failed": "分析失败",
        "invalid_file": "未找到有效的抓包文件。",
        "missing_dep": "缺少依赖",
        "settings_title": "设置",
        "language": "界面语言",
        "font_size": "字体大小",
        "font_color_light": "浅色模式字体颜色",
        "font_color_dark": "深色模式字体颜色",
        "border_color_light": "浅色模式边框颜色",
        "border_color_dark": "深色模式边框颜色",
        "border_width": "边框粗细",
        "choose_color": "选择颜色",
        "restart_required": "语言设置已更改，重启程序后生效。",
        "matched_mark": "★",
    },
    "en": {
        "app_title": "Packet Analyzer",
        "sidebar_title": "Packet Analysis",
        "sidebar_subtitle": "Deep analyzer for pcap / pcapng",
        "choose_file": "📁 Choose File",
        "reanalyze": "🔄 Re-analyze",
        "analysis_config": "⚙️ Config",
        "clear_results": "🗑️ Clear",
        "settings": "⚙️ Settings",
        "theme": "Theme",
        "dark_mode": "Dark Mode",
        "version": "v2.0 Modern Edition",
        "workbench": "Packet Analysis Workbench",
        "welcome_card_title": "Import Capture File",
        "drop_hint": "Click to choose\nor drag pcap / pcapng here",
        "drop_hint_ok": "Click to choose\nor drag pcap / pcapng here ✓",
        "supported_formats": "Supports .pcap / .pcapng | scapy required",
        "missing_scapy": "scapy not installed. Run: pip install scapy",
        "config_title": "Analysis Configuration",
        "target_ips": "Target IPs (comma separated):",
        "focus_errors": "Focus errors (comma separated, e.g. RST,retrans,TLS):",
        "question": "Specific question (for targeted conclusion):",
        "save": "Save",
        "cancel": "Cancel",
        "ready": "Ready",
        "analyzing": "Deep analyzing capture...",
        "loading": "Loading file...",
        "please_select_file": "Please select a capture file to start",
        "current_step": "Current step: {}  ({}/{})",
        "file_overview": "File Overview",
        "protocol_stats": "Protocol Stats",
        "tcp_analysis": "TCP Analysis",
        "tls_analysis": "TLS/Cert Analysis",
        "errors": "Errors & Anomalies",
        "communication": "Communication",
        "conclusion": "Conclusion",
        "export_txt": "Export .txt",
        "copy_result": "Copy Result",
        "search": "Search",
        "clear_highlight": "Clear Highlight",
        "search_not_found": "Not found: {}",
        "search_highlight": "Highlighting: {}",
        "search_cleared": "Search highlight cleared",
        "copy_done": "Result copied to clipboard ✓",
        "no_content": "No content to export. Please analyze first.",
        "export_success": "Export Successful",
        "export_fail": "Export Failed",
        "file_saved_to": "File saved to:\n{}",
        "analysis_failed": "Analysis Failed",
        "invalid_file": "No valid capture file found.",
        "missing_dep": "Missing Dependencies",
        "settings_title": "Settings",
        "language": "Language",
        "font_size": "Font Size",
        "font_color_light": "Light Mode Font Color",
        "font_color_dark": "Dark Mode Font Color",
        "border_color_light": "Light Mode Border Color",
        "border_color_dark": "Dark Mode Border Color",
        "border_width": "Border Width",
        "choose_color": "Choose Color",
        "restart_required": "Language changed. Please restart the application.",
        "matched_mark": "★",
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


# ===================== 分析引擎（保持原逻辑） =====================
class PacketAnalyzer:
    def __init__(self, file_path, config=None):
        self.file_path = file_path
        self.config = config or {}
        self.packets = []
        self.stats = {}
        self.error_msg = None
        self.pkt_infos = []
        self._tcp_handshake_cache = None
        self._tls_cache = None

    def load(self):
        try:
            self.packets = rdpcap(self.file_path)
            return True
        except Exception as e:
            self.error_msg = str(e)
            return False

    def analyze(self):
        if not self.packets:
            return {}
        self._preprocess()
        self._tcp_handshake_cache = self._analyze_tcp_handshake()
        self._tls_cache = self._analyze_tls()
        stats = {
            'file_info': self._analyze_file_info(),
            'protocol': self._analyze_protocol(),
            'traffic_timeline': self._analyze_traffic_timeline(),
            'tcp_handshake': self._tcp_handshake_cache,
            'tls_analysis': self._tls_cache,
            'errors': self._analyze_errors(),
            'ip_comm': self._analyze_ip_communication(),
            'port_session': self._analyze_port_session(),
            'conclusion': '',
        }
        stats['conclusion'] = self._generate_conclusion(stats)
        self.stats = stats
        return stats

    # ---------- 预处理 ----------
    def _preprocess(self):
        self.pkt_infos = []
        for idx, p in enumerate(self.packets):
            info = {
                'idx': idx + 1,
                'time': float(p.time),
                'len': len(p),
                'layers': [],
                'src_ip': None,
                'dst_ip': None,
                'src_port': None,
                'dst_port': None,
                'proto': None,
                'tcp_flags': None,
                'tcp_seq': None,
                'tcp_ack': None,
                'tcp_window': None,
                'http_request': None,
                'http_response': None,
                'dns_qry': None,
                'dns_rcode': None,
                'icmp_type': None,
                'icmp_code': None,
                'tls_info': None,
                'is_retransmission': False,
                'is_dup_ack': False,
            }

            if p.haslayer(Ether):
                info['layers'].append('Ethernet')
            if p.haslayer(ARP):
                info['layers'].append('ARP')
                info['proto'] = 'ARP'
            if p.haslayer(IP):
                info['layers'].append('IP')
                info['src_ip'] = p[IP].src
                info['dst_ip'] = p[IP].dst
            if p.haslayer(IPv6):
                info['layers'].append('IPv6')
                info['src_ip'] = p[IPv6].src
                info['dst_ip'] = p[IPv6].dst
            if p.haslayer(ICMP):
                info['layers'].append('ICMP')
                info['proto'] = 'ICMP'
                info['icmp_type'] = p[ICMP].type
                info['icmp_code'] = p[ICMP].code
            if p.haslayer(TCP):
                info['layers'].append('TCP')
                info['proto'] = 'TCP'
                tcp = p[TCP]
                info['src_port'] = tcp.sport
                info['dst_port'] = tcp.dport
                info['tcp_flags'] = tcp.sprintf('%TCP.flags%')
                info['tcp_seq'] = tcp.seq
                info['tcp_ack'] = tcp.ack
                info['tcp_window'] = tcp.window

                # HTTP detection
                if HTTPRequest and p.haslayer(HTTPRequest):
                    info['layers'].append('HTTP')
                    info['proto'] = 'HTTP'
                    req = p[HTTPRequest]
                    info['http_request'] = {
                        'method': req.Method.decode() if isinstance(req.Method, bytes) else str(req.Method),
                        'host': req.Host.decode() if isinstance(req.Host, bytes) else str(req.Host),
                        'path': req.Path.decode() if isinstance(req.Path, bytes) else str(req.Path),
                    }
                elif HTTPResponse and p.haslayer(HTTPResponse):
                    info['layers'].append('HTTP')
                    info['proto'] = 'HTTP'
                    resp = p[HTTPResponse]
                    status = resp.Status_Code
                    info['http_response'] = {
                        'status': status.decode() if isinstance(status, bytes) else str(status),
                    }
                elif info['dst_port'] in (80, 8080, 8000, 3128, 8888) or info['src_port'] in (80, 8080, 8000, 3128, 8888):
                    info['layers'].append('HTTP')
                    info['proto'] = 'HTTP'

                # TLS detection
                tls_ports = (443, 8443, 465, 587, 993, 995, 3389)
                if info['dst_port'] in tls_ports or info['src_port'] in tls_ports:
                    if TLS_AVAILABLE and p.haslayer(TLS):
                        info['layers'].append('TLS')
                        info['proto'] = 'TLS'
                        info['tls_info'] = self._parse_tls_layer(p[TLS])
                    else:
                        info['layers'].append('TLS')
                        info['proto'] = 'TLS'

            if p.haslayer(UDP):
                info['layers'].append('UDP')
                if info['proto'] is None:
                    info['proto'] = 'UDP'
                udp = p[UDP]
                info['src_port'] = udp.sport
                info['dst_port'] = udp.dport
                if p.haslayer(DNS):
                    info['layers'].append('DNS')
                    info['proto'] = 'DNS'
                    dns = p[DNS]
                    info['dns_rcode'] = dns.rcode
                    if p.haslayer(DNSQR):
                        qname = p[DNSQR].qname
                        if isinstance(qname, bytes):
                            qname = qname.decode('utf-8', errors='ignore').rstrip('.')
                        info['dns_qry'] = qname

            if info['proto'] is None:
                info['proto'] = 'Other'

            self.pkt_infos.append(info)

        self._mark_retransmissions()

    def _parse_tls_layer(self, tls):
        result = {'type': 'Unknown'}
        if TLSClientHello and tls.haslayer(TLSClientHello):
            ch = tls[TLSClientHello]
            result['type'] = 'ClientHello'
            try:
                result['version'] = ch.version.name if hasattr(ch.version, 'name') else str(ch.version)
            except Exception:
                result['version'] = str(ch.version)
            sni = []
            try:
                for ext in ch.ext or []:
                    if TLS_Ext_ServerName and ext.haslayer(TLS_Ext_ServerName):
                        for sn in ext.servernames:
                            name = getattr(sn, 'servername', b'')
                            if isinstance(name, bytes):
                                name = name.decode('utf-8', errors='ignore')
                            if name:
                                sni.append(name)
            except Exception:
                pass
            result['sni'] = sni
        elif TLSServerHello and tls.haslayer(TLSServerHello):
            sh = tls[TLSServerHello]
            result['type'] = 'ServerHello'
            try:
                result['version'] = sh.version.name if hasattr(sh.version, 'name') else str(sh.version)
            except Exception:
                result['version'] = str(sh.version)
            try:
                result['cipher'] = sh.cipher.name if hasattr(sh.cipher, 'name') else str(sh.cipher)
            except Exception:
                result['cipher'] = str(sh.cipher)
        elif TLSCertificate and tls.haslayer(TLSCertificate):
            result['type'] = 'Certificate'
            try:
                certs = tls[TLSCertificate].certs
                result['cert_count'] = len(certs)
            except Exception:
                result['cert_count'] = 0
        return result

    def _ip_match(self, ip):
        targets = self.config.get('target_ips', [])
        if not targets:
            return False
        return ip in targets

    def _error_match(self, category, detail):
        focus = self.config.get('focus_errors', [])
        if not focus:
            return False
        text = f"{category} {detail}"
        for kw in focus:
            if kw and kw.lower() in text.lower():
                return True
        return False

    def _mark_retransmissions(self):
        flow_packets = defaultdict(list)
        for info in self.pkt_infos:
            if info['proto'] in ('TCP', 'HTTP', 'TLS') and info['tcp_seq'] is not None:
                key = tuple(sorted([(info['src_ip'], info['src_port']), (info['dst_ip'], info['dst_port'])]))
                flow_packets[key].append(info)

        for flow, pkts in flow_packets.items():
            pkts.sort(key=lambda x: x['time'])
            seen_seq = defaultdict(list)
            seen_ack = defaultdict(list)
            for p in pkts:
                flags = p['tcp_flags'] or ''
                # 重传检测（纯 ACK 不算）
                if p['tcp_seq'] is not None and (len(flags) > 1 or flags == 'S'):
                    seq_key = (p['src_ip'], p['src_port'], p['dst_ip'], p['dst_port'], p['tcp_seq'])
                    seen_seq[seq_key].append(p)
                    if len(seen_seq[seq_key]) > 1:
                        p['is_retransmission'] = True
                # 重复 ACK 检测
                if flags == 'A' and p['tcp_ack'] is not None:
                    ack_key = (p['src_ip'], p['src_port'], p['dst_ip'], p['dst_port'], p['tcp_ack'])
                    seen_ack[ack_key].append(p)
                    if len(seen_ack[ack_key]) >= 3:
                        for pp in seen_ack[ack_key]:
                            pp['is_dup_ack'] = True

    # ---------- 各维度分析 ----------
    def _analyze_file_info(self):
        total = len(self.packets)
        size = os.path.getsize(self.file_path)
        times = [p['time'] for p in self.pkt_infos]
        start = datetime.fromtimestamp(min(times)).strftime('%Y-%m-%d %H:%M:%S') if times else 'N/A'
        end = datetime.fromtimestamp(max(times)).strftime('%Y-%m-%d %H:%M:%S') if times else 'N/A'
        duration = max(times) - min(times) if times else 0
        avg_len = sum(len(p) for p in self.packets) / total if total else 0
        return {
            'file_name': os.path.basename(self.file_path),
            'file_path': self.file_path,
            'file_size_mb': round(size / 1024 / 1024, 2),
            'packet_count': total,
            'start_time': start,
            'end_time': end,
            'duration_sec': round(duration, 2),
            'avg_packet_len': round(avg_len, 2),
        }

    def _analyze_protocol(self):
        cnt = Counter(p['proto'] for p in self.pkt_infos)
        total = len(self.pkt_infos)
        result = []
        for proto, num in cnt.most_common():
            result.append({'protocol': proto, 'count': num, 'percent': round(num / total * 100, 2) if total else 0})
        return result

    def _analyze_traffic_timeline(self):
        if not self.pkt_infos:
            return {'timeline': [], 'peak': None, 'duration': 0}
        times = [p['time'] for p in self.pkt_infos]
        start = min(times)
        buckets = defaultdict(int)
        for t in times:
            buckets[int((t - start) / 10)] += 1
        timeline = [{'time_sec': k * 10, 'count': v} for k, v in sorted(buckets.items())]
        peak = max(timeline, key=lambda x: x['count']) if timeline else None
        return {
            'timeline': timeline,
            'peak': peak,
            'duration': round(max(times) - start, 2) if len(times) > 1 else 0,
        }

    def _analyze_tcp_handshake(self):
        tcp_packets = [p for p in self.pkt_infos if p['proto'] in ('TCP', 'HTTP', 'TLS') and p['tcp_flags']]
        handshakes = []
        half_opens = []
        refused = []
        resets = []

        # 索引所有 SYN
        syns = {}
        for p in tcp_packets:
            flags = p['tcp_flags']
            if 'S' in flags and 'A' not in flags:
                key = (p['src_ip'], p['src_port'], p['dst_ip'], p['dst_port'])
                syns[key] = p

        for syn_key, syn_pkt in syns.items():
            client_ip, client_port, server_ip, server_port = syn_key
            syn_ack_key = (server_ip, server_port, client_ip, client_port)
            syn_ack_pkt = None
            ack_pkt = None

            # 找 SYN+ACK
            for p in tcp_packets:
                if (p['src_ip'], p['src_port'], p['dst_ip'], p['dst_port']) == syn_ack_key:
                    flags = p['tcp_flags']
                    if 'S' in flags and 'A' in flags:
                        if p['tcp_ack'] == syn_pkt['tcp_seq'] + 1:
                            syn_ack_pkt = p
                            break

            if syn_ack_pkt:
                # 找最终 ACK
                ack_key = (client_ip, client_port, server_ip, server_port)
                for p in tcp_packets:
                    if (p['src_ip'], p['src_port'], p['dst_ip'], p['dst_port']) == ack_key:
                        flags = p['tcp_flags']
                        if 'A' in flags and 'S' not in flags:
                            if p['tcp_ack'] == syn_ack_pkt['tcp_seq'] + 1 and p['time'] > syn_ack_pkt['time']:
                                ack_pkt = p
                                break

                matched = self._ip_match(client_ip) or self._ip_match(server_ip)
                if ack_pkt:
                    handshakes.append({
                        'client': client_ip, 'server': server_ip,
                        'client_port': client_port, 'server_port': server_port,
                        'syn_time': syn_pkt['time'],
                        'syn_ack_time': syn_ack_pkt['time'],
                        'ack_time': ack_pkt['time'],
                        'latency_syn_to_synack': round(syn_ack_pkt['time'] - syn_pkt['time'], 6),
                        'latency_total': round(ack_pkt['time'] - syn_pkt['time'], 6),
                        'matched': matched,
                    })
                else:
                    half_opens.append({
                        'client': client_ip, 'server': server_ip,
                        'client_port': client_port, 'server_port': server_port,
                        'syn_time': syn_pkt['time'],
                        'note': '收到 SYN+ACK，但未捕获到最终 ACK（可能丢包或握手未完成）',
                        'matched': matched,
                    })
            else:
                # 检查 RST
                rst_found = False
                matched = self._ip_match(client_ip) or self._ip_match(server_ip)
                for p in tcp_packets:
                    if ((p['src_ip'], p['src_port'], p['dst_ip'], p['dst_port']) == syn_ack_key or
                        (p['src_ip'], p['src_port'], p['dst_ip'], p['dst_port']) == syn_key):
                        if 'R' in p['tcp_flags']:
                            refused.append({
                                'client': client_ip, 'server': server_ip,
                                'client_port': client_port, 'server_port': server_port,
                                'rst_time': p['time'],
                                'note': '连接被 RST 重置（端口未开放或防火墙拒绝）',
                                'matched': matched,
                            })
                            rst_found = True
                            break
                if not rst_found:
                    half_opens.append({
                        'client': client_ip, 'server': server_ip,
                        'client_port': client_port, 'server_port': server_port,
                        'syn_time': syn_pkt['time'],
                        'note': '仅发出 SYN，未收到 SYN+ACK（目标不可达、超时或被过滤）',
                        'matched': matched,
                    })

        for p in tcp_packets:
            if 'R' in p['tcp_flags']:
                resets.append({
                    'time': p['time'],
                    'src': p['src_ip'], 'dst': p['dst_ip'],
                    'src_port': p['src_port'], 'dst_port': p['dst_port'],
                    'matched': self._ip_match(p['src_ip']) or self._ip_match(p['dst_ip']),
                })

        return {
            'handshakes': handshakes,
            'half_opens': half_opens,
            'refused': refused,
            'resets': resets,
            'total_syns': len(syns),
            'successful_handshakes': len(handshakes),
        }

    def _analyze_tls(self):
        tls_packets = [p for p in self.pkt_infos if p['proto'] == 'TLS']
        if not tls_packets:
            return None

        result = {
            'total_tls_packets': len(tls_packets),
            'client_hellos': [],
            'server_hellos': [],
            'certificates': [],
            'alerts': [],
            'weak_versions': [],
            'sni_list': [],
        }

        for p in tls_packets:
            tls_info = p.get('tls_info')
            if not tls_info:
                continue
            t = tls_info['type']
            matched = self._ip_match(p['src_ip']) or self._ip_match(p['dst_ip'])
            if t == 'ClientHello':
                result['client_hellos'].append({
                    'time': p['time'], 'src': p['src_ip'], 'dst': p['dst_ip'],
                    'sni': tls_info.get('sni', []),
                    'version': tls_info.get('version', 'Unknown'),
                    'matched': matched,
                })
                result['sni_list'].extend(tls_info.get('sni', []))
                ver = str(tls_info.get('version', ''))
                if 'SSL' in ver or 'TLS 1.0' in ver or 'TLS 1.1' in ver:
                    result['weak_versions'].append({'src': p['src_ip'], 'version': ver, 'matched': matched})
            elif t == 'ServerHello':
                result['server_hellos'].append({
                    'time': p['time'], 'src': p['src_ip'], 'dst': p['dst_ip'],
                    'version': tls_info.get('version', 'Unknown'),
                    'cipher': tls_info.get('cipher', 'Unknown'),
                    'matched': matched,
                })
                ver = str(tls_info.get('version', ''))
                if 'SSL' in ver or 'TLS 1.0' in ver or 'TLS 1.1' in ver:
                    result['weak_versions'].append({'src': p['src_ip'], 'version': ver, 'matched': matched})
            elif t == 'Certificate':
                result['certificates'].append({
                    'time': p['time'], 'src': p['src_ip'],
                    'cert_count': tls_info.get('cert_count', 0),
                    'matched': matched,
                })

        # TLS Alert 扫描（基于原始 scapy 包）
        if TLS_AVAILABLE:
            for idx, p in enumerate(self.packets):
                if p.haslayer(TLS):
                    tls = p[TLS]
                    if hasattr(tls, 'type') and str(tls.type) == 'alert':
                        info = self.pkt_infos[idx]
                        result['alerts'].append({
                            'time': info['time'], 'src': info['src_ip'], 'dst': info['dst_ip'],
                            'src_port': info['src_port'], 'dst_port': info['dst_port'],
                            'matched': self._ip_match(info['src_ip']) or self._ip_match(info['dst_ip']),
                        })

        return result

    def _analyze_errors(self):
        errors = []

        def mkerr(level, category, detail, time_val, src_ip=None, dst_ip=None):
            matched = self._error_match(category, detail)
            if src_ip or dst_ip:
                matched = matched or self._ip_match(src_ip or '') or self._ip_match(dst_ip or '')
            return {'level': level, 'category': category, 'detail': detail, 'time': time_val, 'matched': matched}

        # TCP RST
        for p in self.pkt_infos:
            if p['tcp_flags'] and 'R' in p['tcp_flags']:
                errors.append(mkerr('高', 'TCP 连接重置',
                    f"{p['src_ip']}:{p['src_port']} -> {p['dst_ip']}:{p['dst_port']} 发送 RST，连接被强制终止",
                    p['time'], p['src_ip'], p['dst_ip']))

        # 重传
        for p in self.pkt_infos:
            if p.get('is_retransmission'):
                errors.append(mkerr('中', 'TCP 重传',
                    f"{p['src_ip']}:{p['src_port']} -> {p['dst_ip']}:{p['dst_port']} Seq={p['tcp_seq']} 疑似重传",
                    p['time'], p['src_ip'], p['dst_ip']))

        # 重复 ACK
        for p in self.pkt_infos:
            if p.get('is_dup_ack'):
                errors.append(mkerr('中', 'TCP 重复 ACK',
                    f"{p['src_ip']}:{p['src_port']} -> {p['dst_ip']}:{p['dst_port']} Ack={p['tcp_ack']} 重复确认",
                    p['time'], p['src_ip'], p['dst_ip']))

        # 零窗口
        for p in self.pkt_infos:
            if p.get('tcp_window') == 0 and p['tcp_flags'] and 'A' in p['tcp_flags']:
                errors.append(mkerr('中', 'TCP 零窗口',
                    f"{p['src_ip']}:{p['src_port']} Advertised Window=0，接收缓冲区已满",
                    p['time'], p['src_ip'], p['dst_ip']))

        # ICMP 错误
        icmp_map = {
            3: {0: '网络不可达', 1: '主机不可达', 2: '协议不可达', 3: '端口不可达'},
            11: {0: '传输中 TTL 耗尽', 1: '分片重组 TTL 耗尽'},
            12: {0: 'IP 参数错误'},
        }
        for p in self.pkt_infos:
            if p['icmp_type'] is not None:
                desc = icmp_map.get(p['icmp_type'], {}).get(p['icmp_code'], f"ICMP Type={p['icmp_type']} Code={p['icmp_code']}")
                errors.append(mkerr('高' if p['icmp_type'] == 3 else '中', 'ICMP 异常',
                    f"{p['src_ip']} -> {p['dst_ip']} {desc}", p['time'], p['src_ip'], p['dst_ip']))

        # HTTP 错误
        for p in self.pkt_infos:
            if p.get('http_response'):
                status = p['http_response'].get('status', '')
                try:
                    s = int(status)
                    if s >= 500:
                        errors.append(mkerr('高', 'HTTP 服务器错误', f"{p['src_ip']} 返回 HTTP {status}", p['time'], p['src_ip'], p['dst_ip']))
                    elif s >= 400:
                        errors.append(mkerr('中', 'HTTP 客户端错误', f"{p['src_ip']} 返回 HTTP {status}", p['time'], p['src_ip'], p['dst_ip']))
                except ValueError:
                    pass

        # DNS 错误
        dns_err = {2: 'SERVFAIL', 3: 'NXDOMAIN', 5: 'REFUSED'}
        for p in self.pkt_infos:
            if p.get('dns_rcode') in dns_err:
                errors.append(mkerr('中', 'DNS 解析异常',
                    f"查询 {p.get('dns_qry', 'Unknown')} 返回 {dns_err[p['dns_rcode']]} (rcode={p['dns_rcode']})",
                    p['time'], p['src_ip'], p['dst_ip']))

        # TLS Alert
        if self._tls_cache:
            for alert in self._tls_cache.get('alerts', []):
                errors.append(mkerr('高', 'TLS 告警',
                    f"{alert['src']}:{alert['src_port']} -> {alert['dst']}:{alert['dst_port']} 触发 TLS Alert（握手失败或证书错误）",
                    alert['time'], alert['src'], alert['dst']))

        # 半开连接
        if self._tcp_handshake_cache:
            for ho in self._tcp_handshake_cache.get('half_opens', []):
                errors.append(mkerr('中', 'TCP 半开连接',
                    f"{ho['client']}:{ho['client_port']} -> {ho['server']}:{ho['server_port']} {ho['note']}",
                    ho['syn_time'], ho['client'], ho['server']))

        errors.sort(key=lambda x: x['time'])
        if not errors:
            errors.append({'level': '低', 'category': '无显著异常', 'detail': '基于当前规则未检测到明显错误流量', 'time': 0, 'matched': False})
        return errors

    def _analyze_ip_communication(self):
        src_ips = Counter()
        dst_ips = Counter()
        ip_pairs = Counter()
        mac_set = set()
        ip_bytes = Counter()
        for p in self.pkt_infos:
            if p['src_ip']:
                src_ips[p['src_ip']] += 1
                ip_bytes[p['src_ip']] += p['len']
            if p['dst_ip']:
                dst_ips[p['dst_ip']] += 1
                ip_bytes[p['dst_ip']] += p['len']
            if p['src_ip'] and p['dst_ip']:
                ip_pairs[f"{p['src_ip']} -> {p['dst_ip']}"] += 1
        return {
            'src_top10': src_ips.most_common(10),
            'dst_top10': dst_ips.most_common(10),
            'pair_top10': ip_pairs.most_common(10),
            'unique_ips': len(set(list(src_ips.keys()) + list(dst_ips.keys()))),
            'ip_bytes': ip_bytes.most_common(10),
        }

    def _analyze_port_session(self):
        src_ports = Counter()
        dst_ports = Counter()
        tcp_sessions = set()
        udp_sessions = set()
        service_map = {
            22: 'SSH', 23: 'Telnet', 53: 'DNS', 80: 'HTTP', 110: 'POP3',
            143: 'IMAP', 443: 'HTTPS', 445: 'SMB', 465: 'SMTPS', 587: 'SMTP',
            993: 'IMAPS', 995: 'POP3S', 3389: 'RDP', 8080: 'HTTP-Proxy', 8443: 'HTTPS-Alt'
        }
        services = Counter()

        for p in self.pkt_infos:
            if p['proto'] in ('TCP', 'HTTP', 'TLS'):
                sp, dp = p['src_port'], p['dst_port']
                src_ports[sp] += 1
                dst_ports[dp] += 1
                if p['src_ip'] and p['dst_ip']:
                    sess = tuple(sorted([(p['src_ip'], sp), (p['dst_ip'], dp)]))
                    tcp_sessions.add(sess)
                    for port in (dp, sp):
                        if port in service_map:
                            services[service_map[port]] += 1
            elif p['proto'] == 'UDP':
                sp, dp = p['src_port'], p['dst_port']
                src_ports[sp] += 1
                dst_ports[dp] += 1
                if p['src_ip'] and p['dst_ip']:
                    sess = tuple(sorted([(p['src_ip'], sp), (p['dst_ip'], dp)]))
                    udp_sessions.add(sess)
                    for port in (dp, sp):
                        if port in service_map:
                            services[service_map[port]] += 1

        return {
            'src_ports_top10': src_ports.most_common(10),
            'dst_ports_top10': dst_ports.most_common(10),
            'tcp_sessions': len(tcp_sessions),
            'udp_sessions': len(udp_sessions),
            'services': services.most_common(),
        }

    def _generate_conclusion(self, stats):
        fi = stats['file_info']
        proto = stats['protocol']
        tcp_hs = stats['tcp_handshake']
        tls = stats['tls_analysis']
        errs = stats['errors']
        ipcomm = stats['ip_comm']
        port = stats['port_session']
        timeline = stats['traffic_timeline']

        lines = []
        lines.append("=" * 60)
        lines.append("📊 Wireshark 深度抓包分析结论报告")
        lines.append("=" * 60)
        lines.append("")

        lines.append(f"【文件信息】")
        lines.append(f"  文件名称：{fi['file_name']}")
        lines.append(f"  文件大小：{fi['file_size_mb']} MB")
        lines.append(f"  数据包数：{fi['packet_count']} 个")
        lines.append(f"  时间跨度：{fi['start_time']} ~ {fi['end_time']}（持续 {fi['duration_sec']} 秒）")
        lines.append("")

        lines.append(f"【协议分布】")
        if proto:
            top3 = proto[:3]
            lines.append(f"  主要协议：" + "、".join([f"{p['protocol']}({p['percent']}%)" for p in top3]))
        lines.append("")

        lines.append(f"【TCP 连接分析】")
        lines.append(f"  SYN 总数：{tcp_hs['total_syns']} 个")
        lines.append(f"  成功三次握手：{tcp_hs['successful_handshakes']} 个")
        if tcp_hs['half_opens']:
            lines.append(f"  ⚠️ 半开/异常连接：{len(tcp_hs['half_opens'])} 个（可能丢包、超时或扫描）")
        if tcp_hs['refused']:
            lines.append(f"  ⚠️ RST 拒绝连接：{len(tcp_hs['refused'])} 个（端口未开放或防火墙拦截）")
        if tcp_hs['resets']:
            lines.append(f"  ⚠️ 总 RST 包：{len(tcp_hs['resets'])} 个")
        lines.append("")

        lines.append(f"【TLS/SSL 分析】")
        if tls:
            lines.append(f"  TLS 包总数：{tls['total_tls_packets']} 个")
            lines.append(f"  ClientHello：{len(tls['client_hellos'])} 个")
            lines.append(f"  ServerHello：{len(tls['server_hellos'])} 个")
            if tls['sni_list']:
                unique_sni = list(dict.fromkeys(tls['sni_list']))[:5]
                lines.append(f"  SNI 域名：{', '.join(unique_sni)}")
            if tls['weak_versions']:
                lines.append(f"  ⚠️ 发现弱 TLS/SSL 版本通信：{len(tls['weak_versions'])} 次")
            if tls['alerts']:
                lines.append(f"  ⚠️ TLS Alert：{len(tls['alerts'])} 次（证书或握手异常）")
        else:
            lines.append(f"  未检测到 TLS 流量")
        lines.append("")

        lines.append(f"【错误与风险】")
        high = [e for e in errs if e['level'] == '高']
        mid = [e for e in errs if e['level'] == '中']
        if high:
            lines.append(f"  高风险项：{len(high)} 个")
            for e in high[:5]:
                lines.append(f"    - [{e['category']}] {e['detail']}")
            if len(high) > 5:
                lines.append(f"    ... 等共 {len(high)} 项")
        if mid:
            lines.append(f"  中风险项：{len(mid)} 个")
        if not high and not mid:
            lines.append(f"  ✅ 未发现显著异常")
        lines.append("")

        lines.append(f"【通信概况】")
        lines.append(f"  独立 IP 数：{ipcomm['unique_ips']} 个")
        lines.append(f"  TCP 会话数：{port['tcp_sessions']} 个")
        lines.append(f"  UDP 会话数：{port['udp_sessions']} 个")
        if timeline['peak']:
            lines.append(f"  流量峰值：{timeline['peak']['count']} 包/10秒")
        lines.append("")

        # 需求匹配汇总
        cfg_ips = self.config.get('target_ips', [])
        cfg_focus = self.config.get('focus_errors', [])
        cfg_question = self.config.get('question', '')
        matched_errs = [e for e in errs if e.get('matched')]
        matched_hs = [h for h in tcp_hs.get('handshakes', []) if h.get('matched')]
        matched_ho = [h for h in tcp_hs.get('half_opens', []) if h.get('matched')]
        matched_rst = [r for r in tcp_hs.get('resets', []) if r.get('matched')]

        lines.append(f"【需求匹配结果】")
        if cfg_ips:
            lines.append(f"  重点 IP：{', '.join(cfg_ips)}")
        if cfg_focus:
            lines.append(f"  关注错误：{', '.join(cfg_focus)}")
        if matched_errs or matched_hs or matched_ho or matched_rst:
            lines.append(f"  ⭐ 共发现 {len(matched_errs)} 项匹配错误，{len(matched_hs)} 个匹配握手，{len(matched_ho)} 个匹配半开连接，{len(matched_rst)} 个匹配 RST")
            if matched_errs:
                lines.append(f"  关键异常：")
                for e in matched_errs[:5]:
                    lines.append(f"    - [{e['level']}] {e['category']}：{e['detail']}")
        else:
            lines.append(f"  未在抓包中发现与配置需求强匹配的内容")
        lines.append("")

        lines.append(f"【综合结论】")
        if high:
            lines.append(f"  本次抓包存在高风险问题，建议立即排查。重点关注：")
            cats = list(dict.fromkeys([e['category'] for e in high]))
            for c in cats[:3]:
                lines.append(f"    · {c}")
        elif mid:
            lines.append(f"  本次抓包发现部分异常，建议结合业务确认是否为预期行为。")
        else:
            lines.append(f"  本次抓包未发现明显异常，协议分布和连接行为正常。")

        if cfg_question:
            lines.append("")
            lines.append(f"【针对您的问题】")
            lines.append(f"  问题：{cfg_question}")
            # 基于问题类型给出简要指引
            if '中断' in cfg_question or '断开' in cfg_question or 'reset' in cfg_question.lower():
                lines.append(f"  线索：重点排查 RST 包和半开连接。若 RST 集中在特定 IP，通常是防火墙或应用层主动断开；若为半开连接，可能是网络丢包或目标不可达。")
            elif '慢' in cfg_question or '延迟' in cfg_question or '卡顿' in cfg_question:
                lines.append(f"  线索：关注三次握手延迟和 TCP 重传/重复 ACK。握手延迟高通常是网络链路或服务器响应慢；重传多则说明存在丢包。")
            elif '证书' in cfg_question or 'TLS' in cfg_question or 'SSL' in cfg_question:
                lines.append(f"  线索：检查 TLS Alert、弱版本和证书链完整性。TLS Alert 通常意味着客户端与服务器 TLS 配置不兼容或证书已过期。")
            elif '失败' in cfg_question or '不通' in cfg_question:
                lines.append(f"  线索：综合查看 ICMP 不可达、TCP RST、SYN 无响应和 HTTP 4xx/5xx。这些指标能定位是网络层、传输层还是应用层问题。")
            else:
                lines.append(f"  建议：结合上方的需求匹配结果和错误列表，逐项排查与目标 IP 相关的异常。")

        lines.append("")
        lines.append("=" * 60)
        lines.append("报告生成时间：" + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        lines.append("=" * 60)
        return "\n".join(lines)


# ===================== 设置窗口 =====================
class SettingsWindow(CTkToplevel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.settings = parent.settings.copy()
        self.lang_changed = False

        self.title(parent._t("settings_title"))
        self.geometry("520x620")
        self.minsize(450, 500)
        self.transient(parent)
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

        # 颜色设置
        self._add_color_row(content, self.parent._t("font_color_light"), "font_color_light")
        self._add_color_row(content, self.parent._t("font_color_dark"), "font_color_dark")
        self._add_color_row(content, self.parent._t("border_color_light"), "border_color_light")
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
        self.preview_text.insert("0.0", "192.168.1.1 -> 192.168.1.2 TCP SYN")
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
        self.destroy()


# ===================== 分析需求配置窗口 =====================
class ConfigWindow(CTkToplevel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.config = parent.analysis_config.copy()

        self.title(parent._t("config_title"))
        self.geometry("520x420")
        self.minsize(450, 350)
        self.transient(parent)
        self.focus_force()
        self.lift()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()

    def _build_ui(self):
        header = CTkFrame(self, height=50, corner_radius=0, fg_color=("gray90", "gray13"))
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        CTkLabel(header, text=self.parent._t("config_title"), font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20, pady=10)

        content = CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=15)

        CTkLabel(content, text=self.parent._t("target_ips"), font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(8, 4))
        self.ips_entry = self.parent._register_entry(CTkEntry(content, placeholder_text="192.168.1.1, 10.0.0.1"))
        self.ips_entry.pack(fill="x", pady=(0, 10))
        if self.config.get("target_ips"):
            self.ips_entry.insert(0, ", ".join(self.config["target_ips"]))

        CTkLabel(content, text=self.parent._t("focus_errors"), font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(8, 4))
        self.err_entry = self.parent._register_entry(CTkEntry(content, placeholder_text="RST, 重传, TLS"))
        self.err_entry.pack(fill="x", pady=(0, 10))
        if self.config.get("focus_errors"):
            self.err_entry.insert(0, ", ".join(self.config["focus_errors"]))

        CTkLabel(content, text=self.parent._t("question"), font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(8, 4))
        self.q_text = self.parent._register_textbox(CTkTextbox(content, height=80, wrap="word"))
        self.q_text.pack(fill="x", pady=(0, 10))
        if self.config.get("question"):
            self.q_text.insert("0.0", self.config["question"])

        bottom = CTkFrame(self, height=50, fg_color="transparent")
        bottom.pack(fill="x", padx=20, pady=(0, 15))
        bottom.pack_propagate(False)
        CTkButton(bottom, text=self.parent._t("save"), width=100, command=self._save).pack(side="right", padx=(5, 0))
        CTkButton(bottom, text=self.parent._t("cancel"), width=100, fg_color="transparent", border_width=1,
                  hover_color=("gray85", "gray25"), command=self._on_close).pack(side="right", padx=(5, 0))

    def _save(self):
        ips = [x.strip() for x in self.ips_entry.get().split(",") if x.strip()]
        errs = [x.strip() for x in self.err_entry.get().split(",") if x.strip()]
        q = self.q_text.get("0.0", "end").strip()
        self.parent.analysis_config = {"target_ips": ips, "focus_errors": errs, "question": q}
        self._on_close()

    def _on_close(self):
        self.destroy()


# ===================== GUI =====================
class WiresharkAnalyzerApp(CTk):
    def __init__(self):
        super().__init__()
        # CTk 创建完成后再导入 scapy，避免 Windows 64 位 ctypes 冲突提示
        ensure_scapy()
        self.settings = load_settings()
        self.textboxes = []
        self.entries = []

        self.title(self._t("app_title"))
        self.geometry("1300x850")
        self.minsize(1100, 750)

        self.analyzer = None
        self.stats = None
        self.analysis_config = {"target_ips": [], "focus_errors": [], "question": ""}
        self._settings_window = None
        self._config_window = None
        self._analysis_thread = None
        self._drop_enabled = False

        self._build_sidebar()
        self._build_main_area()
        self.apply_settings()
        self._setup_drop()

    def _t(self, key):
        lang = self.settings.get("language", "zh_CN")
        return TEXTS.get(lang, TEXTS["zh_CN"]).get(key, key)

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

        CTkButton(self.sidebar, text=self._t("choose_file"), command=self._choose_file, **btn_primary).pack(fill="x", padx=15, pady=(20, 10))
        self.reanalyze_btn = CTkButton(self.sidebar, text=self._t("reanalyze"), command=self._reanalyze, **btn_secondary)
        self.reanalyze_btn.pack(fill="x", padx=15, pady=(5, 10))
        self.reanalyze_btn.configure(state="disabled")
        CTkButton(self.sidebar, text=self._t("analysis_config"), command=self._open_config, **btn_secondary).pack(fill="x", padx=15, pady=(5, 10))
        CTkButton(self.sidebar, text=self._t("clear_results"), command=self._clear_results, **btn_secondary).pack(fill="x", padx=15, pady=(5, 10))
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
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        self.content_frame = CTkFrame(content, fg_color="transparent")
        self.content_frame.grid(row=0, column=0, sticky="nsew")
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)

        # ---------- 欢迎界面 ----------
        self.welcome_card = CTkFrame(self.content_frame, corner_radius=16, fg_color=("white", "gray16"))
        self.welcome_card.place(relx=0.5, rely=0.45, anchor="center")
        self.welcome_card.configure(width=520, height=360)
        self.welcome_card.pack_propagate(False)

        drop_zone = CTkFrame(self.welcome_card, corner_radius=14, fg_color=("#e3f2fd", "gray17"), border_width=2,
                             border_color=("#0288d1", "#0288d1"))
        drop_zone.pack(fill="x", padx=20, pady=(20, 10))
        drop_zone.pack_propagate(False)
        drop_zone.configure(height=180)

        inner = CTkFrame(drop_zone, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")
        CTkLabel(inner, text="🦈", font=ctk.CTkFont(size=48)).pack(pady=(0, 5))
        self.drop_label = CTkLabel(inner, text=self._t("drop_hint"), font=ctk.CTkFont(size=14), text_color=("#0288d1", "#4fc3f7"))
        self.drop_label.pack()
        self.drop_label.bind("<Button-1>", lambda e: self._choose_file())
        drop_zone.bind("<Button-1>", lambda e: self._choose_file())

        CTkButton(self.welcome_card, text=self._t("choose_file"), command=self._choose_file,
                  font=ctk.CTkFont(size=14, weight="bold"), height=40, corner_radius=10).pack(pady=(10, 5))
        CTkLabel(self.welcome_card, text=self._t("supported_formats"), font=ctk.CTkFont(size=11),
                 text_color=("gray50", "gray60")).pack()

        if getattr(self, "_windows_drop_enabled", False):
            self.drop_label.configure(text=self._t("drop_hint_ok"))

        # ---------- 进度界面 ----------
        self.progress_card = CTkFrame(self.content_frame, corner_radius=16, fg_color=("white", "gray16"))
        self.progress_card.place(relx=0.5, rely=0.45, anchor="center")
        self.progress_card.configure(width=520, height=220)
        self.progress_card.pack_propagate(False)
        self.progress_card.place_forget()

        CTkLabel(self.progress_card, text=self._t("analyzing"), font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(40, 20))
        self.progress_bar = CTkProgressBar(self.progress_card, height=16, corner_radius=8, mode="indeterminate", width=400)
        self.progress_bar.pack(pady=10)
        self.progress_label = CTkLabel(self.progress_card, text=self._t("loading"), font=ctk.CTkFont(size=13),
                                       text_color=("gray50", "gray60"))
        self.progress_label.pack()

        # ---------- 结果界面 ----------
        self.result_card = CTkFrame(self.content_frame, corner_radius=16, fg_color=("white", "gray16"))
        self.result_card.grid(row=0, column=0, sticky="nsew")
        self.result_card.grid_forget()
        self.result_card.columnconfigure(0, weight=1)
        self.result_card.rowconfigure(1, weight=1)

        # 结果头部工具栏
        result_header = CTkFrame(self.result_card, corner_radius=0, fg_color="transparent", height=44)
        result_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 0))
        result_header.pack_propagate(False)
        result_header.columnconfigure(1, weight=1)

        self.step_label = CTkLabel(result_header, text=self._t("please_select_file"), font=ctk.CTkFont(size=13))
        self.step_label.pack(side="left", padx=5)

        # 搜索
        self.search_entry = self._register_entry(CTkEntry(result_header, width=160, placeholder_text=self._t("search")))
        self.search_entry.pack(side="right", padx=(5, 0))
        self.search_entry.bind("<Return>", lambda e: self._search_current_tab())
        CTkButton(result_header, text="🔍", width=32, height=32, corner_radius=8,
                  command=self._search_current_tab).pack(side="right", padx=(5, 0))
        CTkButton(result_header, text="✕", width=32, height=32, corner_radius=8, fg_color="transparent", border_width=1,
                  hover_color=("gray85", "gray25"), command=self._clear_search).pack(side="right", padx=(5, 0))

        btn_style = {"width": 110, "height": 32, "corner_radius": 8, "font": ctk.CTkFont(size=12)}
        CTkButton(result_header, text=self._t("export_txt"), command=self._export_txt, **btn_style).pack(side="right", padx=(5, 0))
        CTkButton(result_header, text=self._t("copy_result"), command=self._copy_result,
                  fg_color="transparent", border_width=1, hover_color=("gray85", "gray25"), **btn_style).pack(side="right", padx=(5, 0))

        # Tabview
        self.tabview = CTkTabview(self.result_card, corner_radius=12, fg_color=("gray98", "gray14"))
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=12, pady=(10, 12))

        self.tab_keys = [
            "file_overview", "protocol_stats", "tcp_analysis",
            "tls_analysis", "errors", "communication", "conclusion"
        ]
        self.tab_textboxes = {}
        for key in self.tab_keys:
            tab = self.tabview.add(self._t(key))
            tab.columnconfigure(0, weight=1)
            tab.rowconfigure(0, weight=1)
            tb = self._register_textbox(CTkTextbox(
                tab, wrap="word",
                font=ctk.CTkFont(family="Consolas", size=self.settings["font_size"]),
                text_color=(self.settings["font_color_light"], self.settings["font_color_dark"]),
                border_color=(self.settings["border_color_light"], self.settings["border_color_dark"]),
                border_width=self.settings["border_width"],
                corner_radius=10, fg_color=("gray98", "gray14"),
            ))
            tb.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            tb.configure(state="disabled")
            self.tab_textboxes[key] = tb
            self._configure_text_tags(tb)

        # 状态栏
        self.status_label = CTkLabel(content, text=self._t("ready"), font=ctk.CTkFont(size=12), text_color=("gray50", "gray60"))
        self.status_label.grid(row=1, column=0, sticky="w", padx=5, pady=(5, 0))

    def _configure_text_tags(self, textbox):
        tw = textbox._textbox
        tw.tag_configure("matched", background="#fff9c4", foreground="#d84315")
        tw.tag_configure("high", foreground="#e53935")
        tw.tag_configure("mid", foreground="#fb8c00")
        tw.tag_configure("low", foreground="#43a047")
        _header_color = "#4fc3f7" if ctk.get_appearance_mode() == "Dark" else "#0288d1"
        tw.tag_configure("header", font=ctk.CTkFont(family="Microsoft YaHei UI", size=self.settings["font_size"], weight="bold"),
                         foreground=_header_color)
        _search_bg = "#b58900" if ctk.get_appearance_mode() == "Dark" else "#f1c40f"
        _search_fg = "white" if ctk.get_appearance_mode() == "Dark" else "black"
        tw.tag_configure("search", background=_search_bg, foreground=_search_fg)

    def _setup_drop(self):
        # customtkinter.CTk 不支持 tkinterdnd2，使用 Windows 原生 WM_DROPFILES 作为拖拽支持
        if sys.platform == 'win32':
            self._setup_windows_drop()

    def _setup_windows_drop(self):
        try:
            import ctypes
            from ctypes import WINFUNCTYPE, c_void_p, c_long, c_int, c_uint

            WM_DROPFILES = 0x0233
            GWL_WNDPROC = -4

            user32 = ctypes.windll.user32
            shell32 = ctypes.windll.shell32

            try:
                GetWindowLongPtr = user32.GetWindowLongPtrW
                SetWindowLongPtr = user32.SetWindowLongPtrW
            except AttributeError:
                GetWindowLongPtr = user32.GetWindowLongW
                SetWindowLongPtr = user32.SetWindowLongW

            user32.GetParent.argtypes = [c_void_p]
            user32.GetParent.restype = c_void_p
            GetWindowLongPtr.argtypes = [c_void_p, c_int]
            GetWindowLongPtr.restype = c_void_p
            SetWindowLongPtr.argtypes = [c_void_p, c_int, c_void_p]
            SetWindowLongPtr.restype = c_void_p
            user32.CallWindowProcW.argtypes = [c_void_p, c_void_p, c_uint, c_void_p, c_void_p]
            user32.CallWindowProcW.restype = c_long
            shell32.DragAcceptFiles.argtypes = [c_void_p, c_int]
            shell32.DragQueryFileW.argtypes = [c_void_p, c_uint, c_void_p, c_uint]
            shell32.DragQueryFileW.restype = c_uint
            shell32.DragFinish.argtypes = [c_void_p]

            self._hwnd = ctypes.c_void_p(user32.GetParent(ctypes.c_void_p(self.winfo_id())))
            self._old_wndproc = GetWindowLongPtr(self._hwnd, GWL_WNDPROC)

            @WINFUNCTYPE(c_long, c_void_p, c_uint, c_void_p, c_void_p)
            def new_wndproc(hwnd, msg, wparam, lparam):
                if msg == WM_DROPFILES:
                    try:
                        hdrop = ctypes.c_void_p(wparam)
                        count = shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
                        files = []
                        for i in range(count):
                            buf = ctypes.create_unicode_buffer(1024)
                            shell32.DragQueryFileW(hdrop, i, buf, 1024)
                            files.append(buf.value)
                        shell32.DragFinish(hdrop)
                        if files:
                            self.after(10, lambda fs=files: self._handle_dropped_files(fs))
                    except Exception as e:
                        print("Windows drop error:", e)
                    return 0
                return user32.CallWindowProcW(self._old_wndproc, hwnd, msg, wparam, lparam)

            self._new_wndproc = new_wndproc
            SetWindowLongPtr(self._hwnd, GWL_WNDPROC, ctypes.cast(new_wndproc, ctypes.c_void_p))
            shell32.DragAcceptFiles(self._hwnd, 1)
            self._windows_drop_enabled = True
            self._drop_enabled = True
        except Exception as e:
            print("Windows native drop setup failed:", e)
            self._windows_drop_enabled = False

    def _handle_dropped_files(self, files):
        valid_exts = ('.pcap', '.pcapng', '.cap', '.dmp')
        target = None
        for f in files:
            if os.path.isfile(f) and f.lower().endswith(valid_exts):
                target = f
                break
        if target is None:
            for f in files:
                if os.path.isfile(f):
                    target = f
                    break
        if target:
            if not SCAPY_AVAILABLE:
                messagebox.showerror(self._t("missing_dep"), self._t("missing_scapy"))
                return
            self._start_analysis(target)
        else:
            messagebox.showwarning(self._t("analysis_failed"), self._t("invalid_file"))

    def _choose_file(self):
        if not SCAPY_AVAILABLE:
            messagebox.showerror(self._t("missing_dep"), self._t("missing_scapy"))
            return
        path = filedialog.askopenfilename(
            title=self._t("choose_file"),
            filetypes=[("抓包文件", "*.pcap *.pcapng"), ("所有文件", "*.*")]
        )
        if path:
            self._start_analysis(path)

    def _start_analysis(self, path):
        self._show_progress(self._t("analyzing"))
        self.analyzer = PacketAnalyzer(path, config=self.analysis_config)
        self._do_analysis()

    def _do_analysis(self):
        def work():
            ok = self.analyzer.load()
            if ok:
                self.stats = self.analyzer.analyze()
                self.after(0, self._on_analysis_done)
            else:
                self.after(0, lambda: self._on_analysis_error(self.analyzer.error_msg))
        self._analysis_thread = threading.Thread(target=work, daemon=True)
        self._analysis_thread.start()

    def _on_analysis_done(self):
        self.progress_bar.stop()
        self._build_result_contents()
        self._show_results()
        self.reanalyze_btn.configure(state="normal")
        self.status_label.configure(text=self._t("ready"))

    def _on_analysis_error(self, msg):
        self.progress_bar.stop()
        self._show_welcome()
        messagebox.showerror(self._t("analysis_failed"), f"{self._t('analysis_failed')}:\n{msg}")

    def _reanalyze(self):
        if self.analyzer and self.analyzer.file_path:
            self._start_analysis(self.analyzer.file_path)

    def _show_welcome(self):
        self.result_card.grid_forget()
        self.progress_card.place_forget()
        self.progress_bar.stop()
        self.welcome_card.place(relx=0.5, rely=0.45, anchor="center")
        self.step_label.configure(text=self._t("please_select_file"))
        self.reanalyze_btn.configure(state="disabled")

    def _show_progress(self, msg):
        self.welcome_card.place_forget()
        self.result_card.grid_forget()
        self.progress_card.place(relx=0.5, rely=0.45, anchor="center")
        self.progress_label.configure(text=msg)
        self.progress_bar.start()

    def _show_results(self):
        self.welcome_card.place_forget()
        self.progress_card.place_forget()
        self.progress_bar.stop()
        self.result_card.grid(row=0, column=0, sticky="nsew")
        self.tabview.set(self._t("file_overview"))
        self._update_step_label("file_overview")

    def _update_step_label(self, key):
        idx = self.tab_keys.index(key)
        self.step_label.configure(text=self._t("current_step").format(self._t(key), idx + 1, len(self.tab_keys)))

    def _build_result_contents(self):
        s = self.stats
        if not s:
            return
        mark = self._t("matched_mark")

        # 0. 文件概览
        tb = self.tab_textboxes["file_overview"]
        tb.configure(state="normal")
        tb.delete("0.0", "end")
        fi = s['file_info']
        tl = s['traffic_timeline']
        lines = [
            f"文件名称：    {fi['file_name']}",
            f"文件路径：    {fi['file_path']}",
            f"文件大小：    {fi['file_size_mb']} MB",
            f"数据包总数：  {fi['packet_count']} 个",
            f"捕获开始：    {fi['start_time']}",
            f"捕获结束：    {fi['end_time']}",
            f"持续时间：    {fi['duration_sec']} 秒",
            f"平均包长度：  {fi['avg_packet_len']} 字节",
            "",
        ]
        if tl['timeline']:
            lines.append("流量时间线（每10秒包数）")
            lines.append(f"{'时间段(秒)':<15}{'包数':<10}")
            for x in tl['timeline']:
                lines.append(f"{x['time_sec']}~{x['time_sec']+10:<12}{x['count']}")
            if tl['peak']:
                lines.append("")
                lines.append(f"流量峰值：{tl['peak']['count']} 包/10秒")
        tb.insert("0.0", "\n".join(lines))
        tb.configure(state="disabled")

        # 1. 协议统计
        tb = self.tab_textboxes["protocol_stats"]
        tb.configure(state="normal")
        tb.delete("0.0", "end")
        lines = ["协议分布", "", f"{'协议':<15}{'包数':<10}{'占比(%)':<10}", "-" * 40]
        for x in s['protocol']:
            lines.append(f"{x['protocol']:<15}{x['count']:<10}{x['percent']:<10}")
        ps = s['port_session']
        if ps['services']:
            lines.extend(["", "识别到的服务", "", f"{'服务':<20}{'包数':<10}", "-" * 35])
            for svc, cnt in ps['services']:
                lines.append(f"{svc:<20}{cnt}")
        tb.insert("0.0", "\n".join(lines))
        tb.configure(state="disabled")

        # 2. TCP 连接分析
        tb = self.tab_textboxes["tcp_analysis"]
        tb.configure(state="normal")
        tb.delete("0.0", "end")
        th = s['tcp_handshake']

        def _insert_header(text):
            start = tb._textbox.index("end-1c")
            tb.insert("end", text + "\n")
            end = tb._textbox.index("end-1c")
            tb._textbox.tag_add("header", start, end)

        def _insert_sep(width=60):
            tb.insert("end", "─" * width + "\n")

        def _insert_record(prefix, lines_list, tag=None):
            for i, line in enumerate(lines_list):
                start = tb._textbox.index("end-1c")
                tb.insert("end", (prefix if i == 0 else "    ") + line + "\n")
                end = tb._textbox.index("end-1c")
                if tag:
                    tb._textbox.tag_add(tag, start, end)

        # 统计摘要
        _insert_header("TCP 连接统计摘要")
        tb.insert("end", f"  SYN 总数:        {th['total_syns']}\n")
        tb.insert("end", f"  成功三次握手:    {th['successful_handshakes']}\n")
        tb.insert("end", f"  半开/异常连接:   {len(th['half_opens'])}\n")
        tb.insert("end", f"  RST 拒绝连接:    {len(th['refused'])}\n")
        tb.insert("end", f"  总 RST 包:       {len(th['resets'])}\n\n")

        # 成功的三次握手
        if th['handshakes']:
            _insert_header(f"成功的三次握手（{len(th['handshakes'])}）")
            _insert_sep()
            for x in th['handshakes']:
                m = mark if x.get('matched') else " "
                tag = "matched" if x.get('matched') else None
                _insert_record(
                    f"[{m}] ",
                    [f"{x['client']}:{x['client_port']} → {x['server']}:{x['server_port']}",
                     f"SYN-ACK 延迟: {x['latency_syn_to_synack']} s    总延迟: {x['latency_total']} s"],
                    tag
                )
            tb.insert("end", "\n")

        # 半开/异常连接
        if th['half_opens']:
            _insert_header(f"半开/异常连接（{len(th['half_opens'])}）")
            _insert_sep()
            for x in th['half_opens']:
                m = mark if x.get('matched') else " "
                tag = "matched" if x.get('matched') else None
                _insert_record(
                    f"[{m}] ",
                    [f"{x['client']}:{x['client_port']} → {x['server']}:{x['server_port']}",
                     f"说明: {x['note']}"],
                    tag
                )
            tb.insert("end", "\n")

        # RST 拒绝的连接
        if th['refused']:
            _insert_header(f"RST 拒绝的连接（{len(th['refused'])}）")
            _insert_sep()
            for x in th['refused']:
                m = mark if x.get('matched') else " "
                tag = "matched" if x.get('matched') else None
                _insert_record(
                    f"[{m}] ",
                    [f"{x['client']}:{x['client_port']} → {x['server']}:{x['server_port']}",
                     f"说明: {x['note']}"],
                    tag
                )
            tb.insert("end", "\n")

        # 所有 RST 包
        if th['resets']:
            _insert_header(f"所有 RST 包（{len(th['resets'])}）")
            _insert_sep()
            for x in th['resets']:
                m = mark if x.get('matched') else " "
                tag = "matched" if x.get('matched') else None
                _insert_record(
                    f"[{m}] ",
                    [f"{x['src']}:{x['src_port']} → {x['dst']}:{x['dst_port']}"],
                    tag
                )
            tb.insert("end", "\n")

        if not (th['handshakes'] or th['half_opens'] or th['refused'] or th['resets']):
            tb.insert("end", "未检测到 TCP 连接事件。\n")

        tb.configure(state="disabled")

        # 3. TLS/证书分析
        tb = self.tab_textboxes["tls_analysis"]
        tb.configure(state="normal")
        tb.delete("0.0", "end")
        tls = s['tls_analysis']
        if tls:
            tb.insert("end", f"TLS 包总数：{tls['total_tls_packets']}    ClientHello：{len(tls['client_hellos'])}    "
                             f"ServerHello：{len(tls['server_hellos'])}    Certificate：{len(tls['certificates'])}\n\n")
            if tls['sni_list']:
                unique_sni = list(dict.fromkeys(tls['sni_list']))[:5]
                tb.insert("end", "SNI 域名列表（去重前5）\n\n")
                for sni in unique_sni:
                    tb.insert("end", f"  · {sni}\n")
                tb.insert("end", "\n")
            if tls['client_hellos']:
                tb.insert("end", "ClientHello 详情\n\n")
                tb.insert("end", f"{'匹配':<5}{'源IP':<20}{'目的IP':<20}{'TLS版本':<18}{'SNI'}\n")
                tb.insert("end", "-" * 100 + "\n")
                for x in tls['client_hellos']:
                    m = mark if x.get('matched') else ""
                    sni = ", ".join(x.get('sni', [])[:3])
                    line = f"{m:<5}{str(x['src']):<20}{str(x['dst']):<20}{str(x['version']):<18}{sni}"
                    self._insert_line_with_tag(tb, line, "matched" if x.get('matched') else None)
                tb.insert("end", "\n")
            if tls['server_hellos']:
                tb.insert("end", "ServerHello 详情\n\n")
                tb.insert("end", f"{'匹配':<5}{'源IP':<20}{'目的IP':<20}{'TLS版本':<18}{'密码套件'}\n")
                tb.insert("end", "-" * 110 + "\n")
                for x in tls['server_hellos']:
                    m = mark if x.get('matched') else ""
                    line = f"{m:<5}{str(x['src']):<20}{str(x['dst']):<20}{str(x['version']):<18}{x.get('cipher', 'Unknown')}"
                    self._insert_line_with_tag(tb, line, "matched" if x.get('matched') else None)
                tb.insert("end", "\n")
            if tls['weak_versions']:
                tb.insert("end", f"⚠️ 弱 TLS/SSL 版本通信：{len(tls['weak_versions'])} 次\n\n")
            if tls['alerts']:
                tb.insert("end", f"⚠️ TLS Alert：{len(tls['alerts'])} 次\n\n")
                tb.insert("end", f"{'匹配':<5}{'源IP':<22}{'目的IP':<22}{'源端口':<12}{'目的端口':<12}\n")
                tb.insert("end", "-" * 80 + "\n")
                for x in tls['alerts']:
                    m = mark if x.get('matched') else ""
                    line = f"{m:<5}{str(x['src']):<22}{str(x['dst']):<22}{str(x['src_port']):<12}{str(x['dst_port']):<12}"
                    self._insert_line_with_tag(tb, line, "matched" if x.get('matched') else None)
        else:
            tb.insert("0.0", "未检测到 TLS/SSL 流量")
        tb.configure(state="disabled")

        # 4. 错误与异常
        tb = self.tab_textboxes["errors"]
        tb.configure(state="normal")
        tb.delete("0.0", "end")
        errs = s['errors']
        high_cnt = len([e for e in errs if e['level'] == '高'])
        mid_cnt = len([e for e in errs if e['level'] == '中'])
        lines = [f"高风险：{high_cnt} 项    中风险：{mid_cnt} 项    低风险/正常：{len(errs)-high_cnt-mid_cnt} 项", "",
                 f"{'匹配':<5}{'等级':<8}{'类别':<18}{'详细信息'}", "-" * 120]
        tb.insert("0.0", "\n".join(lines) + "\n")
        level_tag_map = {"高": "high", "中": "mid", "低": "low"}
        for item in errs:
            m = mark if item.get('matched') else ""
            line = f"{m:<5}{item['level']:<8}{item['category']:<18}{item['detail']}"
            tags = []
            if item.get('matched'):
                tags.append("matched")
            if item['level'] in level_tag_map:
                tags.append(level_tag_map[item['level']])
            self._insert_line_with_tags(tb, line, tags)
        tb.configure(state="disabled")

        # 5. 通信详情
        tb = self.tab_textboxes["communication"]
        tb.configure(state="normal")
        tb.delete("0.0", "end")
        ip = s['ip_comm']
        ps = s['port_session']
        lines = []
        lines.extend(["Top 10 源 IP", "", f"{'IP 地址':<30}{'包数':<10}", "-" * 45])
        for addr, cnt in ip['src_top10']:
            lines.append(f"{str(addr):<30}{cnt}")
        lines.extend(["", "Top 10 目的 IP", "", f"{'IP 地址':<30}{'包数':<10}", "-" * 45])
        for addr, cnt in ip['dst_top10']:
            lines.append(f"{str(addr):<30}{cnt}")
        lines.extend(["", "Top 通信对", "", f"{'通信对':<50}{'包数':<10}", "-" * 65])
        for pair, cnt in ip['pair_top10']:
            lines.append(f"{pair:<50}{cnt}")
        lines.extend(["", "Top 目的端口", "", f"{'目的端口':<20}{'包数':<10}", "-" * 35])
        for port, cnt in ps['dst_ports_top10']:
            lines.append(f"{port:<20}{cnt}")
        lines.extend(["", f"TCP 会话数：{ps['tcp_sessions']}    UDP 会话数：{ps['udp_sessions']}    独立 IP：{ip['unique_ips']} 个"])
        tb.insert("0.0", "\n".join(lines))
        tb.configure(state="disabled")

        # 6. 综合结论
        tb = self.tab_textboxes["conclusion"]
        tb.configure(state="normal")
        tb.delete("0.0", "end")
        tb.insert("0.0", s['conclusion'])
        tb.configure(state="disabled")

        # Tab 切换时更新步骤标签
        self.tabview.configure(command=self._on_tab_change)

    def _insert_line_with_tag(self, textbox, line, tag):
        tw = textbox._textbox
        start = tw.index("end-1c")
        tw.insert("end", line + "\n")
        if tag:
            end = tw.index("end-1c")
            tw.tag_add(tag, start, end)

    def _insert_line_with_tags(self, textbox, line, tags):
        tw = textbox._textbox
        start = tw.index("end-1c")
        tw.insert("end", line + "\n")
        if tags:
            end = tw.index("end-1c")
            for tag in tags:
                tw.tag_add(tag, start, end)

    def _on_tab_change(self):
        key = None
        current = self.tabview.get()
        for k, v in self._t_map().items():
            if v == current:
                key = k
                break
        if key:
            self._update_step_label(key)

    def _t_map(self):
        return {k: self._t(k) for k in self.tab_keys}

    def _search_current_tab(self):
        keyword = self.search_entry.get().strip()
        if not keyword:
            return
        current = self.tabview.get()
        tb = None
        tmap = self._t_map()
        for key, title in tmap.items():
            if title == current:
                tb = self.tab_textboxes[key]
                break
        if not tb:
            return
        tw = tb._textbox
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
        if found:
            self.status_label.configure(text=self._t("search_highlight").format(keyword))
        else:
            self.status_label.configure(text=self._t("search_not_found").format(keyword))

    def _clear_search(self):
        for tb in self.tab_textboxes.values():
            tb._textbox.tag_remove("search", "1.0", "end")
        self.search_entry.delete(0, "end")
        self.status_label.configure(text=self._t("search_cleared"))

    def _export_txt(self):
        current = self.tabview.get()
        tb = None
        tmap = self._t_map()
        for key, title in tmap.items():
            if title == current:
                tb = self.tab_textboxes[key]
                break
        if not tb:
            return
        text = tb.get("0.0", "end").strip()
        if not text:
            messagebox.showinfo(self._t("export_txt"), self._t("no_content"))
            return
        path = filedialog.asksaveasfilename(
            title=self._t("export_txt"),
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            self.status_label.configure(text=self._t("export_success"))
            messagebox.showinfo(self._t("export_txt"), self._t("file_saved_to").format(path))
        except Exception as e:
            messagebox.showerror(self._t("export_fail"), str(e))

    def _copy_result(self):
        current = self.tabview.get()
        tb = None
        tmap = self._t_map()
        for key, title in tmap.items():
            if title == current:
                tb = self.tab_textboxes[key]
                break
        if not tb:
            return
        text = tb.get("0.0", "end").strip()
        if not text:
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.status_label.configure(text=self._t("copy_done"))
        except Exception as e:
            print("Copy failed:", e)

    def _clear_results(self):
        self.stats = None
        self.analyzer = None
        for tb in self.tab_textboxes.values():
            tb.configure(state="normal")
            tb.delete("0.0", "end")
            tb.configure(state="disabled")
        self.search_entry.delete(0, "end")
        self._show_welcome()

    def _toggle_theme(self):
        mode = "Dark" if self.theme_switch.get() == "dark" else "Light"
        ctk.set_appearance_mode(mode)
        # 更新搜索高亮色
        _search_bg = "#b58900" if mode == "Dark" else "#f1c40f"
        _search_fg = "white" if mode == "Dark" else "black"
        for tb in self.tab_textboxes.values():
            tb._textbox.tag_configure("search", background=_search_bg, foreground=_search_fg)

    def _open_settings(self):
        if self._settings_window and self._settings_window.winfo_exists():
            self._settings_window.lift()
            self._settings_window.focus_force()
            return
        self._settings_window = SettingsWindow(self)

    def _open_config(self):
        if self._config_window and self._config_window.winfo_exists():
            self._config_window.lift()
            self._config_window.focus_force()
            return
        self._config_window = ConfigWindow(self)

    def _try_set_icon(self):
        ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wireshark.ico")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass


def main():
    app = WiresharkAnalyzerApp()
    app._try_set_icon()
    app.mainloop()


if __name__ == "__main__":
    main()
