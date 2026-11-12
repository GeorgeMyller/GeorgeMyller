#!/usr/bin/env python3
"""Elite Dynamic GitHub Profile Terminal Card Generator.

Transforms George Myller's profile into an interactive, animated AI Command Center
with tmux split-pane, k9s-style daemon cluster table, dynamic Top-3 language bars, and vector powerline.
"""

import datetime
import html
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests

USERNAME = "GeorgeMyller"
START_DATE = datetime.datetime(2019, 4, 10)

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("ACCESS_TOKEN") or ""
HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

# Mapa de exibição automática para qualquer linguagem que entrar no Top 3 do perfil
LANGUAGE_METADATA: Dict[str, Tuple[str, str]] = {
    "Python": ("Python / FastAPI", "Core Logic & Agents"),
    "TypeScript": ("TypeScript/React", "SPAs & Dynamic UI"),
    "JavaScript": ("JavaScript / Web", "Frontend & Node.js"),
    "Go": ("Go / Systems", "Go, Swift & E2EE"),
    "Rust": ("Rust / PyO3", "Native Kernels & Perf"),
    "Swift": ("Swift / Apple", "Native iOS & macOS"),
    "Kotlin": ("Kotlin / JVM", "Mobile & Backend"),
    "Java": ("Java / Spring", "Enterprise Backend"),
    "C++": ("C++ / Native", "High-Perf Systems"),
    "C": ("C / Low-Level", "Embedded & Systems"),
    "C#": ("C# / .NET Core", "Enterprise Systems"),
    "SQL": ("SQL / BigQuery", "Data & Analytics"),
    "Shell": ("Shell / DevOps", "Automation & CI/CD"),
    "Dockerfile": ("Docker / Infra", "Containers & Cloud"),
    "HCL": ("Terraform / IaC", "Cloud Infrastructure"),
}

# Linguagens ignoradas ou agrupadas para focar apenas em linguagens de programação reais
LANGUAGE_ALIASES: Dict[str, str] = {
    "Jupyter Notebook": "Python",
    "TSX": "TypeScript",
    "JSX": "JavaScript",
    "PLpgSQL": "SQL",
}

IGNORED_LANGUAGES = {
    "HTML",
    "CSS",
    "SCSS",
    "Less",
    "Rich Text Format",
    "TeX",
    "Shell",
    "Makefile",
    "Batchfile",
    "Dockerfile",
}


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
        days_in_prev = (
            datetime.datetime(prev_year, prev_month % 12 + 1, 1) - datetime.timedelta(days=1)
        ).day
        days += days_in_prev

    if months < 0:
        years -= 1
        months += 12

    y_str = f"{years} yr{'s' if years != 1 else ''}"
    m_str = f"{months} mo{'s' if months != 1 else ''}"
    d_str = f"{days} day{'s' if days != 1 else ''}"
    return f"{y_str}, {m_str}, {d_str}"


def build_bar_blocks(percent: int, width: int = 20) -> str:
    """Constrói os 20 blocos internos da barra estilo btop."""
    clamped = max(0, min(100, percent))
    filled = round((clamped / 100) * width)
    empty = width - filled
    return f"{'█' * filled}{'░' * empty}"


