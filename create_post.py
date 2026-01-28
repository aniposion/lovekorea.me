import os
import re
import json
import mimetypes
import pandas as pd
from PIL import Image
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from google.genai import types

# ==============================================================================
# 0. 전역 설정
# ==============================================================================
MIN_WORDS = 1500
OPENAI_MODEL = "gpt-5.2"
MAX_IMAGES_PER_POST = 4

# 수익화(affiliate) 기능 ON/OFF
ENABLE_MONETIZATION = True

# ==============================================================================
# PROVIDER ACTIVATION FLAGS
# ==============================================================================
# Set to True when affiliate partnership is ACTIVE and APPROVED
# Set to False to disable ALL affiliate content for that provider
# When False:
#   - No affiliate disclosures rendered for that provider
#   - No offer shortcodes inserted for that provider
#   - CTA blocks show neutral "Deals hub" without commission claims
# ==============================================================================
AMAZON_ASSOCIATES_ACTIVE = False   # Set True after Amazon approval
BOOKING_AFFILIATE_ACTIVE = False   # Set True after Booking.com approval
KLOOK_AFFILIATE_ACTIVE = False     # Set True after Klook approval
VIATOR_AFFILIATE_ACTIVE = False    # Set True after Viator approval
GETYOURGUIDE_AFFILIATE_ACTIVE = False

# Provider to slot prefix mapping
PROVIDER_SLOT_PREFIX = {
    "amazon": "AMZ_",
    "booking": "KOREA_HOTEL",
    "klook": "KOREA_",  # Default for tours
    "viator": "VIA_",
    "getyourguide": "GYG_",
}

# ==============================================================================
# ACTIVE_SLOTS: 슬롯별 활성화 여부
# - 비활성 슬롯은 disclosure, offer injection 모두 스킵
# - Provider flag가 False면 해당 provider의 모든 슬롯 자동 비활성화
# ==============================================================================
ACTIVE_SLOTS: Dict[str, bool] = {
    # Klook tours
    "KOREA_TOUR_DEALS": KLOOK_AFFILIATE_ACTIVE,
    "KOREA_DMZ_TOUR": KLOOK_AFFILIATE_ACTIVE,
    "KOREA_PALACE_TOUR": KLOOK_AFFILIATE_ACTIVE,
    "KOREA_KPOP_TOUR": KLOOK_AFFILIATE_ACTIVE,
    "KOREA_DAYTRIP": KLOOK_AFFILIATE_ACTIVE,
    "KOREA_FOOD_TOUR": KLOOK_AFFILIATE_ACTIVE,
    # Booking.com hotels
    "KOREA_HOTEL_DEALS": BOOKING_AFFILIATE_ACTIVE,
    "KOREA_HOTEL_LUXURY": BOOKING_AFFILIATE_ACTIVE,
    "KOREA_HOTEL_MIDRANGE": BOOKING_AFFILIATE_ACTIVE,
    "KOREA_HOTEL_BUDGET": BOOKING_AFFILIATE_ACTIVE,
    "KOREA_HANOK_STAY": BOOKING_AFFILIATE_ACTIVE,
    "KOREA_BUSAN_HOTEL": BOOKING_AFFILIATE_ACTIVE,
    # Amazon products
    "AMZ_TRAVEL_ESSENTIALS": AMAZON_ASSOCIATES_ACTIVE,
    "AMZ_KSTYLE_FEATURED": AMAZON_ASSOCIATES_ACTIVE,
    "AMZ_KOREA_ADAPTER": AMAZON_ASSOCIATES_ACTIVE,
    "AMZ_PORTABLE_WIFI": AMAZON_ASSOCIATES_ACTIVE,
    "AMZ_POWER_BANK": AMAZON_ASSOCIATES_ACTIVE,
    "AMZ_KBEAUTY_MASKS": AMAZON_ASSOCIATES_ACTIVE,
}

# 현재 연도 (프롬프트에서 사용)
CURRENT_YEAR = datetime.now().year

# ==============================================================================
# AMAZON ASSOCIATES COMPLIANCE
# ==============================================================================
# EXACT required disclosure text (do not modify!)
AMAZON_DISCLOSURE_EXACT = "As an Amazon Associate I earn from qualifying purchases."

# ==============================================================================
# COMPLIANCE GUARDRAILS
# ==============================================================================
# ⚠️ IMPORTANT: Amazon Associates Program Policy
# - NEVER use redirect links (/go/, /out/, /redirect/) for Amazon products
# - Amazon links MUST be direct links to amazon.com domains
# - All Amazon affiliate content must include AMAZON_DISCLOSURE_EXACT
# - Disclosure must appear within first 30 lines of content body
# ==============================================================================

# ==============================================================================
# 1. 설정 및 초기화
# ==============================================================================
BASE_PROJECT_DIR = Path("C:/Users/uesr/dev")
HUGO_CONTENT_DIR = Path("C:/Users/uesr/myblog/content/posts")
HUGO_IMAGE_DIR = Path("C:/Users/uesr/myblog/static/images")

load_dotenv(dotenv_path=BASE_PROJECT_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY Missing")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY Missing")

clientOpenAI = OpenAI(api_key=OPENAI_API_KEY)
clientGoogle = genai.Client(api_key=GEMINI_API_KEY)

