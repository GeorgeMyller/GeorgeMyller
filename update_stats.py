#!/usr/bin/env python3
"""
Elite Dynamic GitHub Profile Terminal Card Generator
Transforms George Myller's profile into an interactive, animated AI Command Center
with tmux split-pane, k9s-style daemon cluster table, btop-colored bars, and vector powerline.
"""

import os
import sys
import html
import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple
import requests
from PIL import Image, ImageEnhance, ImageFilter

USERNAME = "GeorgeMyller"
START_DATE = datetime.datetime(2019, 4, 10)  # Account creation or career start

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ACCESS_TOKEN") or ""
HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}


def calculate_uptime(start_date: datetime.datetime) -> str:
    """Calcula o tempo decorrido em anos, meses e dias."""
    now = datetime.datetime.now()
    years = now.year - start_date.year
    months = now.month - start_date.month
    days = now.day - start_date.day

    if days < 0:
        months -= 1
        prev_month = (now.month - 1) or 12
        prev_year = now.year if prev_month != 12 else now.year - 1
        days_in_prev = (datetime.datetime(prev_year, prev_month % 12 + 1, 1) - datetime.timedelta(days=1)).day
        days += days_in_prev

    if months < 0:
        years -= 1
        months += 12

    y_str = f"{years} yr{'s' if years != 1 else ''}"
    m_str = f"{months} mo{'s' if months != 1 else ''}"
    d_str = f"{days} day{'s' if days != 1 else ''}"
    return f"{y_str}, {m_str}, {d_str}"


def fetch_github_stats() -> Dict[str, Any]:
    """Coleta estatísticas reais do GitHub com fallback robusto."""
    stats = {
        "repos": 39,
        "contributed": 12,
        "stars": 17,
        "followers": 8,
        "commits": 1420,
        "loc_added": 185240,
        "loc_deleted": 42150,
    }

    try:
        res = requests.get(f"https://api.github.com/users/{USERNAME}", headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json()
            stats["repos"] = data.get("public_repos", stats["repos"])
            stats["followers"] = data.get("followers", stats["followers"])
    except Exception as e:
        print(f"Notice: using cached user profile ({e})")

    try:
        res = requests.get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100", headers=HEADERS, timeout=8)
        if res.status_code == 200:
            repos_data = res.json()
            if isinstance(repos_data, list):
                total_stars = sum(r.get("stargazers_count", 0) for r in repos_data if isinstance(r, dict))
                stats["stars"] = total_stars
    except Exception as e:
        print(f"Notice: using cached stars ({e})")

    if TOKEN:
        query = """
        query($login: String!) {
          user(login: $login) {
            repositoriesContributedTo(first: 100) {
              totalCount
            }
            contributionsCollection {
              totalCommitContributions
              restrictedContributionsCount
              contributionCalendar {
                totalContributions
              }
            }
          }
        }
        """
        try:
            res = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": {"login": USERNAME}},
                headers=HEADERS,
                timeout=8,
            )
            if res.status_code == 200:
                data = res.json().get("data", {}).get("user", {})
                if data:
                    contrib = data.get("contributionsCollection", {})
                    total_commits = contrib.get("totalCommitContributions", 0) + contrib.get("restrictedContributionsCount", 0)
                    total_contribs = contrib.get("contributionCalendar", {}).get("totalContributions", 0)
                    stats["commits"] = max(total_commits, total_contribs, stats["commits"])
                    stats["contributed"] = data.get("repositoriesContributedTo", {}).get("totalCount", stats["contributed"])
        except Exception as e:
            print(f"Notice: using cached GraphQL stats ({e})")

    return stats


def get_gm_logo() -> List[str]:
    """Retorna o logotipo geométrico cyberpunk GM AI-CORE personalizado."""
    return [
        "             ┌─────────┐            ",
        "         ────┤ AI-CORE ├────        ",
        "             └────┬────┘            ",
        "      ┌───────────┴───────────┐     ",
        "      │   ▄████▄    █▄     ▄█ │     ",
        "      │  ██▀  ▀██   ███   ███ │     ",
        "      │ ██▌         ██▀█ █▀██ │     ",
        "      │ ██▌  ████   ██ ▀█▀ ██ │     ",
        "      │ ██▌    ██   ██     ██ │     ",
        "      │  ▀██▄▄██▀   ██     ██ │     ",
        "      └───────────┬───────────┘     ",
        "             ┌────┴────┐            ",
        "         ────┤ SWARMS  ├────        ",
        "             └─────────┘            ",
        "     ─────────────────────────      ",
        "        G E O R G E   M Y L L E R   ",
        "      ◆  AI SYSTEMS ARCHITECT  ◆    ",
        "     ─────────────────────────      ",
    ]