def compute_dynamic_stack_bars(lang_bytes: Dict[str, int]) -> List[Tuple[str, int, str, str]]:
    """Calcula automaticamente o Top 3 de linguagens reais garantindo soma exata de 100%."""
    cleaned: Dict[str, int] = {}
    for raw_lang, size in lang_bytes.items():
        if raw_lang in IGNORED_LANGUAGES or size <= 0:
            continue
        canonical = LANGUAGE_ALIASES.get(raw_lang, raw_lang)
        cleaned[canonical] = cleaned.get(canonical, 0) + size

    # Mescla JavaScript em TypeScript se ambos existirem para consolidar Frontend/Node
    if "TypeScript" in cleaned and "JavaScript" in cleaned:
        cleaned["TypeScript"] += cleaned.pop("JavaScript")

    total_bytes = sum(cleaned.values())
    if total_bytes <= 0 or len(cleaned) == 0:
        return [
            ("Python / FastAPI", 72, "Core Logic & Agents", "bar-py"),
            ("TypeScript/React", 18, "SPAs & Dynamic UI", "bar-ts"),
            ("Go / Rust / Dock", 10, "Systems & Containers", "bar-db"),
        ]

    sorted_langs = sorted(cleaned.items(), key=lambda item: item[1], reverse=True)
    bar_classes = ["bar-py", "bar-ts", "bar-db"]

    def meta_for(lang_name: str) -> Tuple[str, str]:
        if lang_name in LANGUAGE_METADATA:
            return LANGUAGE_METADATA[lang_name]
        return (lang_name[:16], "Software Engineering")

    if len(sorted_langs) == 1:
        l1, _ = sorted_langs[0]
        lbl1, desc1 = meta_for(l1)
        return [(lbl1, 100, desc1, "bar-py")]

    if len(sorted_langs) == 2:
        (l1, b1), (l2, _) = sorted_langs
        pct1 = max(1, min(99, round((b1 / total_bytes) * 100)))
        pct2 = 100 - pct1
        lbl1, desc1 = meta_for(l1)
        lbl2, desc2 = meta_for(l2)
        return [
            (lbl1, pct1, desc1, "bar-py"),
            (lbl2, pct2, desc2, "bar-ts"),
        ]

    # 3 ou mais linguagens: Top 1, Top 2, e a 3ª barra agrega o restante somando exatos 100%
    (l1, b1), (l2, b2) = sorted_langs[0], sorted_langs[1]
    pct1 = max(1, min(98, round((b1 / total_bytes) * 100)))
    pct2 = max(1, min(99 - pct1, round((b2 / total_bytes) * 100)))
    pct3 = 100 - pct1 - pct2

    lbl1, desc1 = meta_for(l1)
    lbl2, desc2 = meta_for(l2)

    if len(sorted_langs) == 3:
        l3 = sorted_langs[2][0]
        lbl3, desc3 = meta_for(l3)
    else:
        # Combina os nomes das linguagens #3 e #4 automaticamente (ex.: "Go / Rust / Dock")
        top_rest = [name for name, _ in sorted_langs[2:4]]
        short_names = ["Dock" if n == "Dockerfile" else n[:6] for n in top_rest]
        if len(sorted_langs) > 4:
            short_names.append("+")
        combined_label = " / ".join(short_names)
        lbl3 = combined_label[:16]
        _, desc3 = meta_for(sorted_langs[2][0])

    return [
        (lbl1, pct1, desc1, bar_classes[0]),
        (lbl2, pct2, desc2, bar_classes[1]),
        (lbl3, pct3, desc3, bar_classes[2]),
    ]