# ==============================================================================
# 2. 유틸리티 함수
# ==============================================================================
def slugify(text: str, max_len: int = 60) -> str:
    t = (text or "").strip().lower()
    t = re.sub(r"['\"]", "", t)
    t = re.sub(r"[^a-z0-9\s-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = t.replace(" ", "-")
    return t[:max_len].strip("-") or "post"


def count_words(md: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", md or ""))


def clean_markdown_response(text: str) -> str:
    text = (text or "").strip()
    pattern = r"^```(?:markdown)?\s*(.*)\s*```$"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text

def prepend_block(md: str, block: str) -> str:
    """Always prepend a block to the top of markdown."""
    if not block:
        return md or ""
    return block.strip() + "\n\n" + (md or "").lstrip()


def strip_first_h1(md: str) -> str:
    """
    Remove the first Markdown H1 line (# ...) to avoid duplicate H1
    when the Hugo theme already renders .Title as H1.
    """
    if not md:
        return ""
    lines = md.splitlines()
    out = []
    removed = False
    for line in lines:
        if (not removed) and line.startswith("# "):
            removed = True
            continue
        out.append(line)
    return "\n".join(out).lstrip()


def extract_first_image_url(md: str) -> str:
    """Extract first markdown image URL: ![alt](url)"""
    if not md:
        return ""
    m = re.search(r'!\[[^\]]*\]\(([^)]+)\)', md)
    return (m.group(1).strip() if m else "")



def convert_to_webp_with_alt(input_path, output_dir, alt_text=None, quality=85):
    if not input_path:
        return None
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    webp_filename = f"{input_path.stem}.webp"
    webp_path = output_dir / webp_filename

    try:
        with Image.open(input_path) as img:
            img.save(webp_path, "webp", quality=quality)
    except Exception as e:
        print(f"❌ WebP Conversion Error: {e}")
        return None

    if not webp_path.exists():
        print(f"❌ WebP file not found after save: {webp_path}")
        return None
    
    if not alt_text:
        alt_text = input_path.stem
    return f'![{alt_text}](/images/{webp_filename})'


def insert_after_h1(md: str, block: str) -> str:
    if not md or not block:
        return md or ""
    lines = md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if not inserted and line.startswith("# "):
            out.append("")
            out.append(block)
            out.append("")
            inserted = True
    return "\n".join(out)


def append_section(md: str, section_md: str) -> str:
    if not section_md:
        return md
    return (md or "").rstrip() + "\n\n" + section_md.strip() + "\n"


def build_faq_section(faq: List[Dict[str, str]]) -> str:
    if not faq:
        return ""
    out = ["## FAQ"]
    for item in faq[:8]:
        q = item.get("q", "").strip()
        a = item.get("a", "").strip()
        if q and a:
            out.append(f"\n**Q: {q}**\n\n{a}")
    return "\n".join(out).strip()


def build_quick_info_box(quick: Dict[str, Any], keyword: str) -> str:
    area = (quick.get("area") or "").strip() or keyword
    best_time = (quick.get("best_time") or "").strip() or "varies by season"
    budget = (quick.get("budget") or "").strip() or "depends on your itinerary"
    transport = (quick.get("transport") or "").strip() or "subway + bus in most cities"
    recommended_for = (quick.get("recommended_for") or "").strip() or "first-time visitors"
    tldr = (quick.get("tldr") or "").strip()

    lines = [
        "> **Quick Info**",
        f"> - 📍 Area: {area}",
        f"> - 🕒 Best time: {best_time}",
        f"> - 💰 Budget: {budget}",
        f"> - 🚇 Getting there: {transport}",
        f"> - 👥 Best for: {recommended_for}",
    ]
    if tldr:
        lines.append(f"> - ✅ TL;DR: {tldr}")
    return "\n".join(lines)


# ------------------------------------------------------------------------------
# Hugo Shortcode helpers
# ------------------------------------------------------------------------------
def sc_offer(slot: str, pos: str = "mid") -> str:
    # Hugo shortcode: {{< offer slot="..." pos="..." >}}
    return f'{{{{< offer slot="{slot}" pos="{pos}" >}}}}'


def sc_lead(slot: str, pos: str = "mid") -> str:
    # (옵션) 나중에 lead shortcode 만들 때 사용
    return f'{{{{< lead slot="{slot}" pos="{pos}" >}}}}'


# ------------------------------------------------------------------------------
# Monetization inference + disclosure
# ------------------------------------------------------------------------------
def is_slot_active(slot: str) -> bool:
    """Check if a slot is active in ACTIVE_SLOTS config."""
    return ACTIVE_SLOTS.get(slot, False)


def filter_active_slots(slots: List[str]) -> List[str]:
    """Filter slots to only include active ones."""
    return [s for s in slots if is_slot_active(s)]


def has_any_active_slot(monetize: Dict[str, Any]) -> bool:
    """
    Check if monetize config has at least one active slot.
    Used for gating disclosure/offer injection.
    """
    if not monetize:
        return False
    slots = monetize.get("slots", {}) or {}
    all_slots = (slots.get("top", []) or []) + (slots.get("bottom", []) or [])
    return any(is_slot_active(s) for s in all_slots)


def has_active_amazon_slot(monetize: Dict[str, Any]) -> bool:
    """Check if any active Amazon slot exists."""
    if not monetize:
        return False
    slots = monetize.get("slots", {}) or {}
    all_slots = (slots.get("top", []) or []) + (slots.get("bottom", []) or [])
    amazon_slots = [s for s in all_slots if s.startswith("AMZ_")]
    return any(is_slot_active(s) for s in amazon_slots)


def infer_monetize(category: str) -> Dict[str, Any]:
    """
    카테고리 기반 수익화 설정 추론.
    - k-travel/k-lifestyle: booking intent (hotel + tour + amazon essentials)
    - k-fashion/k-beauty: shopping intent (amazon)
    - 나머지: info intent
    
    Note: 반환된 슬롯은 ACTIVE_SLOTS에서 활성화된 것만 실제 사용됨.
    """
    cat = (category or "").lower()

    if cat in ["k-travel", "k-lifestyle"]:
        base_slots = {
            "top": ["KOREA_TOUR_DEALS", "KOREA_HOTEL_DEALS", "AMZ_TRAVEL_ESSENTIALS"],
            "bottom": ["KOREA_TOUR_DEALS", "KOREA_HOTEL_DEALS"],
        }
        return {
            "intent": "booking",
            "verticals": ["hotel", "tour", "amazon"],
            "slots": {
                "top": filter_active_slots(base_slots["top"]),
                "bottom": filter_active_slots(base_slots["bottom"]),
            },
        }

    if cat in ["k-fashion", "k-beauty"]:
        base_slots = {
            "top": ["AMZ_KSTYLE_FEATURED"],
            "bottom": ["AMZ_KSTYLE_FEATURED"],
        }
        return {
            "intent": "shopping",
            "verticals": ["amazon"],
            "slots": {
                "top": filter_active_slots(base_slots["top"]),
                "bottom": filter_active_slots(base_slots["bottom"]),
            },
        }

    return {
        "intent": "info",
        "verticals": [],
        "slots": {"top": [], "bottom": []},
    }


def build_affiliate_disclosure_md(monetize: Dict[str, Any]) -> str:
    """
    FTC/Amazon 컴플라이언스 disclosure 생성.
    - ACTIVE provider가 하나라도 있을 때만 disclosure 표시
    - Amazon 슬롯이 활성화된 경우 AMAZON_DISCLOSURE_EXACT 문구 필수
    - Provider가 비활성화면 해당 disclosure 생략
    """
    if not monetize:
        return ""
    
    # Monetization gating: 활성 슬롯이 없으면 disclosure 불필요
    if not has_any_active_slot(monetize):
        # 비활성 상태에서는 중립적 문구만 표시 (커미션 언급 없음)
        return ""

    verticals = monetize.get("verticals", []) or []
    if not verticals:
        return ""

    lines = []
    
    # 일반 FTC disclosure (항상 먼저)
    lines.append("> **Disclosure**: This post may contain affiliate links. If you purchase through them, I may earn a commission at no extra cost to you.")
    
    # Amazon Associate 필수 문구 - EXACT TEXT REQUIRED
    # Amazon 슬롯이 활성화된 경우에만 (AMAZON_ASSOCIATES_ACTIVE=True)
    if has_active_amazon_slot(monetize) and AMAZON_ASSOCIATES_ACTIVE:
        # ⚠️ Do NOT modify this text - exact wording required by Amazon
        lines.append(f"> **{AMAZON_DISCLOSURE_EXACT}**")
    
    return "\n".join(lines)


def build_neutral_cta_block(keyword: str, position: str = "top") -> str:
    """
    중립적 CTA 블록 (커미션 언급 없음).
    Provider가 비활성화 상태일 때 사용.
    """
    if position == "top":
        return f"""## Before you start planning

If you're researching **{keyword}**, check out our curated resources:

- 📚 [Browse our Korea travel guides](/deals/)

Bookmark this page and come back when you're ready to plan!
"""
    return """## Ready to explore more?

Check out our other Korea travel guides for more inspiration.
"""


def build_mini_disclosure() -> str:
    """
    오퍼 삽입 전 표시할 미니 disclosure.
    FTC 가이드라인 준수를 위해 각 오퍼 섹션 앞에 배치.
    """
    return "*Disclosure: This section may contain affiliate links. We may earn a commission at no extra cost to you.*"


# ------------------------------------------------------------------------------
# Deals 페이지 URL 매핑 (/go/ 리다이렉트 대신 콘텐츠 허브 사용)
# ------------------------------------------------------------------------------
DEALS_URLS = {
    "tours": "/deals/korea-tours/",
    "hotels": "/deals/korea-hotels/",
    "essentials": "/deals/korea-essentials/",
}


def build_cta_block(bundle: Dict[str, Any], keyword: str, position: str = "top") -> str:
    """
    CTA 블록 생성.
    - /go/ 리다이렉트 대신 /deals/ 콘텐츠 허브로 연결
    - Amazon은 deals 페이지 내에서만 노출 (direct link 정책 준수)
    - Monetization gating: 활성 슬롯이 없으면 CTA 최소화
    
    ⚠️ COMPLIANCE: Amazon links are ONLY on /deals/ pages (direct links).
       NEVER use /go/ redirects for Amazon products.
    """
    monetize = bundle.get("monetize") or {}
    intent = (monetize.get("intent") or "").lower()
    
    # Monetization gating: 활성 슬롯이 없으면 info intent처럼 처리
    if not has_any_active_slot(monetize):
        intent = "info"

    # booking intent: 호텔/투어 → /deals/ 페이지로 유도
    if intent == "booking":
        if position == "top":
            lines = [
                "## Before you start planning",
                "",
                f"If you're thinking about **{keyword}**, check current prices and deals first:",
                "",
                f"- 🎫 [Compare Korea Tours & Day Trips]({DEALS_URLS['tours']})",
                f"- 🏨 [Find Hotels & Accommodations]({DEALS_URLS['hotels']})",
                f"- 🎒 [Get Travel Essentials]({DEALS_URLS['essentials']})",
                "",
                "**Tip:** Pick **free-cancellation** options if you're still deciding.",
            ]
            return "\n".join(lines).strip()

        # bottom
        lines = [
            "## Ready to book your trip?",
            "",
            "Take one small step now:",
            "",
            f"- [Compare tours and tickets]({DEALS_URLS['tours']})",
            f"- [Check hotel prices]({DEALS_URLS['hotels']})",
            "",
            "Even checking prices today can save money later.",
        ]
        return "\n".join(lines).strip()

    # shopping intent: K-beauty/K-fashion → deals 페이지로 유도
    if intent == "shopping":
        if position == "top":
            lines = [
                "## Quick picks",
                "",
                "Looking for curated K-style products?",
                "",
                f"- 🎒 [Browse Travel & Style Essentials]({DEALS_URLS['essentials']})",
                "",
                "Or keep reading for our in-depth recommendations below.",
            ]
        else:
            lines = [
                "## What to buy next",
                "",
                "Ready to shop? Check out our curated picks:",
                "",
                f"- [Travel Essentials & K-Beauty]({DEALS_URLS['essentials']})",
            ]
        return "\n".join(lines).strip()

    # info intent: 기본 문구만 (오퍼 없음)
    if position == "top":
        return (
            "## Before you dive in\n\n"
            "If any part of this guide feels useful, take 10 seconds to bookmark it.\n"
        )
    return (
        "## What you can do next\n\n"
        "Pick just **one** action from this guide and do it today—small steps add up.\n"
    )


# ==============================================================================
# 3. AI 리서치 & 프롬프트 생성
# ==============================================================================
def research_with_ai(keyword: str) -> str:
    print(f"🔍 [Research] Searching for: '{keyword}'...")
    try:
        prompt = f"""
As a professional researcher, perform a web search on: '{keyword}' (Korean context).
Focus on:
- what this is and why people search for it
- typical prices, tickets, or tour options if relevant
- important locations and seasonal tips
- pitfalls, common mistakes, or things people often regret
"""
        response = clientOpenAI.responses.create(
            model="gpt-4o",
            input=prompt,
            tools=[
                {
                    "type": "web_search_preview",
                    "user_location": {"type": "approximate", "country": "KR"},
                }
            ],
        )
        text = (getattr(response, "output_text", "") or "").strip()
        if text:
            print("✅ [Research] Data collected.")
            return text
        else:
            print("⚠️ [Research] Empty output_text from responses API, falling back to chat.completions...")

    except Exception as e:
        print(f"⚠️ Research via responses API failed, falling back to chat.completions: {e}")

    try:
        fallback_prompt = f"""
You are a research assistant for an English Korea travel & lifestyle blog.

Without web browsing, write a concise but useful research summary
about the topic: "{keyword}".

Focus on:
- what it is / basic background
- why visitors care about it
- practical tips and example prices in KRW if possible
- common mistakes or misunderstandings
"""
        resp2 = clientOpenAI.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You summarize topics for an English Korea travel & lifestyle blog.",
                },
                {"role": "user", "content": fallback_prompt},
            ],
        )
        text2 = (resp2.choices[0].message.content or "").strip()
        if text2:
            print("✅ [Research] Fallback summary generated.")
            return text2
    except Exception as e2:
        print(f"❌ Research fallback error: {e2}")

    print("⚠️ Research failed completely. Using minimal placeholder summary.")
    return f"General background and practical information about '{keyword}' in Korea."


