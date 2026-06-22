import math
import os
import json
import streamlit as st
import pendulum as pdlm
import datetime, pytz
from io import StringIO
from contextlib import contextmanager, redirect_stdout

import kinqimen
from kinliuren import kinliuren
import config
from cerebras_client import CerebrasClient, RateLimitError, DEFAULT_MODEL as DEFAULT_CEREBRAS_MODEL

# ------------------- 工具 -------------------
@contextmanager
def st_capture(output_func):
    with StringIO() as stdout, redirect_stdout(stdout):
        old_write = stdout.write
        def new_write(string):
            ret = old_write(string)
            output_func(stdout.getvalue())
            return ret
        stdout.write = new_write
        yield

def load_local_md(filepath):
    """讀取本地 Markdown 檔案，若檔案不存在則回傳提示訊息。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"⚠️ 找不到檔案：{filepath}"

# ------------------- AI 相關常數與函數 -------------------
CEREBRAS_MODEL_OPTIONS = [
    "qwen-3-235b-a22b-instruct-2507",
    "llama-4-scout-17b-16e-instruct",
    "llama3.1-8b",
    "llama-3.3-70b",
    "deepseek-r1-distill-llama-70b",
]
CEREBRAS_MODEL_DESCRIPTIONS = {
    "qwen-3-235b-a22b-instruct-2507": "Cerebras: Fast inference, great for rapid iteration.",
    "llama-4-scout-17b-16e-instruct": "Cerebras: Optimized for guided workflows.",
    "llama3.1-8b": "Cerebras: Light and fast for quick tasks.",
    "llama-3.3-70b": "Cerebras: Most capable for complex reasoning.",
    "deepseek-r1-distill-llama-70b": "Cerebras: DeepSeek distilled model.",
}

SYSTEM_PROMPTS_FILE = "data/system_prompts.json"

def load_system_prompts():
    DEFAULT_SYSTEM_PROMPT = (
        "당신은 《기문둔갑통종(奇門遁甲統宗)》, 《기문둔갑비급대전(奇門遁甲秘笈大全)》, 《연파조수가(煙波釣叟歌)》 등 고서와 역사 사례에 정통한 기문둔갑 대가입니다."
        "제공된 기문둔갑 포국 데이터를 바탕으로 다음을 수행하세요:\n"
        "1. 반국(盤局)의 핵심 요소(구궁·천반·지반·구성·팔문·팔신·치부치사 등)를 설명합니다.\n"
        "2. 기문둔갑 이론에 결합하여 반국의 길흉 격국과 잠재적 영향을 분석합니다.\n"
        "3. 각 궁위(宮位)의 조합 관계를 상세히 평가합니다.\n"
        "4. 실용적인 조언이나 대응 전략을 제시합니다.\n"
        "명확한 구조(단락·제목)로 제시하고, 전문적이면서도 이해하기 쉬운 한국어로 작성하며, 역사 사례나 고전 이론을 적절히 인용하세요."
    )
    try:
        with open(SYSTEM_PROMPTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        default_data = {
            "prompts": [{"name": "기문둔갑 대가", "content": DEFAULT_SYSTEM_PROMPT}],
            "selected": "기문둔갑 대가",
        }
        with open(SYSTEM_PROMPTS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)
        return default_data

def save_system_prompts(prompts_data):
    try:
        with open(SYSTEM_PROMPTS_FILE, "w", encoding="utf-8") as f:
            json.dump(prompts_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"시스템 프롬프트 저장 중 오류가 발생했습니다: {e}")
        return False

def format_qimen_results_for_prompt(q, gz_str, jq_str, lunar_info, paipan_info, is_shijia, y, m, d, h, minute):
    """Format Qi Men Dun Jia chart data into a text prompt for AI analysis."""
    eg_keys = list("巽離坤震兌艮坎乾")
    lines = [
        "以下是奇門遁甲排盤的計算結果，請根據這些數據提供詳細的分析和解釋：",
        f"日期時間：{y}年{m}月{d}日 {h}時{minute}分",
        f"起盤方式：{'時家奇門' if is_shijia else '刻家奇門'} | 排盤方式：{paipan_info}",
        f"干支：{q.get('干支', '')}",
        f"排局：{q.get('排局', '')}",
        f"節氣：{jq_str}",
        f"農曆：{lunar_info}",
    ]
    zfzs = q.get("值符值使", {})
    if zfzs:
        zf = zfzs.get("值符星宮", ["", ""])
        zs = zfzs.get("值使門宮", ["", ""])
        if len(zf) > 1:
            lines.append(f"值符星宮：天{zf[1]}宮")
        if len(zs) > 1:
            lines.append(f"值使門宮：{zs[0]}門{zs[1]}宮")

    lines.append(f"\n旬首：{q.get('旬首', '')}")

    lines.append("\n【九宮盤局】")
    for gua in eg_keys:
        dp = q.get("地盤", {}).get(gua, "")
        tp = q.get("天盤", {}).get(gua, "")
        shen = q.get("神", {}).get(gua, "")
        men = q.get("門", {}).get(gua, "")
        xing = q.get("星", {}).get(gua, "")
        lines.append(f"  {gua}宮：地盤={dp}，天盤={tp}，九星={xing}，八門={men}，八神={shen}")
    lines.append(f"  中宮：地盤={q.get('地盤', {}).get('中', '')}")

    return "\n\n".join(lines)

# ------------------- 頁面設定 -------------------
st.set_page_config(page_title="堅奇門 - 기문둔갑 포국", page_icon="🧮", layout="wide")

# ------------------- 固定聊天區域 CSS -------------------
st.markdown("""
<style>
    /* Add padding at bottom so main content is not hidden behind the fixed chat input */
    .stMainBlockContainer {
        padding-bottom: 120px !important;
    }

    /* Ensure the fixed bottom area has a solid background */
    section[data-testid="stBottom"] {
        background-color: var(--background-color, #1A1C23);
        border-top: 1px solid rgba(128, 128, 128, 0.2);
    }
    section[data-testid="stBottom"] > div {
        background-color: var(--background-color, #1A1C23);
    }
</style>
""", unsafe_allow_html=True)

pan, example, guji, log, links = st.tabs(['🧮 포국', '📜 사례', '📚 고서', '🆕 업데이트', '🔗 링크'])

with example:
    st.subheader("📜 사례")
    st.info("사례 내용은 곧 업데이트될 예정입니다. 기대해 주세요.")

with guji:
    st.markdown(load_local_md("docs/guji.md"), unsafe_allow_html=True)

with log:
    st.markdown(load_local_md("docs/log.md"), unsafe_allow_html=True)

with links:
    st.subheader("🔗 관련 링크")
    st.markdown("""
- 🐛 [GitHub Issues](https://github.com/kentang2017/kinqimen/issues)
- 📦 [PyPI - kinqimen](https://pypi.org/project/kinqimen/)
""")

# ------------------- 側邊欄 -------------------
with st.sidebar:
    pp_date = st.date_input("날짜", pdlm.now(tz='Asia/Shanghai').date())
    pp_time = st.text_input('시간 (예: 18:30)', '')
    method = st.selectbox('기반 방식', ('시가기문(時家奇門)', '각가기문(刻家奇門)'))
    paipan = st.selectbox('포국 방식', ('치윤(置閏)', '탁보(拆補)'))
    manual = st.button('수동 기반')
    instant = st.button('즉시 기반')

    is_shijia = method == '시가기문(時家奇門)'
    pai = 2 if paipan == '치윤(置閏)' else 1   # 1=탁보(拆補) 2=치윤(置閏)

    # ------------------- AI 설정 -------------------
    st.markdown("---")
    st.header("🤖 AI 설정")

    selected_model = st.selectbox(
        "AI 모델",
        options=CEREBRAS_MODEL_OPTIONS,
        index=0,
        key="cerebras_model_selector",
        help="\n".join(f"• {k}: {v}" for k, v in CEREBRAS_MODEL_DESCRIPTIONS.items()),
    )

    system_prompts_data = load_system_prompts()
    prompts_list = system_prompts_data.get("prompts", [])
    prompt_names = [p["name"] for p in prompts_list]
    selected_prompt = system_prompts_data.get("selected")

    if prompt_names:
        selected_index = 0
        if selected_prompt in prompt_names:
            selected_index = prompt_names.index(selected_prompt)

        selected_name = st.selectbox(
            "시스템 프롬프트 선택",
            options=prompt_names,
            index=selected_index,
            key="qimen_system_prompt_selector",
            help="AI 모델에 사용할 시스템 프롬프트를 선택합니다. 기문둔갑 포국 결과 분석을 지도합니다",
        )

        system_prompts_data["selected"] = selected_name

        selected_content = ""
        for prompt in prompts_list:
            if prompt["name"] == selected_name:
                selected_content = prompt["content"]
                break

        if "qimen_system_prompt" not in st.session_state:
            st.session_state.qimen_system_prompt = selected_content
        elif selected_name != st.session_state.get("last_selected_qimen_prompt"):
            st.session_state.qimen_system_prompt = selected_content

        st.session_state.last_selected_qimen_prompt = selected_name

        new_content = st.text_area(
            "시스템 프롬프트 편집",
            value=st.session_state.qimen_system_prompt,
            height=150,
            placeholder="예: 당신은 기문둔갑 전문가입니다. 포국 데이터를 바탕으로 상세한 분석을 한국어로 제공하세요...",
            key="qimen_system_editor",
        )
        st.session_state.qimen_system_prompt = new_content

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 프롬프트 업데이트", key="update_qimen_prompt_button"):
                for prompt in prompts_list:
                    if prompt["name"] == selected_name:
                        prompt["content"] = new_content
                        break
                if save_system_prompts(system_prompts_data):
                    st.toast(f"프롬프트를 업데이트했습니다: {selected_name}")
        with col2:
            if st.button("🗑️ 프롬프트 삭제", key="delete_qimen_prompt_button",
                         disabled=len(prompts_list) <= 1):
                prompts_list = [p for p in prompts_list if p["name"] != selected_name]
                system_prompts_data["prompts"] = prompts_list
                if selected_name == selected_prompt and prompts_list:
                    system_prompts_data["selected"] = prompts_list[0]["name"]
                if save_system_prompts(system_prompts_data):
                    st.toast(f"프롬프트를 삭제했습니다: {selected_name}")
                    st.rerun()

    if "qimen_form_key_suffix" not in st.session_state:
        st.session_state.qimen_form_key_suffix = 0

    name_key = f"new_qimen_prompt_name_{st.session_state.qimen_form_key_suffix}"
    content_key = f"new_qimen_prompt_content_{st.session_state.qimen_form_key_suffix}"

    with st.expander("➕ 시스템 프롬프트 추가", expanded=False):
        new_prompt_name = st.text_input("프롬프트 이름", key=name_key)
        new_prompt_content = st.text_area(
            "프롬프트 내용",
            height=100,
            placeholder="AI 분석 지시문을 입력하세요...",
            key=content_key,
        )
        if st.button("프롬프트 추가", key="add_qimen_prompt_button",
                     disabled=not new_prompt_name or not new_prompt_content):
            if new_prompt_name in prompt_names:
                st.error(f"프롬프트 이름 「{new_prompt_name}」이(가) 이미 존재합니다")
            else:
                prompts_list.append({"name": new_prompt_name, "content": new_prompt_content})
                system_prompts_data["prompts"] = prompts_list
                if save_system_prompts(system_prompts_data):
                    st.session_state.qimen_form_key_suffix += 1
                    st.toast(f"프롬프트를 추가했습니다: {new_prompt_name}")
                    st.rerun()

    if st.toggle("⚙️ 고급 설정", key="qimen_advanced_settings_toggle"):
        st.session_state.qimen_max_tokens = st.slider(
            "최대 Tokens",
            1024, 32768,
            st.session_state.get("qimen_max_tokens", 8192),
            step=1024,
            key="qimen_max_tokens_slider",
            help="AI 응답의 최대 길이를 조절합니다(값이 낮을수록 토큰 사용량이 줄어듭니다)",
        )
        st.session_state.qimen_temperature = st.slider(
            "Temperature",
            0.0, 1.5,
            st.session_state.get("qimen_temperature", 0.7),
            step=0.05,
            key="qimen_temperature_slider",
            help="AI 응답의 창의성을 조절합니다(0=정확, 1.5=높은 창의성)",
        )

# ------------------- 共用函數 -------------------
eg = list("巽離坤震兌艮坎乾")

# ------------------- 閉六戊法 SVG 產生器 -------------------
_LIUYI_TO_XUN = {
    "戊": "甲子", "己": "甲戌", "庚": "甲申",
    "辛": "甲午", "壬": "甲辰", "癸": "甲寅",
}
_SIXWU_POS = {
    "甲子": "辰", "甲戌": "寅", "甲申": "子",
    "甲午": "戌", "甲辰": "申", "甲寅": "午",
}

def generate_closed_sixwu_svg(xun_head: str, version: str = "演義版") -> str:
    """回傳完整的 SVG 字串 for 真人閉六戊法圓形十二地支圈。

    Args:
        xun_head: 當前旬首，如 "甲子"、"甲戌" 等六個甲XX旬之一。
        version: "演義版" 為逆布連土；"寶鑑版" 為順布連土。

    Returns:
        完整的 SVG XML 字串，可直接嵌入 HTML / st.markdown。
    """
    wu_branch = _SIXWU_POS.get(xun_head, "子")

    dizhi = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    yang_set = {"子", "寅", "辰", "午", "申", "戌"}
    yang_cw = ["子", "寅", "辰", "午", "申", "戌"]  # 六陽支順時針排序

    cx, cy, r, node_r = 250, 250, 175, 22

    positions = {}
    for i, dz in enumerate(dizhi):
        angle = math.radians(i * 30)
        positions[dz] = (cx + r * math.sin(angle), cy - r * math.cos(angle))

    start_idx = yang_cw.index(wu_branch)
    if version == "演義版":
        path_order = [yang_cw[(start_idx - i) % 6] for i in range(7)]
    else:
        path_order = [yang_cw[(start_idx + i) % 6] for i in range(7)]

    def shorten(x1, y1, x2, y2, m=node_r + 6):
        """Shorten a segment by margin m from both ends to avoid overlapping nodes."""
        dx, dy = x2 - x1, y2 - y1
        d = math.sqrt(dx * dx + dy * dy)
        if d == 0:
            return x1, y1, x2, y2
        return x1 + dx / d * m, y1 + dy / d * m, x2 - dx / d * m, y2 - dy / d * m

    arrows = []
    for i in range(6):
        p1 = positions[path_order[i]]
        p2 = positions[path_order[i + 1]]
        x1, y1, x2, y2 = shorten(*p1, *p2)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        d = math.sqrt(dx * dx + dy * dy)
        nx, ny = (-dy / d * 13, dx / d * 13) if d > 0 else (0, 0)
        arrows.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#CC3300" stroke-width="3.5" marker-end="url(#arw)" opacity="0.82"/>'
            f'<circle cx="{mx + nx:.1f}" cy="{my + ny:.1f}" r="10" fill="#CC3300" opacity="0.85"/>'
            f'<text x="{mx + nx:.1f}" y="{my + ny + 4.5:.1f}" text-anchor="middle" '
            f'font-size="11" fill="white" font-weight="bold">{i + 1}</text>'
        )

    nodes = []
    for dz in dizhi:
        x, y = positions[dz]
        is_wu = dz == wu_branch
        is_yang = dz in yang_set

        if is_wu:
            fill, stroke, sw = "#FFD700", "#CC0000", 3.5
            tf, fw, fs = "#CC0000", "bold", 18
        elif is_yang:
            fill, stroke, sw = "#DCF0FF", "#3A7CC7", 2.0
            tf, fw, fs = "#1A4A8A", "bold", 18
        else:
            fill, stroke, sw = "#F0F0F0", "#888888", 1.5
            tf, fw, fs = "#555555", "normal", 16

        nodes.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{node_r}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>'
        )
        nodes.append(
            f'<text x="{x:.1f}" y="{y + 6:.1f}" text-anchor="middle" font-size="{fs}" '
            f'fill="{tf}" font-family="serif" font-weight="{fw}">{dz}</text>'
        )

        if is_wu:
            ax = math.atan2(x - cx, -(y - cy))
            ox = cx + (r + node_r + 22) * math.sin(ax)
            oy = cy - (r + node_r + 22) * math.cos(ax)
            nodes.append(
                f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="16" fill="#CC0000" opacity="0.92"/>'
                f'<text x="{ox:.1f}" y="{oy + 6:.1f}" text-anchor="middle" font-size="19" '
                f'fill="white" font-weight="bold" font-family="serif">戊</text>'
            )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" '
        f'style="width:100%;height:auto;display:block;margin:0 auto">'
        f'<defs>'
        f'<marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="6" markerHeight="6" orient="auto">'
        f'<path d="M0 0 L10 5 L0 10 z" fill="#CC3300"/>'
        f'</marker>'
        f'<radialGradient id="bgg" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0%" style="stop-color:#FFFDF0"/>'
        f'<stop offset="100%" style="stop-color:#FFF0C8"/>'
        f'</radialGradient>'
        f'</defs>'
        f'<rect width="500" height="500" fill="url(#bgg)" rx="14"/>'
        f'<circle cx="{cx}" cy="{cy}" r="218" fill="none" stroke="#8B6914" '
        f'stroke-width="2.5" opacity="0.35"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#C4A44A" '
        f'stroke-width="1.5" stroke-dasharray="5 4" opacity="0.5"/>'
        f'<circle cx="{cx}" cy="{cy}" r="44" fill="#FFFBF0" stroke="#8B6914" '
        f'stroke-width="1.5" opacity="0.7"/>'
        f'<text x="{cx}" y="{cy - 5}" text-anchor="middle" font-size="14" '
        f'fill="#6B4C11" font-family="serif">六戊</text>'
        f'<text x="{cx}" y="{cy + 13}" text-anchor="middle" font-size="14" '
        f'fill="#6B4C11" font-family="serif">連土</text>'
        f'<text x="{cx}" y="28" text-anchor="middle" font-size="15" fill="#5C3317" '
        f'font-family="serif" font-weight="bold">'
        f'{xun_head}旬・戊在{wu_branch}・{version}</text>'
        f'{"".join(arrows)}'
        f'{"".join(nodes)}'
        f'</svg>'
    )

def render_pan(y, m, d, h, minute, is_shijia=True):
    gz = config.gangzhi(y, m, d, h, minute)
    jq = config.jq(y, m, d, h,minute)
    lunar_mon = dict(zip(range(1,13), config.cmonth)).get(config.lunar_date_d(y,m,d)["月"])

    if is_shijia:
        q = kinqimen.Qimen(y, m, d, h, minute).pan(pai)
        lr = kinliuren.Liuren(q["節氣"], lunar_mon, gz[2], gz[3]).result(0)
    else:
        q = kinqimen.Qimen(y, m, d, h, minute).pan_minute(pai)
        lr = kinliuren.Liuren(q["節氣"], lunar_mon, gz[3], gz[4]).result(0)

    # 提取資料
    qd = [q["地盤"][k] for k in eg]
    qt = [q.get("天盤", {}).get(k, "") for k in eg]
    god = [q["神"][k] for k in eg]
    door = [q["門"][k] for k in eg]
    star = [q["星"][k] for k in eg]
    mid = q["地盤"]["中"]
    es, egod = lr["地轉天盤"], lr["地轉天將"]
    zf_xing = q["值符值使"]["值符星宮"][1]
    zm_men  = q["值符值使"]["值使門宮"][0]
    zm_gong = q["值符值使"]["值使門宮"][1]
    # 輸出文字盤面
    print(f"{'時家奇門' if is_shijia else '刻家奇門'} | {q['排盤方式']}")
    print(f"{y}年{m}月{d}日 {h}時{minute}分\n")
    print(f"{q['干支']} | {q['排局']} | 節氣：{jq}")
    print(f"值符星宮：天{zf_xing}宮　　值使門宮：{zm_men}門{zm_gong}宮")
    print(f"農曆月：{config.lunar_date_d(y,m,d)['農曆月']}  |  "
          f"距節氣：{config.qimen_ju_name_zhirun_raw(y,m,d,h,minute)['距節氣差日數']}天\n")

    # 九宮格 ASCII 藝術（共用）
    lines = [
        f"＼  {es['巳']}{egod['巳']}  　 │  {es['午']}{egod['午']}　 │  {es['未']}{egod['未']}　 │  　 {es['申']}{egod['申']}　 ／",
        " ＼─────────┴──┬─────┴─────┬──┴──────────／",
        f" 　│　　{god[0]}　　　 │　　{god[1]}　　　 │　　{god[2]}　　　 │",
        f" 　│　　{door[0]}　　{qt[0]} │　　{door[1]}　　{qt[1]} │　　{door[2]}　　{qt[2]} │",
        f" 　│　　{star[0]}　　{qd[0]} │　　{star[1]}　　{qd[1]} │　　{star[2]}　　{qd[2]} │",
        f" {es['辰']}├───────────┼───────────┼───────────┤{es['酉']}",
        f" {egod['辰']}│　　{god[3]}　　　 │　　　　　　 │　　{god[4]}　　　 │{egod['酉']}",
        f"　─┤　　{door[3]}　　{qt[3]} │　　　　　　 │　　{door[4]}　　{qt[4]} ├─",
        f" 　│　　{star[3]}　　{qd[3]} │　　　　　{mid} │　　{star[4]}　　{qd[4]} │",
        " 　├───────────┼───────────┼───────────┤",
        f"　 │　　{god[5]}　　　 │　　{god[6]}　　　 │　　{god[7]}　　　 │",
        f" {es['卯']}│　　{door[5]}　　{qt[5]} │　　{door[6]}　　{qt[6]} │　　{door[7]}　　{qt[7]} │{es['戌']}",
        f" {egod['卯']}│　　{star[5]}　　{qd[5]} │　　{star[6]}　　{qd[6]} │　　{star[7]}　　{qd[7]} │{egod['戌']}",
        " ／─────────┬──┴─────┬─────┴──┬────────＼",
        f"／  {es['寅']}{egod['寅']}  　 │  {es['丑']}{egod['丑']}　 │  {es['子']}{egod['子']}　 │  　 {es['亥']}{egod['亥']}　 ＼",
    ]
    for line in lines:
        print(line)

    st.expander("原始資料").write(q)

    # ------------------- 閉六戊法 expander -------------------
    xun_head_jiazi = _LIUYI_TO_XUN.get(q.get("旬首", ""), "甲子")
    wu_branch = _SIXWU_POS.get(xun_head_jiazi, "子")
    yang_cw = ["子", "寅", "辰", "午", "申", "戌"]
    start_idx = yang_cw.index(wu_branch)

    with st.expander("🔒 진인폐육무법(真人閉六戊法, 법술기문) - 십이지지권 SVG 시각화"):
        version_choice = st.radio(
            "버전 선택",
            ["연의판(演義版, 역포연토)", "보감판(寶鑑版, 순포연토)"],
            horizontal=True,
            key="sixwu_version",
        )
        v = "演義版" if "演義版" in version_choice else "寶鑑版"

        svg_str = generate_closed_sixwu_svg(xun_head_jiazi, v)
        st.markdown(
            f'<div style="max-width:420px;width:100%;margin:0 auto;padding:12px 0">{svg_str}</div>',
            unsafe_allow_html=True,
        )

        if v == "演義版":
            path_order = [yang_cw[(start_idx - i) % 6] for i in range(7)]
            direction_text = "逆布（逆時針依六陽支）"
        else:
            path_order = [yang_cw[(start_idx + i) % 6] for i in range(7)]
            direction_text = "順布（順時針依六陽支）"

        path_text = "→".join(path_order[:6]) + f" → 回{path_order[0]}"

        st.markdown(f"""**📌 本旬六戊位置**：{xun_head_jiazi}旬，戊藏於 **{wu_branch}** 位

**🗺️ 連土路徑（{v} · {direction_text}）**  
{path_text}

---
**🪜 畫地儀式步驟**  
1. **起筆**：由鬼門（艮宮，東北方）起筆，以{path_order[0]}位為起點  
2. **禹步**：{"逆時針" if v == "演義版" else "順時針"}踏行，依序於六陽支（{" → ".join(path_order[:6])}）各落土一撮  
3. **天門留空**：乾宮（西北方）留「天門」不封，以納天氣  
4. **收筆**：回踏{path_order[0]}位，封閉六戊圈

---
**📿 共同主咒**
> 泰山之陽，黃河之陰，天有雷神，地有鬼兵，  
> 六戊封土，萬邪退散，護我{xun_head_jiazi}旬清淨之地，  
> 急急如九天玄女元君律令敕！

---
**⚠️ 注意事項**  
- 翌日必於乾門（西北方）開土散土，勿忘解封  
- 施法期間，施法者不可從乾門（西北）出入，否則法效消散  
- 若無法翌日解封，三日內必解，否則反傷自身
""")

    return q, jq, is_shijia


# 顯示原始 dict

# ------------------- 主畫面 -------------------
with pan:
    st.header('堅奇門排盤')

    # Track chart parameters for AI analysis
    chart_params = {}

    output = st.empty()
    with st_capture(output.code):
        # 即時盤（預設）
        if instant or (not manual and not instant):  # 頁面初載也顯示即時
            now = datetime.datetime.now(pytz.timezone('Asia/Hong_Kong'))
            q_data, jq_str, _shijia = render_pan(now.year, now.month, now.day, now.hour, now.minute, is_shijia=True)
            chart_params = {
                "q": q_data, "jq": jq_str, "is_shijia": _shijia,
                "y": now.year, "m": now.month, "d": now.day,
                "h": now.hour, "minute": now.minute,
            }

        # 手動盤
        if manual and pp_time:
            try:
                h, mnt = map(int, pp_time.split(':'))
                q_data, jq_str, _shijia = render_pan(pp_date.year, pp_date.month, pp_date.day, h, mnt, is_shijia)
                chart_params = {
                    "q": q_data, "jq": jq_str, "is_shijia": _shijia,
                    "y": pp_date.year, "m": pp_date.month, "d": pp_date.day,
                    "h": h, "minute": mnt,
                }
            except Exception:
                st.error("時間格式錯誤，請輸入如 18:30")

    # ------------------- AI 分析按鈕 -------------------
    if chart_params:
        if st.button("🔍 AI로 포국 결과 분석", key="analyze_with_ai"):
            with st.spinner("AI가 기문둔갑 포국 결과를 분석하는 중..."):
                cerebras_api_key = st.secrets.get("CEREBRAS_API_KEY", "") or os.getenv("CEREBRAS_API_KEY", "")
                if not cerebras_api_key:
                    st.error("CEREBRAS_API_KEY가 설정되지 않았습니다. .streamlit/secrets.toml 또는 환경 변수에 설정해 주세요.")
                else:
                    try:
                        client = CerebrasClient(api_key=cerebras_api_key)
                        cp = chart_params
                        lunar_info = config.lunar_date_d(cp["y"], cp["m"], cp["d"]).get("農曆月", "")
                        paipan_info = cp["q"].get("排盤方式", "")
                        qimen_prompt = format_qimen_results_for_prompt(
                            cp["q"], cp["q"].get("干支", ""), cp["jq"],
                            lunar_info, paipan_info, cp["is_shijia"],
                            cp["y"], cp["m"], cp["d"], cp["h"], cp["minute"],
                        )
                        messages = [
                            {"role": "system", "content": st.session_state.get("qimen_system_prompt", "")},
                            {"role": "user", "content": qimen_prompt},
                        ]
                        api_params = {
                            "messages": messages,
                            "model": selected_model,
                            "max_tokens": st.session_state.get("qimen_max_tokens", 8192),
                            "temperature": st.session_state.get("qimen_temperature", 0.7),
                        }
                        response = client.get_chat_completion(**api_params)
                        raw_response = response.choices[0].message.content
                        with st.expander("🤖 AI 분석 결과", expanded=True):
                            st.markdown(raw_response)
                    except RateLimitError as e:
                        st.error(f"⚠️ {e}")
                    except Exception as e:
                        st.error(f"AI 호출 중 오류가 발생했습니다: {e}")


# ------------------- LLM 聊天（固定在頁面底部） -------------------
# --- session state for chat ---
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "chat_expanded" not in st.session_state:
    st.session_state.chat_expanded = False

def _build_chat_system_prompt(chart_params_local):
    """Build the system prompt for the chat, optionally including chart context."""
    base = st.session_state.get("qimen_system_prompt", "당신은 기문둔갑 대가입니다. 한국어로 답변하세요.")
    if chart_params_local:
        cp = chart_params_local
        lunar_data = config.lunar_date_d(cp["y"], cp["m"], cp["d"])
        lunar_info = lunar_data.get("農曆月", "") if lunar_data else ""
        paipan_info = cp["q"].get("排盤方式", "")
        chart_text = format_qimen_results_for_prompt(
            cp["q"], cp["q"].get("干支", ""), cp["jq"],
            lunar_info, paipan_info, cp["is_shijia"],
            cp["y"], cp["m"], cp["d"], cp["h"], cp["minute"],
        )
        return base + "\n\n다음은 현재 포국 데이터입니다(참고용):\n" + chart_text
    return base

# --- Fixed chat UI at bottom ---
with st.container():
    col_title, col_toggle, col_clear = st.columns([6, 2, 2])
    with col_title:
        st.markdown("#### 💬 AI 채팅")
    with col_toggle:
        if st.button("📜 기록 펼치기/접기", key="toggle_chat_history"):
            st.session_state.chat_expanded = not st.session_state.chat_expanded
    with col_clear:
        if st.button("🗑️ 대화 지우기", key="clear_chat"):
            st.session_state.chat_messages = []
            st.rerun()

# Show chat history in a scrollable container
if st.session_state.chat_expanded and st.session_state.chat_messages:
    history_container = st.container(height=300)
    with history_container:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

# Chat input (at root level, auto-pins to bottom of viewport)
user_input = st.chat_input("질문을 입력해 AI에게 기문둔갑을 문의하세요...", key="chat_input")
if user_input:
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    # Auto-expand history when a message is sent
    st.session_state.chat_expanded = True

    cerebras_api_key = st.secrets.get("CEREBRAS_API_KEY", "") or os.getenv("CEREBRAS_API_KEY", "")
    if not cerebras_api_key:
        st.error("CEREBRAS_API_KEY 未設置，請在 .streamlit/secrets.toml 或環境變量中設置。")
    else:
        try:
            client = CerebrasClient(api_key=cerebras_api_key)
            system_prompt = _build_chat_system_prompt(chart_params or None)

            api_messages = [{"role": "system", "content": system_prompt}]
            # Include recent conversation history (last 20 messages to stay within token limits)
            for msg in st.session_state.chat_messages[-20:]:
                api_messages.append({"role": msg["role"], "content": msg["content"]})

            with st.spinner("AI 생각 중..."):
                response = client.get_chat_completion(
                    messages=api_messages,
                    model=selected_model,
                    max_tokens=st.session_state.get("qimen_max_tokens", 8192),
                    temperature=st.session_state.get("qimen_temperature", 0.7),
                )
                assistant_reply = response.choices[0].message.content

            st.session_state.chat_messages.append({"role": "assistant", "content": assistant_reply})
            st.rerun()
        except RateLimitError as e:
            st.error(f"⚠️ {e}")
        except Exception as e:
            st.error(f"AI 호출 중 오류가 발생했습니다: {e}")