def fetch_github_stats() -> Dict[str, Any]:
    """Coleta estatísticas e bytes por linguagem em todos os repositórios do GitHub."""
    stats: Dict[str, Any] = {
        "repos": 36,
        "contributed": 12,
        "stars": 18,
        "followers": 8,
        "commits": 2056,
        "loc_added": 185240,
        "loc_deleted": 42150,
        "lang_bytes": {},
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
        res = requests.get(
            f"https://api.github.com/users/{USERNAME}/repos?per_page=100",
            headers=HEADERS,
            timeout=8,
        )
        if res.status_code == 200:
            repos_data = res.json()
            if isinstance(repos_data, list):
                total_stars = sum(
                    r.get("stargazers_count", 0) for r in repos_data if isinstance(r, dict)
                )
                stats["stars"] = total_stars

                # Fallback de linguagens via REST caso não haja GITHUB_TOKEN para GraphQL
                fallback_bytes: Dict[str, int] = {}
                for r in repos_data:
                    if not isinstance(r, dict) or r.get("fork"):
                        continue
                    lang = r.get("language")
                    size_kb = max(1, int(r.get("size") or 1))
                    if lang:
                        fallback_bytes[lang] = fallback_bytes.get(lang, 0) + (size_kb * 1024)
                stats["lang_bytes"] = fallback_bytes
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
            repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
              nodes {
                name
                languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
                  edges {
                    size
                    node {
                      name
                    }
                  }
                }
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
                timeout=10,
            )
            if res.status_code == 200:
                data = res.json().get("data", {}).get("user", {})
                if data:
                    contrib = data.get("contributionsCollection", {})
                    total_commits = contrib.get("totalCommitContributions", 0) + contrib.get(
                        "restrictedContributionsCount", 0
                    )
                    total_contribs = contrib.get("contributionCalendar", {}).get(
                        "totalContributions", 0
                    )
                    stats["commits"] = max(total_commits, total_contribs, stats["commits"])
                    stats["contributed"] = data.get("repositoriesContributedTo", {}).get(
                        "totalCount", stats["contributed"]
                    )

                    # Soma exata de bytes de todas as linguagens em todos os repositórios
                    gql_lang_bytes: Dict[str, int] = {}
                    repo_nodes = data.get("repositories", {}).get("nodes", []) or []
                    for repo_node in repo_nodes:
                        if not isinstance(repo_node, dict):
                            continue
                        edges = (repo_node.get("languages") or {}).get("edges") or []
                        for edge in edges:
                            if not isinstance(edge, dict):
                                continue
                            lang_name = (edge.get("node") or {}).get("name")
                            byte_size = int(edge.get("size") or 0)
                            if lang_name and byte_size > 0:
                                gql_lang_bytes[lang_name] = (
                                    gql_lang_bytes.get(lang_name, 0) + byte_size
                                )
                    if gql_lang_bytes:
                        stats["lang_bytes"] = gql_lang_bytes
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
    stack_bars: List[Tuple[str, int, str, str]],
) -> str:
    """Monta o card de terminal interativo com alinhamento vetorial pixel-perfect."""
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
        bar_py = "#7ee787"
        bar_ts = "#79c0ff"
        bar_db = "#d2a8ff"
        power_bg1 = "#2ea043"
        power_bg2 = "#21262d"
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
        power_bg4 = "#0969da"

    width = 1040
    height = 720

    loc_total = stats["loc_added"] - stats["loc_deleted"]

    def esc(s: Any) -> str:
        return html.escape(str(s), quote=True)

    svg: List[str] = []
    svg.append("<?xml version='1.0' encoding='UTF-8'?>")
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ConsolasFallback,Consolas,Menlo,monospace" width="{width}px" height="{height}px" viewBox="0 0 {width} {height}" font-size="14px">'
    )

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
    svg.append(
        f'<rect width="{width}px" height="{height}px" rx="14" fill="{bg_main}" stroke="{border_color}" stroke-width="1.5"/>'
    )

    # 2. Window Chrome Titlebar with Tabs
    svg.append(
        f'<path d="M 0 14 Q 0 0 14 0 L {width-14} 0 Q {width} 0 {width} 14 L {width} 42 L 0 42 Z" fill="{bg_header}"/>'
    )
    svg.append(f'<line x1="0" y1="42" x2="{width}" y2="42" stroke="{border_color}" stroke-width="1"/>')

    # Window Controls (macOS style)
    svg.append('<circle cx="22" cy="21" r="6" fill="#ff5f56"/>')
    svg.append('<circle cx="42" cy="21" r="6" fill="#ffbd2e"/>')
    svg.append('<circle cx="62" cy="21" r="6" fill="#27c93f"/>')

    # Terminal Tabs
    tab_x = 95
    svg.append(f'<rect x="{tab_x}" y="8" width="165" height="34" rx="6" fill="{bg_active_tab}"/>')
    svg.append(
        f'<line x1="{tab_x+8}" y1="8" x2="{tab_x+157}" y2="8" stroke="{prompt_user}" stroke-width="2"/>'
    )
    svg.append(
        f'<text x="{tab_x+20}" y="29" font-size="12px" font-weight="bold" fill="{text_white}">⚡ ai-workspace</text>'
    )
    svg.append(f'<text x="{tab_x+185}" y="29" font-size="12px" fill="{text_dim}">sdd-architecture</text>')
    svg.append(f'<text x="{tab_x+315}" y="29" font-size="12px" fill="{text_dim}">swarm-agents</text>')

    # Window Info Right
    svg.append(
        f'<text x="{width - 24}" y="27" font-size="12px" fill="{text_dim}" text-anchor="end">zsh · tmux 3.4 · 1040x720</text>'
    )

    # 3. Interactive Prompt Bar with Cursor
    prompt_y = 70
    svg.append(
        f'<text x="22" y="{prompt_y}">'
        f'<tspan fill="{prompt_user}" font-weight="bold">george@myller</tspan>'
        f'<tspan fill="{dot_color}">:</tspan>'
        f'<tspan fill="{prompt_path}">~/ai-workspace</tspan>'
        f'<tspan fill="{prompt_branch}"> (main)</tspan>'
        f'<tspan fill="{text_dim}"> $ </tspan>'
        f'<tspan fill="{prompt_cmd}">fastfetch --cluster=autonomous-swarm</tspan>'
        f'<tspan fill="{cursor_color}" class="cursor"> █</tspan>'
        f"</text>"
    )

    # Status Pill
    svg.append(f'<g transform="translate({width - 175}, {prompt_y - 12})">')
    svg.append(f'  <rect width="155" height="24" rx="12" fill="{pill_bg}"/>')
    svg.append(f'  <circle cx="16" cy="12" r="4.5" fill="{status_online}" class="pulse-live"/>')
    svg.append(
        f'  <text x="28" y="16" font-size="11px" font-weight="bold" fill="{status_online}">CLUSTER ONLINE</text>'
    )
    svg.append("</g>")

    # 4. Tmux Split-Pane Vertical Divider
    split_x = 350
    pane_top = 88
    pane_bottom = height - 45
    svg.append(
        f'<line x1="{split_x}" y1="{pane_top}" x2="{split_x}" y2="{pane_bottom}" stroke="{pane_border}" stroke-width="1.5" stroke-dasharray="4,4"/>'
    )

    # Pane Labels
    svg.append(
        f'<text x="24" y="{pane_top + 4}" font-size="10px" font-weight="bold" fill="{text_dim}">[0:brand &amp; core]</text>'
    )
    svg.append(
        f'<text x="{split_x + 18}" y="{pane_top + 4}" font-size="10px" font-weight="bold" fill="{text_dim}">[1:telemetry &amp; daemons]</text>'
    )

    # 5. Left Pane: Custom Cyberpunk GM AI-CORE Logo + Pixel-Perfect Spec Box
    ascii_x = 22
    y_start_ascii = 108
    line_h = 17

    svg.append(f'<text x="{ascii_x}" y="{y_start_ascii}" class="ascii">')
    for i, line in enumerate(ascii_lines):
        y_pos = y_start_ascii + (i * line_h)
        svg.append(f'<tspan x="{ascii_x}" y="{y_pos}">{esc(line)}</tspan>')
    svg.append("</text>")

    # Spec Box in Left Pane (x=22 to x=332, width=310, height=130)
    box_y = y_start_ascii + (len(ascii_lines) * line_h) + 14  # 428
    box_w = 310
    box_h = 130
    svg.append(
        f'<rect x="{ascii_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="8" fill="{pill_bg}" stroke="{border_color}" stroke-width="1"/>'
    )

    b_left = ascii_x + 14           # 36
    b_right = ascii_x + box_w - 14  # 318
    b_top = box_y + 18              # 446
    b_bot = box_y + box_h - 14      # 544

    svg.append(
        f'<path d="M {b_left} {b_top + 8} L {b_left} {b_top} L {b_left + 18} {b_top}" stroke="{title_color}" stroke-width="1.8" fill="none" stroke-linecap="square"/>'
    )
    svg.append(
        f'<text x="{b_left + 25}" y="{b_top + 4}" class="title">[Agent Engine Specs]</text>'
    )
    svg.append(
        f'<path d="M {b_left + 202} {b_top} L {b_right} {b_top} L {b_right} {b_top + 8}" stroke="{title_color}" stroke-width="1.8" fill="none" stroke-linecap="square"/>'
    )

    row_x_key = b_left + 10   # 46
    row_x_col = b_left + 78   # 114
    row_x_val = b_left + 90   # 126
    spec_y1 = b_top + 23      # 469
    svg.append(
        f'<text y="{spec_y1}"><tspan x="{row_x_key}" class="key">• Target</tspan><tspan x="{row_x_col}" class="dim">:</tspan><tspan x="{row_x_val}" class="val">Multi-Agent Swarms</tspan></text>'
    )
    svg.append(
        f'<text y="{spec_y1 + 19}"><tspan x="{row_x_key}" class="key">• Stack</tspan><tspan x="{row_x_col}" class="dim">:</tspan><tspan x="{row_x_val}" class="val">FastAPI, React, Rust</tspan></text>'
    )
    svg.append(
        f'<text y="{spec_y1 + 38}"><tspan x="{row_x_key}" class="key">• Tools</tspan><tspan x="{row_x_col}" class="dim">:</tspan><tspan x="{row_x_val}" class="val">Claude, Antigravity</tspan></text>'
    )
    svg.append(
        f'<text y="{spec_y1 + 57}"><tspan x="{row_x_key}" class="key">• Arch</tspan><tspan x="{row_x_col}" class="dim">:</tspan><tspan x="{row_x_val}" class="val">Clean Arch &amp; SOLID</tspan></text>'
    )

    svg.append(
        f'<path d="M {b_left} {b_bot - 8} L {b_left} {b_bot} L {b_right} {b_bot} L {b_right} {b_bot - 8}" stroke="{title_color}" stroke-width="1.8" fill="none" stroke-linecap="square"/>'
    )

    # 6. Right Pane: Telemetry, Daemon Table, Resource Meters (x=368 to x=1016)
    info_x = 368
    right_end = 1016
    r_y = 112
    step_y = 18

    def add_section_header(y: int, title_text: str, title_cls: str, line_start_x: int) -> None:
        svg.append(
            f'<text x="{info_x}" y="{y}"><tspan class="{title_cls}">{esc(title_text)}</tspan></text>'
        )
        svg.append(
            f'<line x1="{line_start_x}" y1="{y - 4}" x2="{right_end}" y2="{y - 4}" stroke="{dot_color}" stroke-width="1.2"/>'
        )

    # Block A: Identity Info
    add_section_header(r_y, "george@myller", "title", info_x + 120)

    id_rows = [
        ("Role", "AI Systems Architect & Full-Stack Engineer"),
        ("OS", "macOS, Linux (Docker / Distroless)"),
        ("Host", "Portugal"),
        ("Uptime", uptime_str),
        ("Stack.Core", "Python 3.12 (FastAPI), TypeScript, React, Go, Swift, Rust"),
        ("Engineering", "Spec-Driven Dev (SDD), Clean Arch, TDD, Multi-Agent"),
    ]
    for key_label, val_label in id_rows:
        r_y += step_y
        dots = "." * max(2, 14 - len(key_label))
        svg.append(
            f'<text y="{r_y}">'
            f'<tspan x="{info_x}" class="key">{esc(key_label)}</tspan>'
            f'<tspan class="dot">{dots}: </tspan>'
            f'<tspan x="{info_x + 138}" class="val">{esc(val_label)}</tspan>'
            f"</text>"
        )

    # Block B: Autonomous Daemon Table (pixel-aligned columns)
    r_y += step_y + 8
    add_section_header(r_y, "[Autonomous Swarm: Active Daemons]", "key", info_x + 298)

    col_name = info_x          # 368
    col_status = info_x + 148  # 516
    col_engine = info_x + 250  # 618
    col_tests = info_x + 468   # 836
    col_port = info_x + 558    # 926

    r_y += step_y
    svg.append(
        f'<text y="{r_y}">'
        f'<tspan x="{col_name}" class="dim">NAME</tspan>'
        f'<tspan x="{col_status}" class="dim">STATUS</tspan>'
        f'<tspan x="{col_engine}" class="dim">ENGINE / ARCHITECTURE</tspan>'
        f'<tspan x="{col_tests}" class="dim">TESTS</tspan>'
        f'<tspan x="{col_port}" class="dim">PORT</tspan>'
        f"</text>"
    )

    daemons = [
        ("towerman", "https://github.com/GeorgeMyller/towerman", "● ONLINE", "Go + Swift Apple Radar", "v2.0.1", ":7352"),
        ("SimuladorRemap", "https://github.com/GeorgeMyller/SimuladorRemap", "● RUNNING", "PyO3 Rust + LAYA.ai ECU", ">85% cov", ":8000"),
        ("sintetica", "https://github.com/GeorgeMyller/sintetica", "● ACTIVE", "Pydantic v2 + PII-Guard", "570 pass", ":9000"),
        ("CodeConcilAI", "https://github.com/GeorgeMyller/CodeConcilAI", "● RUNNING", "Multi-Agent SaaS Engine", "51 pass", ":3000"),
    ]
    for d_name, d_url, d_status, d_engine, d_tests, d_port in daemons:
        r_y += step_y
        svg.append(
            f'<text y="{r_y}">'
            f'<a href="{d_url}"><tspan x="{col_name}" class="link">{esc(d_name)}</tspan></a>'
            f'<tspan x="{col_status}" class="online">{esc(d_status)}</tspan>'
            f'<tspan x="{col_engine}" class="white">{esc(d_engine)}</tspan>'
            f'<tspan x="{col_tests}" class="dim">{esc(d_tests)}</tspan>'
            f'<tspan x="{col_port}" class="key">{esc(d_port)}</tspan>'
            f"</text>"
        )

    # Block C: Dynamic Top-3 Resource Allocation & Stack Capacity (100% Automatic)
    r_y += step_y + 8
    add_section_header(r_y, "[Resource Allocation & Stack Capacity (100%)]", "key", info_x + 390)

    bar_label_x = info_x + 8       # 376
    bar_open_x = info_x + 150      # 518
    bar_blocks_x = info_x + 160    # 528
    bar_close_x = info_x + 334     # 702
    bar_pct_x = info_x + 348       # 716
    bar_desc_x = info_x + 392      # 760

    for b_label, b_pct_num, b_desc, b_cls in stack_bars:
        r_y += step_y
        b_blocks = build_bar_blocks(b_pct_num)
        b_pct_str = f"{b_pct_num:2d}%"
        svg.append(
            f'<text y="{r_y}">'
            f'<tspan x="{bar_label_x}" class="white">{esc(b_label)}</tspan>'
            f'<tspan x="{bar_open_x}" class="{b_cls}">[</tspan>'
            f'<tspan x="{bar_blocks_x}" textLength="172" lengthAdjust="spacingAndGlyphs" class="{b_cls}">{b_blocks}</tspan>'
            f'<tspan x="{bar_close_x}" class="{b_cls}">]</tspan>'
            f'<tspan x="{bar_pct_x}" class="{b_cls}">{b_pct_str}</tspan>'
            f'<tspan x="{bar_desc_x}" class="dim">{esc(b_desc)}</tspan>'
            f"</text>"
        )

    # Block D: GitHub Live Telemetry
    r_y += step_y + 8
    add_section_header(r_y, "[GitHub Live Telemetry]", "key", info_x + 202)
    r_y += step_y
    svg.append(
        f'<text x="{info_x}" y="{r_y}">'
        f'<tspan class="key">Repos</tspan><tspan class="dot">: </tspan><tspan class="val">{stats["repos"]}</tspan>'
        f'<tspan class="dot"> (Contributed: {stats["contributed"]}) | </tspan>'
        f'<tspan class="key">Stars</tspan><tspan class="dot">: </tspan><tspan class="val">{stats["stars"]}</tspan>'
        f'<tspan class="dot"> | </tspan>'
        f'<tspan class="key">Followers</tspan><tspan class="dot">: </tspan><tspan class="val">{stats["followers"]}</tspan>'
        f"</text>"
    )
    r_y += step_y
    svg.append(
        f'<text x="{info_x}" y="{r_y}">'
        f'<tspan class="key">Commits</tspan><tspan class="dot">: </tspan><tspan class="val">{format_num(stats["commits"])}</tspan>'
        f'<tspan class="dot"> | </tspan>'
        f'<tspan class="key">Lines of Code</tspan><tspan class="dot">: </tspan><tspan class="val">{format_num(loc_total)}</tspan>'
        f' <tspan class="add">({format_num(stats["loc_added"])}++)</tspan>'
        f'<tspan class="dot">, </tspan>'
        f'<tspan class="del">({format_num(stats["loc_deleted"])}--)</tspan>'
        f"</text>"
    )

    # Block E: Network Links
    r_y += step_y + 8
    add_section_header(r_y, "[Network Links]", "key", info_x + 135)
    r_y += step_y
    svg.append(
        f'<text x="{info_x}" y="{r_y}">'
        f'<tspan class="key">GitHub</tspan><tspan class="dot">...: </tspan>'
        f'<a href="https://github.com/GeorgeMyller"><tspan class="link">github.com/GeorgeMyller</tspan></a>'
        f'<tspan class="dot">  │  </tspan>'
        f'<tspan class="key">LinkedIn</tspan><tspan class="dot">: </tspan>'
        f'<a href="https://linkedin.com/in/georgemyller"><tspan class="link">linkedin.com/in/georgemyller</tspan></a>'
        f"</text>"
    )

    # 7. True Vector Powerline Status Bar at bottom
    bar_y = height - 34
    bar_h = 34
    svg.append(
        f'<path d="M 0 {bar_y} L {width} {bar_y} L {width} {height-14} Q {width} {height} {width-14} {height} L 14 {height} Q 0 {height} 0 {height-14} Z" fill="{bg_footer}"/>'
    )
    svg.append(
        f'<line x1="0" y1="{bar_y}" x2="{width}" y2="{bar_y}" stroke="{border_color}" stroke-width="1"/>'
    )

    # Segment 1: NORMAL mode
    seg1_w = 90
    svg.append(
        f'<polygon points="0,{bar_y} {seg1_w},{bar_y} {seg1_w+12},{bar_y + bar_h//2} {seg1_w},{bar_y + bar_h} 0,{bar_y + bar_h}" fill="{power_bg1}"/>'
    )
    svg.append(
        f'<text x="45" y="{bar_y + 22}" font-size="12px" font-weight="bold" fill="#ffffff" text-anchor="middle">NORMAL</text>'
    )

    # Segment 2: Git branch
    seg2_x = seg1_w
    seg2_w = 110
    svg.append(
        f'<polygon points="{seg2_x},{bar_y} {seg2_x+seg2_w},{bar_y} {seg2_x+seg2_w+12},{bar_y + bar_h//2} {seg2_x+seg2_w},{bar_y + bar_h} {seg2_x},{bar_y + bar_h} {seg2_x+12},{bar_y + bar_h//2}" fill="{power_bg2}"/>'
    )
    svg.append(
        f'<text x="{seg2_x + 60}" y="{bar_y + 22}" font-size="12px" font-weight="bold" fill="{text_white}" text-anchor="middle">git:main</text>'
    )

    # Segment 3: Environment info
    svg.append(
        f'<text x="{seg2_x + seg2_w + 24}" y="{bar_y + 22}" font-size="12px" fill="{prompt_path}">Python 3.12 · Go · Swift</text>'
    )
    svg.append(
        f'<text x="{seg2_x + seg2_w + 205}" y="{bar_y + 22}" font-size="12px" fill="{dot_color}">│</text>'
    )
    svg.append(
        f'<text x="{seg2_x + seg2_w + 222}" y="{bar_y + 22}" font-size="12px" fill="{val_color}">Swarm: 4 Flagship Systems</text>'
    )

    # Right side segments
    svg.append(
        f'<text x="{width - 310}" y="{bar_y + 22}" font-size="12px" fill="{key_color}">Commits: {format_num(stats["commits"])}</text>'
    )
    svg.append(f'<text x="{width - 185}" y="{bar_y + 22}" font-size="12px" fill="{dot_color}">│</text>')
    svg.append(
        f'<text x="{width - 170}" y="{bar_y + 22}" font-size="12px" fill="{title_color}">Portugal</text>'
    )

    # Final right pill
    seg_end_w = 75
    seg_end_x = width - seg_end_w
    svg.append(
        f'<polygon points="{seg_end_x},{bar_y} {width},{bar_y} {width},{bar_y + bar_h} {seg_end_x},{bar_y + bar_h} {seg_end_x-12},{bar_y + bar_h//2}" fill="{power_bg4}"/>'
    )
    svg.append(
        f'<text x="{seg_end_x + 35}" y="{bar_y + 22}" font-size="11px" font-weight="bold" fill="#ffffff" text-anchor="middle">100%</text>'
    )

    svg.append("</svg>")
    return "\n".join(svg)


def main() -> None:
    root_dir = Path(__file__).parent

    print("Fetching GitHub stats...")
    stats = fetch_github_stats()
    uptime_str = calculate_uptime(START_DATE)
    stack_bars = compute_dynamic_stack_bars(stats.get("lang_bytes", {}))

    for lbl, pct, desc, _ in stack_bars:
        print(f"  -> {lbl:16s}: {pct:2d}% ({desc})")

    print("Generating custom GM AI-CORE logo...")
    logo_lines = get_gm_logo()

    print("Generating refined gm_terminal_dark.svg...")
    dark_svg = build_svg("dark", logo_lines, stats, uptime_str, stack_bars)
    (root_dir / "gm_terminal_dark.svg").write_text(dark_svg, encoding="utf-8")

    print("Generating refined gm_terminal_light.svg...")
    light_svg = build_svg("light", logo_lines, stats, uptime_str, stack_bars)
    (root_dir / "gm_terminal_light.svg").write_text(light_svg, encoding="utf-8")

    (root_dir / "dark_mode.svg").unlink(missing_ok=True)
    (root_dir / "light_mode.svg").unlink(missing_ok=True)

    print("Done! Elite terminal SVGs generated successfully.")


if __name__ == "__main__":
    main()