def create_dynamic_image_prompt(topic: str) -> str:
    print(f"🎨 [Prompt Gen] creating prompt for '{topic}'...")
    try:
        prompt = f"""
Create a photorealistic image prompt about: "{topic}".

Include:
- clear subject and composition (camera angle, distance)
- specific setting in Korea (street, market, station, palace, river, etc.)
- realistic lighting and mood (time of day, weather)
- photographic style (lens, depth of field, film/digital, grain)

Rules:
- absolutely NO text, letters, numbers, logos, or watermarks in the image
- no posters, menus, or signs with readable text

Return ONE concise paragraph in English.
"""
        resp = clientOpenAI.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return (resp.choices[0].message.content or "").strip().replace('"', "")
    except Exception as e:
        print(f"❌ [Prompt Gen] Error: {e}")
        return (
            f"A high-quality photorealistic travel photo of {topic}, candid street "
            "photography, 35mm film grain, shallow depth of field, no text."
        )


# ==============================================================================
# 4. 이미지 생성 (Gemini 이미지 생성)
# ==============================================================================
def _save_binary_file(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def _generate_with_google_banana(prompt: str, filename_base: str) -> Optional[Path]:
    print(f"🍌 [Nano Banana] Generating: {filename_base}...")
    try:
        model = "gemini-3-pro-image-preview"

        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            )
        ]

        gc_kwargs: Dict[str, Any] = {"response_modalities": ["IMAGE", "TEXT"]}
        if hasattr(types, "ImageConfig"):
            try:
                gc_kwargs["image_config"] = types.ImageConfig(image_size="1K")
            except Exception as e_ic:
                print(f"⚠️ ImageConfig error, continuing without it: {e_ic}")

        generate_content_config = types.GenerateContentConfig(**gc_kwargs)

        for chunk in clientGoogle.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                not chunk.candidates
                or chunk.candidates[0].content is None
                or not chunk.candidates[0].content.parts
            ):
                continue

            for part in chunk.candidates[0].content.parts:
                inline = getattr(part, "inline_data", None)
                if inline and inline.data:
                    ext = mimetypes.guess_extension(inline.mime_type) or ".png"
                    path = HUGO_IMAGE_DIR / f"{filename_base}{ext}"
                    _save_binary_file(path, inline.data)
                    return path

            text_attr = getattr(chunk, "text", None)
            if text_attr:
                print(f"   (Text output: {text_attr})")

    except Exception as e:
        print(f"❌ Nano Banana Error: {e}")
        return None

    print("⚠️ Nano Banana did not return any image bytes.")
    return None