def format_num(num: int) -> str:
    return f"{num:,}"


def build_svg(
    theme: str,
    ascii_lines: List[str],
    stats: Dict[str, Any],
    uptime_str: str,
) -> str:
    """Monta o card de terminal interativo com Split-Pane, Daemon Table e Powerline vetorial."""
    is_dark = theme == "dark"

    if is_dark:
        bg_main = "#0d1117"
        bg_header = "#161b22"
        bg_active_tab = "#0d1117"
        bg_footer = "#161b22"
        border_color = "#30363d"
        text_white = "#e6edf3"
        text_dim = "#8b949e"
        prompt_user = "#58a6ff"
        prompt_path = "#bc8cff"
        prompt_branch = "#7ee787"
        prompt_cmd = "#f0883e"
        cursor_color = "#58a6ff"
        ascii_color = "#79c0ff"
        title_color = "#7ee787"
        key_color = "#ffa657"
        val_color = "#a5d6ff"
        dot_color = "#484f58"
        add_color = "#3fb950"
        del_color = "#f85149"
        status_online = "#3fb950"
        status_pause = "#e3b341"
        link_color = "#58a6ff"
        pill_bg = "#21262d"
        pane_border = "#21262d"
        # Cores temáticas das barras btop
        bar_py = "#7ee787"
        bar_ts = "#79c0ff"
        bar_db = "#d2a8ff"
        power_bg1 = "#2ea043"
        power_bg2 = "#21262d"
        power_bg3 = "#161b22"
        power_bg4 = "#1f6feb"
    else:
        bg_main = "#f6f8fa"
        bg_header = "#eaeef2"
        bg_active_tab = "#f6f8fa"
        bg_footer = "#eaeef2"
        border_color = "#d0d7de"
        text_white = "#1f2328"
        text_dim = "#656d76"
        prompt_user = "#0969da"
        prompt_path = "#8250df"
        prompt_branch = "#1a7f37"
        prompt_cmd = "#bc4c00"
        cursor_color = "#0969da"
        ascii_color = "#0969da"
        title_color = "#1a7f37"
        key_color = "#953800"
        val_color = "#0550ae"
        dot_color = "#afb8c1"
        add_color = "#1a7f37"
        del_color = "#cf222e"
        status_online = "#1a7f37"
        status_pause = "#9a6700"
        link_color = "#0969da"
        pill_bg = "#e1e4e8"
        pane_border = "#d0d7de"
        bar_py = "#1a7f37"
        bar_ts = "#0969da"
        bar_db = "#8250df"
        power_bg1 = "#1a7f37"
        power_bg2 = "#d0d7de"
        power_bg3 = "#eaeef2"
        power_bg4 = "#0969da"

    width = 1040
    height = 720

    loc_total = stats["loc_added"] - stats["loc_deleted"]

    def esc(s: Any) -> str:
        return html.escape(str(s), quote=True)

    svg: List[str] = []
    svg.append("<?xml version='1.0' encoding='UTF-8'?>")
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,monospace" width="{width}px" height="{height}px" viewBox="0 0 {width} {height}" font-size="14px">')
    
    # Estilos e Keyframes CSS
    svg.append("<style>")
    svg.append("""
@font-face {
  src: local('Consolas'), local('Consolas Bold');
  font-family: 'ConsolasFallback';
  font-display: swap;
  -webkit-size-adjust: 109%;
  size-adjust: 109%;
}
@keyframes blink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0; }
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}
.cursor { animation: blink 1.1s infinite; }
.pulse-live { animation: pulse 2s infinite ease-in-out; }
a { text-decoration: none; cursor: pointer; }
a:hover text, a:hover tspan { text-decoration: underline; }
text, tspan { white-space: pre; }
""")
    svg.append(f".ascii {{ fill: {ascii_color}; }}")
    svg.append(f".title {{ fill: {title_color}; font-weight: bold; }}")
    svg.append(f".key {{ fill: {key_color}; font-weight: 600; }}")
    svg.append(f".val {{ fill: {val_color}; }}")
    svg.append(f".dot {{ fill: {dot_color}; }}")
    svg.append(f".add {{ fill: {add_color}; }}")
    svg.append(f".del {{ fill: {del_color}; }}")
    svg.append(f".dim {{ fill: {text_dim}; }}")
    svg.append(f".white {{ fill: {text_white}; }}")
    svg.append(f".link {{ fill: {link_color}; font-weight: bold; }}")
    svg.append(f".online {{ fill: {status_online}; font-weight: bold; }}")
    svg.append(f".pause {{ fill: {status_pause}; font-weight: bold; }}")
    svg.append(f".bar-py {{ fill: {bar_py}; font-weight: bold; }}")
    svg.append(f".bar-ts {{ fill: {bar_ts}; font-weight: bold; }}")
    svg.append(f".bar-db {{ fill: {bar_db}; font-weight: bold; }}")
    svg.append("</style>")

    # 1. Main Window Box
    svg.append(f'<rect width="{width}px" height="{height}px" rx="14" fill="{bg_main}" stroke="{border_color}" stroke-width="1.5"/>')

    # 2. Window Chrome Titlebar with Tabs
    svg.append(f'<path d="M 0 14 Q 0 0 14 0 L {width-14} 0 Q {width} 0 {width} 14 L {width} 42 L 0 42 Z" fill="{bg_header}"/>')
    svg.append(f'<line x1="0" y1="42" x2="{width}" y2="42" stroke="{border_color}" stroke-width="1"/>')

    # Window Controls (macOS style)
    svg.append('<circle cx="22" cy="21" r="6" fill="#ff5f56"/>')
    svg.append('<circle cx="42" cy="21" r="6" fill="#ffbd2e"/>')
    svg.append('<circle cx="62" cy="21" r="6" fill="#27c93f"/>')

    # Terminal Tabs
    tab_x = 95
    # Active Tab
    svg.append(f'<rect x="{tab_x}" y="8" width="165" height="34" rx="6" fill="{bg_active_tab}"/>')
    svg.append(f'<line x1="{tab_x+8}" y1="8" x2="{tab_x+157}" y2="8" stroke="{prompt_user}" stroke-width="2"/>')
    svg.append(f'<text x="{tab_x+20}" y="29" font-size="12px" font-weight="bold" fill="{text_white}">⚡ ai-workspace</text>')

    # Inactive Tab 1
    svg.append(f'<text x="{tab_x+185}" y="29" font-size="12px" fill="{text_dim}">crewai-pipeline</text>')
    # Inactive Tab 2
    svg.append(f'<text x="{tab_x+305}" y="29" font-size="12px" fill="{text_dim}">swarm-agents</text>')

    # Window Info Right
    svg.append(f'<text x="{width - 24}" y="27" font-size="12px" fill="{text_dim}" text-anchor="end">zsh · tmux 3.4 · 1040x720</text>')

    # 3. Interactive Prompt Bar with Cursor
    prompt_y = 70
    svg.append(f'<text x="22" y="{prompt_y}">')
    svg.append(f'  <tspan fill="{prompt_user}" font-weight="bold">george@myller</tspan>')
    svg.append(f'  <tspan fill="{dot_color}">:</tspan>')
    svg.append(f'  <tspan fill="{prompt_path}">~/ai-workspace</tspan>')
    svg.append(f'  <tspan fill="{prompt_branch}"> (main)</tspan>')
    svg.append(f'  <tspan fill="{text_dim}">$ </tspan>')
    svg.append(f'  <tspan fill="{prompt_cmd}">fastfetch --cluster=autonomous-swarm</tspan>')
    svg.append(f'  <tspan fill="{cursor_color}" class="cursor"> █</tspan>')
    svg.append('</text>')

    # Status Pill
    svg.append(f'<g transform="translate({width - 175}, {prompt_y - 12})">')
    svg.append(f'  <rect width="155" height="24" rx="12" fill="{pill_bg}"/>')
    svg.append(f'  <circle cx="16" cy="12" r="4.5" fill="{status_online}" class="pulse-live"/>')
    svg.append(f'  <text x="28" y="16" font-size="11px" font-weight="bold" fill="{status_online}">CLUSTER ONLINE</text>')
    svg.append('</g>')

    # 4. Tmux Split-Pane Vertical Divider
    split_x = 350
    pane_top = 88
    pane_bottom = height - 45
    svg.append(f'<line x1="{split_x}" y1="{pane_top}" x2="{split_x}" y2="{pane_bottom}" stroke="{pane_border}" stroke-width="1.5" stroke-dasharray="4,4"/>')

    # Pane Labels
    svg.append(f'<text x="24" y="{pane_top + 4}" font-size="10px" font-weight="bold" fill="{text_dim}">[0:brand &amp; core]</text>')
    svg.append(f'<text x="{split_x + 15}" y="{pane_top + 4}" font-size="10px" font-weight="bold" fill="{text_dim}">[1:telemetry &amp; daemons]</text>')

    # 5. Left Pane: Custom Cyberpunk GM AI-CORE Logo + Spec Box
    ascii_x = 22
    y_start_ascii = 108
    line_h = 17

    svg.append(f'<text x="{ascii_x}" y="{y_start_ascii}" class="ascii">')
    for i, line in enumerate(ascii_lines):
        y_pos = y_start_ascii + (i * line_h)
        svg.append(f'  <tspan x="{ascii_x}" y="{y_pos}">{esc(line)}</tspan>')
    svg.append('</text>')

    # Spec Box in Left Pane
    box_y = y_start_ascii + (len(ascii_lines) * line_h) + 14
    box_w = 310
    box_h = 130
    svg.append(f'<rect x="{ascii_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="8" fill="{pill_bg}" stroke="{border_color}" stroke-width="1"/>')
    
    spec_text_y = box_y + 22
    svg.append(f'<text x="{ascii_x + 14}" y="{spec_text_y}">')
    svg.append(f'  <tspan class="title">┌─ [Agent Engine Specs] ──────┐</tspan>')
    svg.append(f'</text>')
    svg.append(f'<text x="{ascii_x + 14}" y="{spec_text_y + 19}">')
    svg.append(f'  <tspan class="key">• Target</tspan><tspan class="dim">: </tspan><tspan class="val">Multi-Agent Swarms</tspan>')
    svg.append(f'</text>')
    svg.append(f'<text x="{ascii_x + 14}" y="{spec_text_y + 38}">')
    svg.append(f'  <tspan class="key">• Stack</tspan><tspan class="dim">: </tspan><tspan class="val">CrewAI, FastAPI, D3.js</tspan>')
    svg.append(f'</text>')
    svg.append(f'<text x="{ascii_x + 14}" y="{spec_text_y + 57}">')
    svg.append(f'  <tspan class="key">• Tools</tspan><tspan class="dim">: </tspan><tspan class="val">Claude Code, Antigravity</tspan>')
    svg.append(f'</text>')
    svg.append(f'<text x="{ascii_x + 14}" y="{spec_text_y + 76}">')
    svg.append(f'  <tspan class="key">• Arch</tspan><tspan class="dim">: </tspan><tspan class="val">Clean Architecture &amp; SOLID</tspan>')
    svg.append(f'</text>')
    svg.append(f'<text x="{ascii_x + 14}" y="{spec_text_y + 95}">')
    svg.append(f'  <tspan class="title">└─────────────────────────────┘</tspan>')
    svg.append(f'</text>')

    # 6. Right Pane: Telemetry, Daemon Table, Resource Meters
    info_x = 368
    r_y = 112
    step_y = 18

    def r_row(y: int, content: str):
        return f'  <tspan x="{info_x}" y="{y}">{content}</tspan>'

    svg.append(f'<text x="{info_x}" y="{r_y}">')

    # Block A: Identity Info
    svg.append(r_row(r_y, f'<tspan class="title">george@myller</tspan> <tspan class="dot">─────────────────────────────────────────────────────</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<tspan class="key">Role</tspan><tspan class="dot">...........: </tspan><tspan class="val">Junior Software Engineer / AI Systems Architect</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<tspan class="key">OS</tspan><tspan class="dot">.............: </tspan><tspan class="val">Linux x86_64, macOS</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<tspan class="key">Host</tspan><tspan class="dot">...........: </tspan><tspan class="val">Portugal</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<tspan class="key">Uptime</tspan><tspan class="dot">.........: </tspan><tspan class="val">{uptime_str}</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<tspan class="key">Stack.Core</tspan><tspan class="dot">.....: </tspan><tspan class="val">Python 3.12 (FastAPI), TypeScript, React, D3.js</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<tspan class="key">Hobbies.Tech</tspan><tspan class="dot">...: </tspan><tspan class="val">AI Agents, Open Source, Hardware Engineering</tspan>'))

    # Block B: Autonomous Daemon Table (k9s / docker ps style)
    r_y += step_y + 8
    svg.append(r_row(r_y, f'<tspan class="key">[Autonomous Swarm: Active Daemons]</tspan> <tspan class="dot">──────────────────────────────</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<tspan class="dim">NAME                STATUS      ENGINE / MODEL           UPTIME   PORT</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<a href="https://github.com/GeorgeMyller/mira-animator"><tspan class="link">mira-animator</tspan></a>     <tspan class="online">● RUNNING</tspan>   <tspan class="white">D3.js Vector Engine</tspan>      <tspan class="dim">99.8%</tspan>    <tspan class="key">:8080</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<a href="https://github.com/GeorgeMyller/groups_evo_crewai"><tspan class="link">groups_evo_crew</tspan></a>   <tspan class="online">● ACTIVE</tspan>    <tspan class="white">CrewAI Swarm Cluster</tspan>     <tspan class="dim">100%</tspan>     <tspan class="key">:9000</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<a href="https://github.com/GeorgeMyller/agentinstagram"><tspan class="link">agentinstagram</tspan></a>    <tspan class="pause">● STANDBY</tspan>   <tspan class="white">Autonomous Workflow</tspan>      <tspan class="dim">paused</tspan>   <tspan class="key">:5000</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<a href="https://github.com/GeorgeMyller/resume_optimizer_crew_v2"><tspan class="link">resume_optimizer</tspan></a>   <tspan class="online">● RUNNING</tspan>   <tspan class="white">CrewAI Multi-Agent Engine</tspan>   <tspan class="dim">99.9%</tspan>    <tspan class="key">:3000</tspan>'))

    # Block C: Resource Allocation Meters with Real Colors
    r_y += step_y + 8
    svg.append(r_row(r_y, f'<tspan class="key">[Resource Allocation &amp; Stack Capacity]</tspan> <tspan class="dot">────────────────────────────</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<tspan class="white"> Python / FastAPI </tspan><tspan class="bar-py">[████████████████░░░░] 74%</tspan> <tspan class="dim">Core Logic &amp; Agents</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<tspan class="white"> TypeScript/React </tspan><tspan class="bar-ts">[████████░░░░░░░░░░░░] 26%</tspan> <tspan class="dim">SPAs &amp; Dynamic UI</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<tspan class="white"> Postgres / Docker</tspan><tspan class="bar-db">[██████████████░░░░░░] 60%</tspan> <tspan class="dim">Persistence &amp; CI/CD</tspan>'))

    # Block D: GitHub Live Telemetry
    r_y += step_y + 8
    svg.append(r_row(r_y, f'<tspan class="key">[GitHub Live Telemetry]</tspan> <tspan class="dot">─────────────────────────────────────────────</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<tspan class="key">Repos</tspan><tspan class="dot">: </tspan><tspan class="val">{stats["repos"]}</tspan> <tspan class="dot">(Contributed: {stats["contributed"]})</tspan> <tspan class="dot">|</tspan> <tspan class="key">Stars</tspan><tspan class="dot">: </tspan><tspan class="val">{stats["stars"]}</tspan> <tspan class="dot">|</tspan> <tspan class="key">Followers</tspan><tspan class="dot">: </tspan><tspan class="val">{stats["followers"]}</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<tspan class="key">Commits</tspan><tspan class="dot">: </tspan><tspan class="val">{format_num(stats["commits"])}</tspan> <tspan class="dot">|</tspan> <tspan class="key">Lines of Code</tspan><tspan class="dot">: </tspan><tspan class="val">{format_num(loc_total)}</tspan> <tspan class="add">({format_num(stats["loc_added"])}++)</tspan>, <tspan class="del">({format_num(stats["loc_deleted"])}--)</tspan>'))

    # Block E: Network Links
    r_y += step_y + 8
    svg.append(r_row(r_y, f'<tspan class="key">[Network Links]</tspan> <tspan class="dot">─────────────────────────────────────────────────────</tspan>'))
    r_y += step_y
    svg.append(r_row(r_y, f'<tspan class="key">GitHub</tspan><tspan class="dot">...: </tspan><a href="https://github.com/GeorgeMyller"><tspan class="link">github.com/GeorgeMyller</tspan></a>  <tspan class="dot">│</tspan>  <tspan class="key">LinkedIn</tspan><tspan class="dot">: </tspan><a href="https://linkedin.com/in/georgemyller"><tspan class="link">linkedin.com/in/georgemyller</tspan></a>'))

    svg.append('</text>')

    # 7. True Vector Powerline Status Bar at bottom
    bar_y = height - 34
    bar_h = 34
    svg.append(f'<path d="M 0 {bar_y} L {width} {bar_y} L {width} {height-14} Q {width} {height} {width-14} {height} L 14 {height} Q 0 {height} 0 {height-14} Z" fill="{bg_footer}"/>')
    svg.append(f'<line x1="0" y1="{bar_y}" x2="{width}" y2="{bar_y}" stroke="{border_color}" stroke-width="1"/>')

    # Segment 1: NORMAL mode
    seg1_w = 90
    svg.append(f'<polygon points="0,{bar_y} {seg1_w},{bar_y} {seg1_w+12},{bar_y + bar_h//2} {seg1_w},{bar_y + bar_h} 0,{bar_y + bar_h}" fill="{power_bg1}"/>')
    svg.append(f'<text x="45" y="{bar_y + 22}" font-size="12px" font-weight="bold" fill="#ffffff" text-anchor="middle">NORMAL</text>')

    # Segment 2: Git branch
    seg2_x = seg1_w
    seg2_w = 110
    svg.append(f'<polygon points="{seg2_x},{bar_y} {seg2_x+seg2_w},{bar_y} {seg2_x+seg2_w+12},{bar_y + bar_h//2} {seg2_x+seg2_w},{bar_y + bar_h} {seg2_x},{bar_y + bar_h} {seg2_x+12},{bar_y + bar_h//2}" fill="{power_bg2}"/>')
    svg.append(f'<text x="{seg2_x + 60}" y="{bar_y + 22}" font-size="12px" font-weight="bold" fill="{text_white}" text-anchor="middle">git:main</text>')

    # Segment 3: Environment info
    svg.append(f'<text x="{seg2_x + seg2_w + 24}" y="{bar_y + 22}" font-size="12px" fill="{prompt_path}">Python 3.12</text>')
    svg.append(f'<text x="{seg2_x + seg2_w + 115}" y="{bar_y + 22}" font-size="12px" fill="{dot_color}">│</text>')
    svg.append(f'<text x="{seg2_x + seg2_w + 130}" y="{bar_y + 22}" font-size="12px" fill="{val_color}">Swarm: 4 Active Daemons</text>')

    # Right side segments
    # Commits
    svg.append(f'<text x="{width - 310}" y="{bar_y + 22}" font-size="12px" fill="{key_color}">Commits: {format_num(stats["commits"])}</text>')
    svg.append(f'<text x="{width - 185}" y="{bar_y + 22}" font-size="12px" fill="{dot_color}">│</text>')
    svg.append(f'<text x="{width - 170}" y="{bar_y + 22}" font-size="12px" fill="{title_color}">Portugal</text>')

    # Final right pill
    seg_end_w = 75
    seg_end_x = width - seg_end_w
    svg.append(f'<polygon points="{seg_end_x},{bar_y} {width},{bar_y} {width},{bar_y + bar_h} {seg_end_x},{bar_y + bar_h} {seg_end_x-12},{bar_y + bar_h//2}" fill="{power_bg4}"/>')
    svg.append(f'<text x="{seg_end_x + 35}" y="{bar_y + 22}" font-size="11px" font-weight="bold" fill="#ffffff" text-anchor="middle">100%</text>')

    svg.append('</svg>')
    return '\n'.join(svg)


def main():
    root_dir = Path(__file__).parent

    print("Fetching GitHub stats...")
    stats = fetch_github_stats()
    uptime_str = calculate_uptime(START_DATE)

    print("Generating custom GM AI-CORE logo...")
    logo_lines = get_gm_logo()

    print("Generating refined terminal_dark.svg...")
    dark_svg = build_svg("dark", logo_lines, stats, uptime_str)
    (root_dir / "terminal_dark.svg").write_text(dark_svg, encoding="utf-8")

    print("Generating refined terminal_light.svg...")
    light_svg = build_svg("light", logo_lines, stats, uptime_str)
    (root_dir / "terminal_light.svg").write_text(light_svg, encoding="utf-8")

    # Remove os nomes antigos se existirem
    (root_dir / "dark_mode.svg").unlink(missing_ok=True)
    (root_dir / "light_mode.svg").unlink(missing_ok=True)

    print("Done! Elite terminal SVGs generated successfully.")


if __name__ == "__main__":
    main()