def sanitize_ai_artifacts(md: str) -> str:
    if not md:
        return ""
    # 흔한 AI 메타 문구 제거/완화
    md = re.sub(r"\byour summary supports\b.*?(?:\n|$)", "", md, flags=re.IGNORECASE)
    md = re.sub(r"\baccording to the research summary\b.*?(?:\n|$)", "", md, flags=re.IGNORECASE)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()

def generate_image(topic: str, filename_base: str, alt: str) -> str:
    full_prompt = create_dynamic_image_prompt(topic)
    saved_path = _generate_with_google_banana(full_prompt, filename_base)

    if saved_path:
        tag = convert_to_webp_with_alt(saved_path, HUGO_IMAGE_DIR, alt)
        if tag:
            print(f"✅ [Image] OK: {filename_base} -> {tag}")
            return tag

    print(f"❌ [Image] Failed: {filename_base} (topic={topic})")
    return ""


def inject_images(content: str, slug: str, title: str) -> str:
    lines = content.split("\n")
    out = []
    img_cnt = 0

    for line in lines:
        out.append(line)
        if line.startswith("## ") and img_cnt < MAX_IMAGES_PER_POST:
            h2 = line[3:].strip()
            prompt_topic = f"{title} - {h2}" if len(h2) < 40 else h2
            fname = f"{slug}-h2-{img_cnt}"
            tag = generate_image(prompt_topic, fname, h2)
            if tag:
                out.append("")
                out.append(tag)
                out.append("")
            img_cnt += 1
    return "\n".join(out)


# ------------------------------------------------------------------------------
# Offer injection (H2 기반 수익화 숏코드 삽입)
# ------------------------------------------------------------------------------
# H2 키워드 → 슬롯 매핑 규칙
H2_OFFER_RULES: List[Dict[str, Any]] = [
    {
        "keywords": ["where to book", "tickets", "pass", "tour", "how to book"],
        "slots": ["KOREA_TOUR_DEALS", "KOREA_HOTEL_DEALS"],
        "intents": ["booking", "info"],  # 적용 가능한 intent
    },
    {
        "keywords": ["typical price", "budget", "cost", "how much", "price"],
        "slots": ["KOREA_TOUR_DEALS"],
        "intents": ["booking", "info"],
    },
    {
        "keywords": ["what to pack", "essentials", "adapter", "packing", "bring", "gear"],
        "slots": ["AMZ_TRAVEL_ESSENTIALS"],
        "intents": ["booking", "info"],
    },
    {
        "keywords": ["beauty", "skincare", "makeup", "cosmetic"],
        "slots": ["AMZ_KSTYLE_FEATURED"],
        "intents": ["shopping"],
    },
    {
        "keywords": ["fashion", "style", "outfit", "clothing", "wear"],
        "slots": ["AMZ_KSTYLE_FEATURED"],
        "intents": ["shopping"],
    },
    {
        "keywords": ["buy", "shop", "purchase", "deal", "discount"],
        "slots": ["AMZ_KSTYLE_FEATURED"],
        "intents": ["shopping"],
    },
]

# 전역 슬롯별 삽입 상한
MAX_SLOT_PER_PAGE = 2


def _match_h2_to_slots(h2_text: str, intent: str) -> List[str]:
    """
    H2 텍스트와 intent에 따라 삽입할 슬롯 리스트 반환.
    매칭되는 첫 번째 규칙의 슬롯만 반환 (과도한 삽입 방지).
    """
    h2_lower = h2_text.lower()
    intent_lower = intent.lower()

    for rule in H2_OFFER_RULES:
        # intent 체크
        if intent_lower not in [i.lower() for i in rule.get("intents", [])]:
            continue

        # 키워드 매칭
        for kw in rule.get("keywords", []):
            if kw.lower() in h2_lower:
                return rule.get("slots", [])

    return []


def inject_offers(content_md: str, monetize: Dict[str, Any]) -> str:
    """
    H2 헤딩 아래에 오퍼 숏코드를 자동 삽입.

    규칙:
    - H2에 특정 키워드가 포함되면 해당 슬롯의 offer 삽입
    - 페이지당 동일 슬롯은 최대 MAX_SLOT_PER_PAGE회까지만
    - intent가 'info'인 경우 오퍼 삽입 안 함 (단, 특정 키워드 매칭 시 예외)
    - ACTIVE_SLOTS에서 비활성화된 슬롯은 삽입하지 않음
    - 각 오퍼 앞에 미니 disclosure 삽입 (FTC compliance)

    Args:
        content_md: 본문 마크다운
        monetize: infer_monetize()에서 반환된 딕셔너리

    Returns:
        오퍼가 삽입된 마크다운
    """
    if not monetize:
        return content_md
    
    # Monetization gating: 활성 슬롯이 없으면 오퍼 삽입 스킵
    if not has_any_active_slot(monetize):
        return content_md

    intent = (monetize.get("intent") or "").lower()

    # info intent는 H2 매칭 예외 케이스(packing 등)만 처리
    if intent == "info":
        # info intent여도 travel essentials 같은 건 넣을 수 있음
        pass

    lines = content_md.split("\n")
    out: List[str] = []
    slot_count: Dict[str, int] = {}  # 슬롯별 삽입 횟수 추적
    disclosure_inserted = False  # 미니 disclosure 한 번만 삽입

    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)

        # H2 감지
        if line.startswith("## "):
            h2_text = line[3:].strip()

            # H2에 맞는 슬롯 찾기
            matched_slots = _match_h2_to_slots(h2_text, intent)
            
            # ACTIVE_SLOTS 필터링 적용
            matched_slots = filter_active_slots(matched_slots)

            # 삽입할 슬롯 필터링 (중복 상한 체크)
            slots_to_insert = []
            for slot in matched_slots:
                current = slot_count.get(slot, 0)
                if current < MAX_SLOT_PER_PAGE:
                    slots_to_insert.append(slot)
                    slot_count[slot] = current + 1
                    break  # H2당 하나의 슬롯만 삽입

            if slots_to_insert:
                # H2 바로 다음 줄 확인 (이미지 태그 등 건너뛰기)
                # 이미지/빈줄을 건너뛴 뒤 오퍼 삽입
                j = i + 1
                insert_lines = []

                # 다음 줄들 수집 (이미지, 빈줄)
                while j < len(lines):
                    next_line = lines[j]
                    # 빈줄이나 이미지 태그는 먼저 out에 추가
                    if next_line.strip() == "" or next_line.strip().startswith("!["):
                        insert_lines.append(next_line)
                        j += 1
                    else:
                        break

                # 수집한 줄들 추가
                out.extend(insert_lines)

                # 첫 번째 오퍼 삽입 시 미니 disclosure 추가 (FTC compliance)
                if not disclosure_inserted:
                    out.append("")
                    out.append(build_mini_disclosure())
                    disclosure_inserted = True

                # 오퍼 삽입 (빈줄 + 오퍼 + 빈줄)
                for slot in slots_to_insert:
                    out.append("")
                    out.append(sc_offer(slot, "mid"))
                    out.append("")

                # 인덱스 조정
                i = j
                continue

        i += 1

    # 결과 정리: 연속 빈줄 3개 이상 → 2개로
    result = "\n".join(out)
    result = re.sub(r"\n{4,}", "\n\n\n", result)

    return result


# ==============================================================================
# 5. 콘텐츠 생성
# ==============================================================================
def create_blog_bundle(keyword: str, research: str) -> Dict[str, Any]:
    print("✍️ [Step 1] Planning (intent-based)...")
    plan_prompt = f"""
You are planning a Korea travel/lifestyle blog post with clear user intent.

Topic (Korean): "{keyword}"

Research summary:
{research}

=== STEP 1: DETERMINE INTENT ===
First, determine the user intent based on the topic:
- "booking": User wants to BOOK something (tours, hotels, tickets, passes)
- "shopping": User wants to BUY products (beauty, fashion, electronics)
- "info": User wants INFORMATION only (culture, history, tips, guides)

=== STEP 2: APPLY INTENT-BASED CONSTRAINTS ===

Return ONE JSON object with these keys:

1. **intent**: MUST be one of ["booking", "shopping", "info"]

2. **category**: one of ["k-beauty","k-drama","k-fashion","k-food",
   "k-lifestyle","k-movie","k-music","k-news","k-tech","k-travel",
   "k-trends","learn-korean"]

3. **seo_title**: SEO-optimized English title that MUST include:
   - either a year (e.g. {CURRENT_YEAR}) OR a number (e.g. Top 7)
   - AND intent-specific words:
     * IF intent="booking": MUST include one of ["tours", "how to book", "prices", "tickets", "pass"]
     * IF intent="shopping": MUST include one of ["where to buy", "best", "prices", "review", "top"]
     * IF intent="info": MUST include one of ["guide", "tips", "itinerary", "things to know", "complete"]

4. **slug**: short lowercase-hyphen slug (3-80 chars)

5. **meta_description**: 140-160 chars. Intent-specific:
   * booking: mention prices, booking, best tours
   * shopping: mention where to buy, best products, prices
   * info: mention guide, tips, what to know

6. **tags**: array of 6-10 short lowercase tags (max 2 words each)

7. **quick_info**: object with keys [area, best_time, budget, transport, recommended_for, tldr]

8. **faq**: array of 4-6 objects {{"q": "...", "a": "..."}}.
   * booking: At least 3 questions about money/booking
   * shopping: At least 3 questions about prices/where to buy
   * info: At least 3 questions about practical tips

9. **outline**: array of 5-8 H2-style section titles. Intent-specific:
   * IF intent="booking", MUST include:
     - "Where to Book {{topic}} Tours and Tickets"
     - "Typical Prices & Budget Examples"
     - "Money-Saving Tips"
   * IF intent="shopping", MUST include:
     - "Where to Buy {{topic}}"
     - "Price Ranges & What to Expect"
     - "Best {{topic}} Recommendations"
   * IF intent="info", MUST include:
     - "Complete Guide to {{topic}}"
     - "Tips for First-Time Visitors"
     - "What to Know Before You Go"

Return ONLY the JSON object. No explanation.
"""
    resp_plan = clientOpenAI.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": plan_prompt}],
    )
    plan = json.loads(resp_plan.choices[0].message.content)

    # monetize 자동 추론(최소 MVP)
    plan["monetize"] = infer_monetize(plan.get("category", ""))

    print("✍️ [Step 2] Writing (conversion-oriented)...")
    outline_items = plan.get("outline", []) or []
    outline_str = "\n".join([f"- {h}" for h in outline_items])

    # Anti-hallucination: 카테고리별 가격 언급 규칙
    category = plan.get("category", "").lower()
    price_guidelines = f"""
=== PRICE & BUDGET GUIDELINES (IMPORTANT - Anti-hallucination) ===
- Use PRICE RANGES, not exact prices (e.g., "₩50,000-80,000" not "₩65,000")
- Add "as of {CURRENT_YEAR}/{CURRENT_YEAR+1}" for any price ranges
- Label uncertain prices as "typical range" and add "check current prices"
- Only include specific prices if clearly supported by the research summary above
- For budget examples, use ranges: "budget travelers: ₩X-Y, mid-range: ₩A-B"
"""
    
    # k-beauty/k-fashion 카테고리 추가 규칙
    if category in ["k-beauty", "k-fashion"]:
        price_guidelines += """
- Do NOT include exact Amazon product prices or imply live Amazon pricing
- Avoid specific product costs; use phrases like "affordable range" or "premium tier"
- Focus on value comparison rather than exact numbers for products
"""

    write_prompt = f"""
Write a long-form blog post in English for a Korea travel & lifestyle blog.

Title: {plan.get('seo_title')}
Topic (Korean): {keyword}

Research summary:
{research}

Use this outline. Treat each item as an H2 heading (## ...):
{outline_str}

{price_guidelines}

Requirements:
- Start with "# {plan.get('seo_title')}" as the H1 title.
- Minimum {MIN_WORDS} words.
- Each H2 section should help with decision-making:
  - where to book, how much it costs, which option is cheaper, what to avoid.
- Use price RANGES with "as of {CURRENT_YEAR}" phrasing, not exact prices.
- Only include specific numbers if directly supported by research summary.
- Naturally include soft CTAs in text (e.g., "check current prices", "compare deals") but do NOT add actual URLs.
- Do NOT add any affiliate links or special tokens. (We will inject shortcodes separately.)
- End with a complete, encouraging sentence.

Output ONLY the Markdown content. No JSON, no backticks.
"""
    resp_content = clientOpenAI.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": write_prompt}],
    )
    plan["content"] = clean_markdown_response(resp_content.choices[0].message.content)
    return plan


def expand_content(md: str, keyword: str) -> str:
    wc = count_words(md)
    print(f"🔧 [Expand] Current: {wc} words. Target: {MIN_WORDS}+ words.")
    prompt = f"""
You are improving an existing blog post for a Korea travel & lifestyle blog.

Goal:
- Expand the post to at least {MIN_WORDS} words.
- Keep the same title and general H2 structure.
- Do NOT remove sections. Add depth:
  - extra practical examples,
  - more price RANGES in KRW (not exact prices),
  - clearer step-by-step guidance,
  - short personal-style mini stories.

=== PRICE & BUDGET GUIDELINES (Anti-hallucination) ===
- Use PRICE RANGES, not exact prices (e.g., "₩50,000-80,000" not "₩65,000")
- Add "as of {CURRENT_YEAR}/{CURRENT_YEAR+1}" for any price ranges
- Label uncertain prices as "typical range" and add "check current prices"
- Do NOT invent specific prices not already in the draft
- Do NOT include exact Amazon product prices or imply live pricing

Topic (Korean): {keyword}

Here is the current draft (Markdown):
{md}

Return ONLY the revised Markdown. No backticks.
"""
    resp = clientOpenAI.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return clean_markdown_response(resp.choices[0].message.content)


# ==============================================================================
# 6. 키워드 생성 (성과 기반 최적화)
# ==============================================================================

def load_last_month_performance() -> Dict[str, Any]:
    """
    지난달 CSV에서 성과 데이터를 로드.
    click_count, top_slot, best_pos 컬럼 활용.
    
    Returns:
        {
            "top_keywords": [...],  # 클릭 수 상위 키워드
            "top_slots": [...],     # 가장 많이 클릭된 슬롯
            "best_positions": [...], # 가장 효과적인 위치
            "patterns": [...]       # 성과 좋은 키워드 패턴
        }
    """
    from datetime import datetime, timedelta
    
    # 지난달 CSV 파일 경로
    last_month = datetime.today().replace(day=1) - timedelta(days=1)
    last_month_str = last_month.strftime("%Y-%m")
    csv_path = BASE_PROJECT_DIR / f"keywords_{last_month_str}.csv"
    
    result = {
        "top_keywords": [],
        "top_slots": [],
        "best_positions": [],
        "patterns": [],
        "summary": ""
    }
    
    if not csv_path.exists():
        print(f"📊 No performance data found for {last_month_str}")
        return result
    
    try:
        df = pd.read_csv(csv_path)
        
        # click_count 컬럼이 있는 경우에만 분석
        if "click_count" not in df.columns:
            print(f"📊 No click_count data in {last_month_str} CSV")
            return result
        
        # 상위 성과 키워드 (클릭 수 기준)
        top_df = df[df["click_count"] > 0].nlargest(10, "click_count")
        result["top_keywords"] = top_df["keyword"].tolist()
        
        # 가장 효과적인 슬롯
        if "top_slot" in df.columns:
            slot_counts = df["top_slot"].value_counts()
            result["top_slots"] = slot_counts.head(3).index.tolist()
        
        # 가장 효과적인 위치
        if "best_pos" in df.columns:
            pos_counts = df["best_pos"].value_counts()
            result["best_positions"] = pos_counts.head(3).index.tolist()
        
        # 패턴 추출 (간단한 키워드 분석)
        all_keywords = " ".join(result["top_keywords"])
        common_words = ["투어", "가이드", "가격", "예약", "추천", "맛집", "여행", "체험"]
        patterns = [w for w in common_words if w in all_keywords]
        result["patterns"] = patterns
        
        # 요약 텍스트 생성
        if result["top_keywords"]:
            result["summary"] = f"""
Last month's top performing keywords (by affiliate clicks):
- Keywords: {', '.join(result['top_keywords'][:5])}
- Best slots: {', '.join(result['top_slots']) if result['top_slots'] else 'N/A'}
- Best positions: {', '.join(result['best_positions']) if result['best_positions'] else 'N/A'}
- Patterns: {', '.join(result['patterns']) if result['patterns'] else 'travel/tour focused'}
"""
        
        print(f"📊 Loaded performance data from {last_month_str}: {len(result['top_keywords'])} top keywords")
        
    except Exception as e:
        print(f"⚠️ Error loading performance data: {e}")
    
    return result


def generate_blog_keywords(today_str: str) -> List[str]:
    """
    키워드 생성 - 지난달 성과 데이터를 반영하여 '더 돈 되는' 키워드 생성.
    """
    print("🔑 Generating keywords...")
    
    # 지난달 성과 데이터 로드
    perf = load_last_month_performance()
    perf_context = perf.get("summary", "")
    
    prompt = f"""
Generate 50 Korean blog topics (in Korean) for an English Korea travel/lifestyle blog.
Date: {today_str}

=== MONETIZATION PRIORITY ===
Our blog earns from:
1. Tour/activity bookings (Klook, Viator) - HIGHEST VALUE
2. Hotel bookings - HIGH VALUE
3. Amazon travel essentials - MEDIUM VALUE

Generate keywords that naturally lead to these conversion opportunities.

=== LAST MONTH'S PERFORMANCE DATA ===
{perf_context if perf_context else "No previous data available. Focus on booking-intent keywords."}

=== KEYWORD REQUIREMENTS ===
Strong preference (prioritize these patterns):
- Booking intent: "OO 투어 예약", "OO 패스 가격", "OO 티켓 구매"
- Price comparison: "OO vs OO 비교", "OO 가격 정리"
- How-to guides: "OO 가는 법", "OO 예약 방법"
- Best/Top lists: "OO 추천 TOP 10", "OO 베스트"
- Seasonal: current season + upcoming events
- Location-specific: 서울, 부산, 제주 specific attractions

Avoid:
- Pure information keywords with no booking potential
- News/celebrity gossip
- Overly generic topics

Return JSON ONLY:
{{ "keywords": ["..."] }}
"""
    try:
        resp = clientOpenAI.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(resp.choices[0].message.content).get("keywords", [])
    except Exception as e:
        print(f"❌ Keyword generation error: {e}")
        return []


# ==============================================================================
# 7. Hugo 저장
# ==============================================================================
def _yaml_list(items: List[str], indent: int = 2) -> str:
    sp = " " * indent
    if not items:
        return "[]"
    return "[{}]".format(", ".join([f'"{x}"' for x in items]))


def _yaml_block_monetize(m: Dict[str, Any]) -> str:
    """
    Front matter에 넣을 monetize 블록(YAML)
    """
    if not m or not m.get("verticals"):
        return ""

    intent = m.get("intent", "")
    verticals = m.get("verticals", []) or []
    slots = m.get("slots", {}) or {}
    top_slots = slots.get("top", []) or []
    bottom_slots = slots.get("bottom", []) or []

    block = [
        "monetize:",
        f'  intent: "{intent}"',
        f"  verticals: {_yaml_list(verticals, indent=2)}",
        "  slots:",
        f"    top: {_yaml_list(top_slots, indent=4)}",
        f"    bottom: {_yaml_list(bottom_slots, indent=4)}",
    ]
    return "\n".join(block)


def normalize_cover_url(url: str) -> str:
    """
    Normalize cover image URL for Hugo front matter.
    If cover.relative = true, prefer path without leading slash: images/xxx.webp
    """
    u = (url or "").strip()
    if not u:
        return ""
    # if markdown image used /images/..., strip leading slash
    if u.startswith("/"):
        u = u.lstrip("/")
    return u


def save_post(bundle: Dict[str, Any], final_md: str, cover_md: str):
    slug = bundle.get("slug", "post")
    seo_title = bundle.get("seo_title", "Korea Travel Guide").replace('"', "'")
    meta_desc = bundle.get("meta_description", "").replace('"', "'")
    category = bundle.get("category", "k-travel")
    tags = bundle.get("tags", []) or []

    # 1) cover_md (generated cover tag)에서 url 추출
    cover_url = ""
    if cover_md:
        m = re.search(r"\((.*?)\)", cover_md)
        if m:
            cover_url = (m.group(1) or "").strip()

    # 2) ✅ fallback: 본문 첫 이미지 URL을 커버로 사용
    if not cover_url:
        cover_url = extract_first_image_url(final_md)

    # 3) ✅ 최종 정규화 (relative: true에 맞춤)
    cover_url = normalize_cover_url(cover_url)

    # 4) 디버그 로그 (왜 비는지 바로 확인 가능)
    if not cover_url:
        print("⚠️ [Cover] cover_url is EMPTY. (cover generation failed + no image in content)")
    else:
        print(f"✅ [Cover] cover_url = {cover_url}")

    monetize_block = ""
    if ENABLE_MONETIZATION:
        monetize_block = _yaml_block_monetize(bundle.get("monetize") or {})

    fm_lines = [
        "---",
        f'title: "{seo_title}"',
        f"date: {datetime.now().isoformat()}",
        f'slug: "{slug}"',
        f'description: "{meta_desc}"',
        f'categories: ["{category}"]',
        f"tags: {json.dumps(tags, ensure_ascii=False)}",
        "cover:",
        f'  image: "{cover_url}"',
        f'  alt: "{seo_title}"',
        "  relative: true",
    ]
    if monetize_block:
        fm_lines.append(monetize_block)
    fm_lines.append("---")

    fm = "\n".join(fm_lines) + "\n" + (final_md or "").rstrip() + "\n"

    path = HUGO_CONTENT_DIR / f"{datetime.now().strftime('%Y-%m-%d')}-{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(fm, encoding="utf-8")
    print(f"✅ Saved to: {path}")


# ==============================================================================
# 8. 메인 실행
# ==============================================================================
if __name__ == "__main__":
    today = datetime.today()
    month_str = today.strftime("%Y-%m")
    csv_path = BASE_PROJECT_DIR / f"keywords_{month_str}.csv"

    # 1) 키워드 캐시 생성/로드
    # CSV 컬럼: keyword, done, click_count, top_slot, best_pos, slug, published_date
    if today.day == 1 or not csv_path.exists():
        keywords = generate_blog_keywords(today.strftime("%Y-%m-%d"))
        if keywords:
            df = pd.DataFrame({
                "keyword": keywords,
                "done": [False] * len(keywords),
                "click_count": [0] * len(keywords),      # GA4에서 수동 입력
                "top_slot": [""] * len(keywords),        # 가장 많이 클릭된 슬롯
                "best_pos": [""] * len(keywords),        # 가장 효과적인 위치 (top/mid/bottom)
                "slug": [""] * len(keywords),            # 발행된 포스트 slug
                "published_date": [""] * len(keywords),  # 발행일
            })
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            print(f"📝 Created new keyword CSV with performance columns: {csv_path}")
        else:
            print("❌ No keywords generated. Exiting.")
            raise SystemExit(1)
    else:
        df = pd.read_csv(csv_path)
        # 기존 CSV에 새 컬럼이 없으면 추가
        new_cols = {
            "click_count": 0,
            "top_slot": "",
            "best_pos": "",
            "slug": "",
            "published_date": ""
        }
        for col, default in new_cols.items():
            if col not in df.columns:
                df[col] = default
                print(f"  📊 Added missing column: {col}")

    remaining = df[df["done"] == False]
    if remaining.empty:
        print("✅ All keywords for this month have been processed.")
        raise SystemExit(0)

    row = remaining.sample(1)
    target_keyword = row.iloc[0]["keyword"]
    idx = row.index[0]

    print(f"\n🚀 Processing: {target_keyword}")

    # 2) 리서치
    research_data = research_with_ai(target_keyword)

    # 3) 플랜 + 본문 작성
    bundle = create_blog_bundle(target_keyword, research_data)

    # 4) 단어 수 부족 시 확장
    if count_words(bundle.get("content", "")) < MIN_WORDS:
        bundle["content"] = expand_content(bundle["content"], target_keyword)

    content_md = bundle["content"]

    # 5) 상단 블록 (Disclosure + Quick Info + Top CTA)
    qi_box = build_quick_info_box(bundle.get("quick_info", {}) or {}, target_keyword)
    cta_top = build_cta_block(bundle, target_keyword, position="top")

    top_parts = []
    if ENABLE_MONETIZATION:
        disclosure = build_affiliate_disclosure_md(bundle.get("monetize") or {})
        if disclosure:
            top_parts.append(disclosure)

    top_parts.append(qi_box)

    if cta_top:
        top_parts.append(cta_top)

    top_block = "\n\n".join([p for p in top_parts if p])
    
    content_md = insert_after_h1(content_md, top_block)
    # ✅ 1) 중복 H1 방지: 콘텐츠의 첫 H1 제거 (테마가 H1 뿌린다고 가정)
    content_md = strip_first_h1(content_md)

    # ✅ 2) H1 없이도 무조건 상단 블록 삽입
    content_md = prepend_block(content_md, top_block)

    # 6) FAQ + 하단 CTA
    if "faq" in bundle:
        faq_section = build_faq_section(bundle["faq"])
        content_md = append_section(content_md, faq_section)

    cta_bottom = build_cta_block(bundle, target_keyword, position="bottom")
    if cta_bottom:
        content_md = append_section(content_md, cta_bottom)

    slug = bundle["slug"]
    title = bundle["seo_title"]

    # 7) 커버 이미지 생성
    cover_tag = generate_image(title, f"{slug}-cover", title)

    # 8) H2 이미지 삽입
    content_md = inject_images(content_md, slug, title)

    # 9) H2 기반 오퍼 삽입 (돈 되는 H2에만)
    if ENABLE_MONETIZATION:
        content_md = inject_offers(content_md, bundle.get("monetize") or {})

    final_content = content_md
    final_content = sanitize_ai_artifacts(final_content)



    # 10) 저장
    save_post(bundle, final_content, cover_tag)

    # 11) 키워드 처리 완료 표시 + 메타데이터 저장
    df.at[idx, "done"] = True
    df.at[idx, "slug"] = slug
    df.at[idx, "published_date"] = today.strftime("%Y-%m-%d")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"✨ Done: {target_keyword} → {slug}")
