"""
NEWSMIND AI - Your World. Summarized.
A modern, professional AI-powered news platform built with Streamlit, OpenAI API, and GNews/NewsAPI.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import streamlit as st
from dotenv import load_dotenv

import utils.database as db
import utils.helpers as helpers
import services.ai_service as ai_service
import services.news_service as news_service

# Load environment variables
load_dotenv()

# Page configuration
favicon_path = os.path.join(os.path.dirname(__file__), "assets", "favicon.png")
st.set_page_config(
    page_title="NEWSMIND AI - Your World. Summarized.",
    page_icon=favicon_path if os.path.exists(favicon_path) else "📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize database
db.init_db()

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Dashboard"

if "selected_category" not in st.session_state:
    st.session_state["selected_category"] = "All News"

if "search_query" not in st.session_state:
    st.session_state["search_query"] = ""

if "search_history" not in st.session_state:
    st.session_state["search_history"] = ["Artificial Intelligence", "Climate Change"]

if "show_suggestions" not in st.session_state:
    st.session_state["show_suggestions"] = False

if "selected_article" not in st.session_state:
    st.session_state["selected_article"] = None

if "summaries" not in st.session_state:
    st.session_state["summaries"] = {}

if "saved_ids" not in st.session_state:
    saved = db.get_saved_articles()
    st.session_state["saved_ids"] = {a["id"] for a in saved}

if "news_country" not in st.session_state:
    st.session_state["news_country"] = "us"

if "news_lang" not in st.session_state:
    st.session_state["news_lang"] = "en"

if "last_updated" not in st.session_state:
    st.session_state["last_updated"] = datetime.now().strftime("%b %d, %Y • %I:%M %p")

if "daily_brief" not in st.session_state:
    st.session_state["daily_brief"] = None

if "preferred_topics" not in st.session_state:
    st.session_state["preferred_topics"] = ["AI and Technology", "Business and Finance", "World Politics"]

if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [
        {
            "role": "assistant",
            "content": "👋 Welcome to **NEWSMIND AI Assistant**. I can summarize complex stories, compare reports across sources, and answer questions grounded strictly in today's active news feeds. How can I assist your news exploration today?",
            "cited_articles": [],
        }
    ]


# -----------------------------------------------------------------------------
# Cached Data Fetching
# -----------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def get_cached_news(category: str, query: str, country: str = "us", lang: str = "en"):
    """Fetches and caches news articles based on query or category."""
    if query:
        return news_service.search_news(query, category=category, country=country, lang=lang)
    return news_service.fetch_top_headlines(category=category, country=country, lang=lang)


def trigger_refresh():
    """Clears cached news data and refreshes timestamps."""
    st.cache_data.clear()
    st.session_state["search_query"] = ""
    st.session_state["selected_article"] = None
    st.session_state["last_updated"] = datetime.now().strftime("%b %d, %Y • %I:%M %p")
    st.toast("NEWSMIND AI feed refreshed with latest reports!", icon="🔄")


def handle_search_selection(keyword: str):
    """Executes a search from keyword or suggestion pill."""
    clean_k = keyword.strip()
    st.session_state["search_query"] = clean_k
    st.session_state["selected_article"] = None
    if clean_k and clean_k not in st.session_state["search_history"]:
        st.session_state["search_history"].insert(0, clean_k)
        st.session_state["search_history"] = st.session_state["search_history"][:8]
    if st.session_state["current_page"] in ["Article Details", "Settings", "About"]:
        st.session_state["current_page"] = "Dashboard"
    st.session_state["show_suggestions"] = False


# -----------------------------------------------------------------------------
# Component: Header
# -----------------------------------------------------------------------------
def render_header():
    """Renders a sleek, branded NEWSMIND AI header."""
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")

    with st.container():
        h_left, h_right = st.columns([5, 5])

        with h_left:
            logo_cols = st.columns([1, 5.5])
            with logo_cols[0]:
                if os.path.exists(logo_path):
                    st.image(logo_path, width=56)
                else:
                    st.markdown("## 🧠")
            with logo_cols[1]:
                st.markdown(
                    """
                    <div style='padding-top: 2px;'>
                        <h1 class='brand-title'>NEWSMIND <span class='brand-title-accent'>AI</span></h1>
                        <p class='brand-tagline'>Your World. Summarized.</p>
                        <p class='brand-subtitle'>Stay informed. Understand more. Save time.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with h_right:
            # Search Bar row
            current_q = st.session_state.get("search_query", "")
            s_input_col, s_btn_col, r_btn_col, set_btn_col = st.columns([5, 1.2, 1.2, 1.2])

            with s_input_col:
                new_q = st.text_input(
                    "Search",
                    value=current_q,
                    placeholder="🔍 Search topics, companies, events...",
                    label_visibility="collapsed",
                    key="header_search_input",
                )

            with s_btn_col:
                if st.button("Search", use_container_width=True):
                    handle_search_selection(new_q)
                    st.rerun()

            with r_btn_col:
                if st.button("🔄", help="Refresh latest news", use_container_width=True):
                    trigger_refresh()
                    st.rerun()

            with set_btn_col:
                if st.button("⚙️", help="Open Settings", use_container_width=True):
                    st.session_state["current_page"] = "Settings"
                    st.rerun()

            # Meta sub-row
            sub1, sub2 = st.columns([3, 2])
            with sub1:
                is_live, prov, _ = news_service.check_api_status()
                prov_icon = "🟢" if is_live else "🟡"
                st.markdown(
                    f"<div style='font-size: 0.76rem; color: #475569; padding-top: 4px;'>"
                    f"{prov_icon} <strong>Feed:</strong> {prov} • 🕒 {st.session_state['last_updated']}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with sub2:
                sugg_label = "💡 Close Suggestions" if st.session_state["show_suggestions"] else "💡 Smart Suggestions"
                if st.button(sugg_label, key="toggle_sugg_btn", use_container_width=True):
                    st.session_state["show_suggestions"] = not st.session_state["show_suggestions"]
                    st.rerun()

    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Component: Smart Search Suggestions Drawer
# -----------------------------------------------------------------------------
def render_search_suggestions():
    """Renders interactive clickable search suggestions."""
    if not st.session_state.get("show_suggestions", False):
        return

    with st.container(border=True):
        st.markdown("<h4 style='margin: 0 0 10px 0; color: #1E3A8A; font-size: 1.05rem;'>💡 Smart Search Suggestions</h4>", unsafe_allow_html=True)

        tab1, tab2, tab3, tab4 = st.tabs(["🔥 Trending Searches", "⚡ Quick Searches", "🏷️ Popular Categories", "🕒 Recent History"])

        with tab1:
            trending = [
                "Artificial Intelligence", "OpenAI", "Google", "Cybersecurity",
                "Space Exploration", "Climate Change", "Stock Market", "Cricket",
                "Indian Politics", "Technology Startups",
            ]
            t_cols = st.columns(5)
            for i, item in enumerate(trending):
                col = t_cols[i % 5]
                if col.button(f"🔥 {item}", key=f"sugg_trend_{i}", use_container_width=True):
                    handle_search_selection(item)
                    st.rerun()

        with tab2:
            quick = [
                "Latest AI News", "Today's Top Stories", "Latest News in India",
                "Global Headlines", "Startup News", "Latest Science Discoveries",
            ]
            q_cols = st.columns(3)
            for i, item in enumerate(quick):
                col = q_cols[i % 3]
                if col.button(f"⚡ {item}", key=f"sugg_quick_{i}", use_container_width=True):
                    handle_search_selection(item)
                    st.rerun()

        with tab3:
            cats = [
                ("💻 Technology", "Technology"),
                ("📈 Business", "Business"),
                ("🏛️ Politics", "Politics"),
                ("⚽ Sports", "Sports"),
                ("🔬 Science", "Science"),
                ("🏥 Health", "Health"),
                ("🎬 Entertainment", "Entertainment"),
            ]
            c_cols = st.columns(4)
            for i, (label, val) in enumerate(cats):
                col = c_cols[i % 4]
                if col.button(label, key=f"sugg_cat_{i}", use_container_width=True):
                    st.session_state["selected_category"] = val
                    st.session_state["search_query"] = ""
                    st.session_state["show_suggestions"] = False
                    st.session_state["current_page"] = "Dashboard"
                    st.rerun()

        with tab4:
            history = st.session_state.get("search_history", [])
            if history:
                h_cols = st.columns(min(len(history), 4))
                for i, h_item in enumerate(history[:4]):
                    col = h_cols[i % 4]
                    if col.button(f"🕒 {h_item}", key=f"sugg_hist_{i}", use_container_width=True):
                        handle_search_selection(h_item)
                        st.rerun()
            else:
                st.caption("No searches recorded in this session yet.")


# -----------------------------------------------------------------------------
# Component: Summary Statistics Bar
# -----------------------------------------------------------------------------
def render_summary_statistics(articles_count: int):
    """Displays genuine, data-backed summary statistics at the top of Dashboard."""
    saved_count = len(st.session_state["saved_ids"])
    summarized_count = len(st.session_state["summaries"])
    categories_count = len([c for c in news_service.CATEGORIES if c != "All News"])

    s1, s2, s3, s4 = st.columns(4)

    with s1:
        st.markdown(
            f"""
            <div class='metrics-card'>
                <div class='metrics-label'>📰 Articles Available</div>
                <div class='metrics-value'>{articles_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with s2:
        st.markdown(
            f"""
            <div class='metrics-card' style='border-top-color: #0284C7;'>
                <div class='metrics-label'>🏷️ Categories</div>
                <div class='metrics-value'>{categories_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with s3:
        st.markdown(
            f"""
            <div class='metrics-card' style='border-top-color: #7C3AED;'>
                <div class='metrics-label'>⚡ Summaries Generated</div>
                <div class='metrics-value'>{summarized_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with s4:
        st.markdown(
            f"""
            <div class='metrics-card' style='border-top-color: #059669;'>
                <div class='metrics-label'>🔖 Saved Articles</div>
                <div class='metrics-value'>{saved_count}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Component: AI Summary Panel
# -----------------------------------------------------------------------------
def render_summary_content(summary: Dict[str, Any], article: Dict[str, Any]):
    """Renders the professional 4-part AI summary panel with copy action."""
    st.markdown(
        """
        <div class='summary-container'>
            <div class='summary-title'>⚡ NEWSMIND AI SUMMARY</div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Quick Summary
    st.markdown("<div class='summary-section-label'>📌 QUICK SUMMARY</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='summary-body'>{summary.get('quick_summary', 'Summary not available.')}</div>", unsafe_allow_html=True)

    # 2. Key Takeaways
    takeaways = summary.get("key_takeaways") or summary.get("key_points") or []
    if takeaways:
        st.markdown("<div class='summary-section-label'>🎯 KEY TAKEAWAYS</div>", unsafe_allow_html=True)
        for pt in takeaways:
            st.markdown(f"- {pt}")

    # 3. Why It Matters
    why_matters = summary.get("why_it_matters")
    if why_matters:
        st.markdown("<div class='summary-section-label'>💡 WHY IT MATTERS</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='summary-body'>{why_matters}</div>", unsafe_allow_html=True)

    # 4. Category & Source
    cat = summary.get("category") or article.get("category", "General")
    source_name = article.get("source", "Publisher")
    url = article.get("url", "#")
    st.markdown(
        f"<div style='margin-top: 10px; font-size: 0.78rem; color: #475569; display: flex; gap: 15px;'>"
        f"<span><strong>🏷️ Category:</strong> {cat}</span>"
        f"<span><strong>📰 Source:</strong> <a href='{url}' target='_blank'>{source_name}</a></span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Limitation note
    if summary.get("limitation_note"):
        st.caption(f"ℹ️ {summary['limitation_note']}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Copy summary text helper
    copy_text = f"NEWSMIND AI BRIEF: {article.get('title')}\n\nQuick Summary:\n{summary.get('quick_summary')}\n\nKey Takeaways:\n" + "\n".join([f"- {t}" for t in takeaways]) + f"\n\nSource: {url}"
    st.text_area("Copy summary text", value=copy_text, height=70, label_visibility="collapsed", key=f"copy_area_{article['id']}")


# -----------------------------------------------------------------------------
# Component: Featured Story (Hero Banner)
# -----------------------------------------------------------------------------
def render_featured_story(article: Dict[str, Any]):
    """Renders the top breaking or featured article in a prominent hero format."""
    art_id = article["id"]
    cat = article.get("category", "All News")
    cat_icon = helpers.get_category_icon(cat)
    source = article.get("source", "News Source")
    rel_time = helpers.time_ago(article.get("published_at"))
    img_url = article.get("url_to_image") or helpers.get_category_placeholder(cat)

    with st.container():
        st.markdown(
            f"""
            <div class='hero-card'>
                <div class='hero-tag'>⭐ FEATURED STORY • {cat_icon} {cat.upper()}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        f_cols = st.columns([1.6, 2.4])
        with f_cols[0]:
            try:
                st.image(img_url, use_container_width=True)
            except Exception:
                fallback = helpers.get_category_placeholder(cat)
                if fallback:
                    st.image(fallback, use_container_width=True)

        with f_cols[1]:
            st.markdown(
                f"<span class='source-pill'>{source}</span> "
                f"<span class='time-pill' style='margin-left: 8px;'>🕒 {rel_time}</span>",
                unsafe_allow_html=True,
            )
            title = article.get("title", "Untitled Article")
            st.markdown(f"<div class='hero-headline'>{title}</div>", unsafe_allow_html=True)

            desc = article.get("description") or article.get("content") or ""
            st.markdown(f"<div class='hero-description'>{desc}</div>", unsafe_allow_html=True)

            # Actions
            fb1, fb2, fb3 = st.columns([1.2, 1, 1])
            with fb1:
                if st.button("⚡ AI Summary", key=f"hero_sum_{art_id}", use_container_width=True, type="primary"):
                    if art_id not in st.session_state["summaries"]:
                        with st.spinner("NEWSMIND AI synthesizing executive brief..."):
                            summary = ai_service.summarize_article(article)
                            st.session_state["summaries"][art_id] = summary
                            if art_id in st.session_state["saved_ids"]:
                                db.save_article(article, ai_summary=summary)
                    st.rerun()

            with fb2:
                st.link_button("🔗 Read Article", url=article.get("url", "#"), use_container_width=True)

            with fb3:
                is_saved = art_id in st.session_state["saved_ids"]
                btn_label = "🔖 Saved" if is_saved else "🤍 Save Story"
                if st.button(btn_label, key=f"hero_save_{art_id}", use_container_width=True):
                    if is_saved:
                        db.remove_saved_article(art_id)
                        st.session_state["saved_ids"].remove(art_id)
                        st.toast("Removed from saved articles.", icon="🗑️")
                    else:
                        existing_sum = st.session_state["summaries"].get(art_id)
                        db.save_article(article, ai_summary=existing_sum)
                        st.session_state["saved_ids"].add(art_id)
                        st.toast("Saved to your personal collection!", icon="🔖")
                    st.rerun()

        # Render summary if active
        if art_id in st.session_state["summaries"]:
            render_summary_content(st.session_state["summaries"][art_id], article)

    st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Component: News Card
# -----------------------------------------------------------------------------
def render_news_card(article: Dict[str, Any], container):
    """Renders a standard news card with thumbnail, headline, and actions."""
    art_id = article["id"]
    cat = article.get("category", "All News")
    cat_icon = helpers.get_category_icon(cat)
    source = article.get("source", "News Source")
    rel_time = helpers.time_ago(article.get("published_at"))
    img_url = article.get("url_to_image") or helpers.get_category_placeholder(cat)

    with container:
        with st.container(border=True):
            # Header Row
            top1, top2 = st.columns([3, 2])
            with top1:
                st.markdown(
                    f"<span class='category-pill'>{cat_icon} {cat}</span> "
                    f"<span class='source-pill'>{source}</span>",
                    unsafe_allow_html=True,
                )
            with top2:
                st.markdown(f"<div style='text-align: right;' class='time-pill'>🕒 {rel_time}</div>", unsafe_allow_html=True)

            # Thumbnail
            try:
                st.image(img_url, use_container_width=True)
            except Exception:
                fallback = helpers.get_category_placeholder(cat)
                if fallback:
                    st.image(fallback, use_container_width=True)

            # Headline
            title = article.get("title", "Untitled Article")
            st.markdown(f"<div class='card-headline'>{title}</div>", unsafe_allow_html=True)

            # Description
            desc = article.get("description") or article.get("content") or ""
            st.markdown(f"<div class='card-description'>{helpers.truncate_text(desc, 125)}</div>", unsafe_allow_html=True)

            # Render Summary
            if art_id in st.session_state["summaries"]:
                render_summary_content(st.session_state["summaries"][art_id], article)

            # Actions Row
            b1, b2, b3 = st.columns([1.2, 1, 1])

            with b1:
                if st.button("⚡ AI Summary", key=f"btn_sum_{art_id}", use_container_width=True):
                    if art_id not in st.session_state["summaries"]:
                        with st.spinner("NEWSMIND AI analyzing article..."):
                            summary = ai_service.summarize_article(article)
                            st.session_state["summaries"][art_id] = summary
                            if art_id in st.session_state["saved_ids"]:
                                db.save_article(article, ai_summary=summary)
                    st.rerun()

            with b2:
                st.link_button("🔗 Read", url=article.get("url", "#"), use_container_width=True)

            with b3:
                is_saved = art_id in st.session_state["saved_ids"]
                btn_label = "🔖 Saved" if is_saved else "🤍 Save"
                if st.button(btn_label, key=f"btn_save_{art_id}", use_container_width=True):
                    if is_saved:
                        db.remove_saved_article(art_id)
                        st.session_state["saved_ids"].remove(art_id)
                        st.toast("Removed from saved.", icon="🗑️")
                    else:
                        existing_sum = st.session_state["summaries"].get(art_id)
                        db.save_article(article, ai_summary=existing_sum)
                        st.session_state["saved_ids"].add(art_id)
                        st.toast("Saved to bookmarks!", icon="🔖")
                    st.rerun()


# -----------------------------------------------------------------------------
# Component: Daily Brief Panel
# -----------------------------------------------------------------------------
def render_daily_brief_section(articles: List[Dict[str, Any]]):
    """Renders the Daily News Brief generator and display."""
    with st.container():
        brief_bar1, brief_bar2, brief_bar3 = st.columns([4, 1.5, 1.5])
        with brief_bar1:
            st.markdown(
                "<div style='font-size: 0.95rem; font-weight: 700; color: #1E3A8A;'>"
                "⚡ Generate Your AI Daily News Brief"
                "</div>"
                "<div style='font-size: 0.8rem; color: #64748B;'>"
                "Consolidate today's active stories across all categories into a single executive digest."
                "</div>",
                unsafe_allow_html=True,
            )
        with brief_bar2:
            brief_type_choice = st.selectbox("Format", ["Quick Brief (3 Min)", "Detailed Brief"], label_visibility="collapsed")
        with brief_bar3:
            if st.button("🚀 Generate Brief", type="primary", use_container_width=True):
                chosen_type = "quick" if "Quick" in brief_type_choice else "detailed"
                with st.spinner("NEWSMIND AI synthesizing your daily brief..."):
                    brief_data = ai_service.generate_daily_brief(articles, brief_type=chosen_type)
                    st.session_state["daily_brief"] = brief_data
                st.rerun()

    # If daily brief is present, display it
    brief = st.session_state.get("daily_brief")
    if brief:
        with st.container():
            st.markdown(
                f"""
                <div class='brief-container'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <span class='category-pill'>📅 {brief.get('brief_type')}</span>
                        <span style='font-size: 0.78rem; color: #64748B;'>Generated: {brief.get('generated_at')}</span>
                    </div>
                    <div class='brief-theme'>{brief.get('headline_theme')}</div>
                    <p style='color: #334155; font-size: 0.95rem; line-height: 1.55; margin-bottom: 16px;'>
                        {brief.get('executive_overview')}
                    </p>
                """,
                unsafe_allow_html=True,
            )

            # Key Takeaways
            takeaways = brief.get("key_takeaways", [])
            if takeaways:
                st.markdown("##### 🎯 Top Takeaways for Today")
                for t in takeaways:
                    st.markdown(f"- {t}")

            # Category breakdowns
            cat_sections = brief.get("categories", [])
            if cat_sections:
                st.markdown("##### 📂 Category Highlights & Sources")
                for sec in cat_sections:
                    with st.expander(f"📁 {sec.get('category')} ({len(sec.get('articles', []))} Stories)"):
                        for h in sec.get("highlights", []):
                            st.markdown(f"- {h}")
                        st.markdown("<div style='margin-top: 8px; font-weight: 700; font-size: 0.8rem;'>Original Sources:</div>", unsafe_allow_html=True)
                        for a in sec.get("articles", []):
                            st.markdown(f"- [{a.get('title')}]({a.get('url')}) *({a.get('source')})*")

            close_col, copy_col = st.columns([1, 1])
            with close_col:
                if st.button("Close Brief View", key="close_brief_btn"):
                    st.session_state["daily_brief"] = None
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# View: Dashboard
# -----------------------------------------------------------------------------
def render_dashboard_view():
    """Renders the main dashboard."""
    active_cat = st.session_state["selected_category"]
    search_q = st.session_state["search_query"]
    country = st.session_state.get("news_country", "us")
    lang = st.session_state.get("news_lang", "en")

    # Fetch articles
    with st.spinner("Fetching news feeds..."):
        articles, is_live, status_msg = get_cached_news(active_cat, search_q, country=country, lang=lang)

    # Top Metrics
    render_summary_statistics(len(articles))

    # Daily Brief Action Banner
    render_daily_brief_section(articles)

    # Active Feed Title & Filter Controls
    title_text = "Top Stories & Breaking News" if (active_cat == "All News" and not search_q) else f"News: {active_cat}"
    if search_q:
        title_text = f"Search Results for: \"{search_q}\""

    f_col1, f_col2 = st.columns([5, 1.2])
    with f_col1:
        st.markdown(f"<h3 style='margin: 0; font-weight: 800; color: #0F172A;'>{title_text}</h3>", unsafe_allow_html=True)
    with f_col2:
        if search_q or active_cat != "All News":
            if st.button("❌ Clear Filter", use_container_width=True):
                st.session_state["search_query"] = ""
                st.session_state["selected_category"] = "All News"
                st.rerun()

    # Informative message if no live key
    if not is_live:
        st.info(f"ℹ️ {status_msg}")

    if not articles:
        st.warning(f"No news stories found matching '{search_q}'. Try searching for terms like 'AI', 'Google', or select another category.")
        return

    # Render Featured Story (Hero) if not in search mode
    if not search_q and len(articles) > 0:
        render_featured_story(articles[0])
        remaining = articles[1:]
    else:
        remaining = articles

    # Grid of Remaining Stories
    if remaining:
        st.markdown("<h4 style='color: #334155; margin: 12px 0 14px 0; font-weight: 700;'>Trending Stories & Latest Updates</h4>", unsafe_allow_html=True)
        grid_cols = st.columns(3) if len(remaining) >= 3 else st.columns(2)
        n_cols = len(grid_cols)

        for i, article in enumerate(remaining):
            target_col = grid_cols[i % n_cols]
            render_news_card(article, target_col)


# -----------------------------------------------------------------------------
# View: "For You" Personalized Feed
# -----------------------------------------------------------------------------
def render_for_you_view():
    """Renders a customized feed prioritized by user selected preferences."""
    st.markdown("<h2 style='font-weight: 800; color: #0F172A;'>✨ For You — Personalized Feed</h2>", unsafe_allow_html=True)
    st.caption("Curated stories matching your preferred topics configured in Settings.")

    preferred = st.session_state.get("preferred_topics", [])
    if not preferred:
        st.info("You haven't selected any preferred topics yet. Visit Settings to customize your feed!")
        if st.button("Go to Settings"):
            st.session_state["current_page"] = "Settings"
            st.rerun()
        return

    st.markdown(f"**Your Active Topics:** " + " • ".join([f"`{t}`" for t in preferred]))

    with st.spinner("Curating your personalized stories..."):
        all_articles, _, _ = get_cached_news("All News", "")
        # Filter matching preferred topics
        matching = []
        for a in all_articles:
            text = f"{a.get('title', '')} {a.get('description', '')} {a.get('category', '')}".lower()
            if any(p.lower().split()[0] in text for p in preferred):
                matching.append(a)

        if not matching:
            matching = all_articles[:6]

    render_summary_statistics(len(matching))

    grid = st.columns(3)
    for i, a in enumerate(matching):
        render_news_card(a, grid[i % 3])


# -----------------------------------------------------------------------------
# View: Ask NEWSMIND AI (Assistant)
# -----------------------------------------------------------------------------
def render_assistant_view():
    """Renders the conversational AI News Assistant."""
    st.markdown("<h2 style='font-weight: 800; color: #0F172A; margin-bottom: 2px;'>🤖 Ask NEWSMIND AI</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #475569; margin-bottom: 16px;'>Ask questions about current events, compare stories, or request simple explanations using active news feeds.</p>", unsafe_allow_html=True)

    available_articles, _, _ = get_cached_news(
        st.session_state["selected_category"],
        "",
        country=st.session_state.get("news_country", "us"),
        lang=st.session_state.get("news_lang", "en"),
    )

    # Suggested Prompts
    st.markdown("<div style='font-size: 0.84rem; font-weight: 700; color: #475569; margin-bottom: 8px;'>💡 Suggested Questions:</div>", unsafe_allow_html=True)
    p_cols = st.columns(3)

    suggested = [
        "What are today's top technology stories?",
        "Summarize the latest AI developments.",
        "Explain this news in simple words.",
        "What are the important business headlines?",
        "Compare two news articles.",
        "What is happening in Indian technology?",
        "Why is this story important?",
    ]

    selected_query = None
    for i, prompt in enumerate(suggested[:6]):
        col_idx = i % 3
        if p_cols[col_idx].button(prompt, key=f"sugg_prompt_{i}", use_container_width=True):
            selected_query = prompt

    st.markdown("<hr style='margin: 16px 0;'>", unsafe_allow_html=True)

    # Chat history
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            cited = msg.get("cited_articles", [])
            if cited:
                st.markdown("<div style='margin-top: 8px; font-size: 0.8rem; font-weight: 700; color: #1E40AF;'>Supporting Sources:</div>", unsafe_allow_html=True)
                for c in cited:
                    st.markdown(f"- [{c.get('title')}]({c.get('url')}) *({c.get('source')})*")

    # Chat Input
    user_input = st.chat_input("Ask a question about today's news...") or selected_query

    if user_input:
        st.session_state["chat_messages"].append({"role": "user", "content": user_input, "cited_articles": []})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("NEWSMIND AI analyzing active stories to answer..."):
                response_data = ai_service.ask_news_agent(
                    user_input,
                    available_articles,
                    chat_history=st.session_state["chat_messages"][:-1],
                )
                answer = response_data.get("answer", "No response generated.")
                cited = response_data.get("cited_articles", [])

                st.markdown(answer)
                if cited:
                    st.markdown("<div style='margin-top: 8px; font-size: 0.8rem; font-weight: 700; color: #1E40AF;'>Supporting Sources:</div>", unsafe_allow_html=True)
                    for c in cited:
                        st.markdown(f"- [{c.get('title')}]({c.get('url')}) *({c.get('source')})*")

        st.session_state["chat_messages"].append({
            "role": "assistant",
            "content": answer,
            "cited_articles": cited,
        })

    # Clear chat
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    if st.button("🧹 Clear Chat History"):
        st.session_state["chat_messages"] = [
            {
                "role": "assistant",
                "content": "👋 Chat reset. What news would you like to explore?",
                "cited_articles": [],
            }
        ]
        st.rerun()


# -----------------------------------------------------------------------------
# View: Saved Articles
# -----------------------------------------------------------------------------
def render_saved_view():
    """Renders bookmarked articles from SQLite database."""
    st.markdown("<h2 style='font-weight: 800; color: #0F172A; margin-bottom: 2px;'>🔖 Saved Articles</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #475569; margin-bottom: 18px;'>Your bookmarked articles and AI summaries, stored persistently in local SQLite database.</p>", unsafe_allow_html=True)

    saved_list = db.get_saved_articles()

    if not saved_list:
        st.info("No saved articles yet. Click the 'Save' button on any news card to bookmark it here!")
        if st.button("Explore Dashboard"):
            st.session_state["current_page"] = "Dashboard"
            st.session_state["selected_category"] = "All News"
            st.rerun()
        return

    st.markdown(f"**Total Bookmarked Articles:** {len(saved_list)}")

    grid_cols = st.columns(2)
    for idx, article in enumerate(saved_list):
        target_col = grid_cols[idx % 2]
        render_news_card(article, target_col)


# -----------------------------------------------------------------------------
# View: Settings & Personalization
# -----------------------------------------------------------------------------
def render_settings_view():
    """Renders Settings, Personalization preferences, and API status."""
    st.markdown("<h2 style='font-weight: 800; color: #0F172A; margin-bottom: 2px;'>⚙️ Settings & Feed Personalization</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #475569; margin-bottom: 20px;'>Configure your feed topics, regional edition, and API keys.</p>", unsafe_allow_html=True)

    # 1. Personalization Section
    with st.container(border=True):
        st.markdown("### 🎨 Customize My Feed")
        st.caption("Select topics to prioritize in your personalized 'For You' news feed:")

        all_topics = [
            "AI and Technology",
            "Business and Finance",
            "Indian News",
            "World Politics",
            "Sports",
            "Science",
            "Health",
            "Entertainment",
        ]
        chosen_topics = st.multiselect(
            "Preferred Topics",
            options=all_topics,
            default=st.session_state.get("preferred_topics", ["AI and Technology", "Business and Finance"]),
        )
        if st.button("💾 Save Feed Preferences"):
            st.session_state["preferred_topics"] = chosen_topics
            st.toast("Feed preferences updated!", icon="✅")

    # 2. Regional Preferences
    with st.container(border=True):
        st.markdown("### 🌍 News Region & Language")
        c1, c2 = st.columns(2)

        with c1:
            countries = {
                "us": "United States (US)",
                "in": "India (IN)",
                "gb": "United Kingdom (GB)",
                "ca": "Canada (CA)",
                "au": "Australia (AU)",
            }
            cur_country = st.session_state.get("news_country", "us")
            sel_country = st.selectbox(
                "News Country / Edition",
                options=list(countries.keys()),
                format_func=lambda x: countries[x],
                index=list(countries.keys()).index(cur_country) if cur_country in countries else 0,
            )
            if sel_country != cur_country:
                st.session_state["news_country"] = sel_country
                trigger_refresh()

        with c2:
            st.selectbox("Language", ["English (en)"], index=0)

    # 3. API Status & Keys
    with st.container(border=True):
        st.markdown("### 🔑 API Connection Status")

        is_live, provider_name, news_msg = news_service.check_api_status()
        openai_live, openai_msg = ai_service.check_openai_api_status()

        st.markdown(f"**News Provider:** {'🟢 Live Active' if is_live else '🟡 Curated Feed'} ({provider_name})")
        st.caption(news_msg)

        st.markdown(f"**OpenAI Status:** {'🟢 Active' if openai_live else '🟡 Offline Mode'}")
        st.caption(openai_msg)

        st.markdown("---")
        st.markdown("#### Configure Keys for Current Session")
        st.caption("Keys are stored securely in environment memory and are never exposed.")

        kc1, kc2 = st.columns(2)
        with kc1:
            in_gnews = st.text_input("GNews Key (gnews.io)", type="password", key="set_gnews_key")
            in_newsapi = st.text_input("NewsAPI Key (newsapi.org)", type="password", key="set_newsapi_key")
        with kc2:
            in_openai = st.text_input("OpenAI Key (platform.openai.com)", type="password", key="set_openai_key")

        if st.button("💾 Save Session Keys", type="primary"):
            if in_gnews:
                os.environ["GNEWS_API_KEY"] = in_gnews
            if in_newsapi:
                os.environ["NEWS_API_KEY"] = in_newsapi
            if in_openai:
                os.environ["OPENAI_API_KEY"] = in_openai
            st.toast("Session keys updated!", icon="🔑")
            trigger_refresh()
            st.rerun()

    # 4. Cache Clearing
    with st.container(border=True):
        st.markdown("### 🗄️ Application Cache")
        st.caption("Streamlit caches articles for 5 minutes to conserve external API quotas.")
        if st.button("🧹 Clear All Cached Feeds"):
            st.cache_data.clear()
            st.toast("Application cache cleared!", icon="🧹")


# -----------------------------------------------------------------------------
# View: About Section
# -----------------------------------------------------------------------------
def render_about_view():
    """Renders the About section."""
    st.markdown("<h2 style='font-weight: 800; color: #0F172A;'>ℹ️ About NEWSMIND AI</h2>", unsafe_allow_html=True)
    st.markdown(
        """
        **NEWSMIND AI** is an AI-powered news platform that helps people understand current events 
        quickly by summarizing lengthy articles, organizing news by topic, and answering questions about retrieved news.
        """
    )

    with st.container(border=True):
        st.markdown("### 🎯 Problem & Solution")
        st.markdown(
            """
            - **Problem:** People struggle to keep up with lengthy news articles and daily information overload across fragmented sources.
            - **Solution:** NEWSMIND AI transforms available news articles into short summaries, key takeaways, and category-based feeds with grounded conversational exploration.
            """
        )

    with st.container(border=True):
        st.markdown("### 🚀 Technology Stack")
        st.markdown(
            """
            - **Frontend:** Streamlit 1.49+ (Modern SaaS UI, responsive layout, custom theme)
            - **Backend:** Python 3.12 (Modular architecture, helpers, caching)
            - **AI Summarization:** OpenAI API (GPT-4o-mini structured JSON synthesis)
            - **Live News Ingestion:** GNews API & NewsAPI (Multi-provider failover)
            - **Persistent Storage:** SQLite 3 (Bookmarks & summaries)
            """
        )


# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------
def render_sidebar():
    """Renders the sidebar navigation with exact sections and active indicators."""
    with st.sidebar:
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=54)

        st.markdown("<h3 style='margin: 0; font-size: 1.22rem; font-weight: 800;'>NEWSMIND AI</h3>", unsafe_allow_html=True)
        st.caption("Your World. Summarized.")

        st.markdown("<hr style='margin: 10px 0 14px 0;'>", unsafe_allow_html=True)

        # Navigation Options
        nav_items = [
            "📊 Dashboard",
            "✨ For You",
            "📰 Latest News",
            "💻 Technology",
            "🏛️ Politics",
            "📈 Business",
            "⚽ Sports",
            "🏥 Health",
            "🔬 Science",
            "🎬 Entertainment",
            "🤖 Ask NEWSMIND AI",
            f"🔖 Saved Articles ({len(st.session_state['saved_ids'])})",
            "⚙️ Settings",
            "ℹ️ About",
        ]

        cur_page = st.session_state["current_page"]
        cur_cat = st.session_state["selected_category"]

        cur_idx = 0
        if cur_page == "Dashboard" and cur_cat == "All News":
            cur_idx = 0
        elif cur_page == "For You":
            cur_idx = 1
        elif cur_page == "Dashboard" and cur_cat != "All News":
            cat_map = {
                "Technology": 3,
                "Politics": 4,
                "Business": 5,
                "Sports": 6,
                "Health": 7,
                "Science": 8,
                "Entertainment": 9,
            }
            cur_idx = cat_map.get(cur_cat, 0)
        elif cur_page == "Ask NEWSMIND AI":
            cur_idx = 10
        elif cur_page == "Saved Articles":
            cur_idx = 11
        elif cur_page == "Settings":
            cur_idx = 12
        elif cur_page == "About":
            cur_idx = 13

        selected_nav = st.radio("Navigation", nav_items, index=cur_idx, label_visibility="collapsed")

        # Routing
        if "Dashboard" in selected_nav:
            st.session_state["current_page"] = "Dashboard"
            st.session_state["selected_category"] = "All News"
        elif "For You" in selected_nav:
            st.session_state["current_page"] = "For You"
        elif "Latest News" in selected_nav:
            st.session_state["current_page"] = "Dashboard"
            st.session_state["selected_category"] = "All News"
        elif "Technology" in selected_nav:
            st.session_state["current_page"] = "Dashboard"
            st.session_state["selected_category"] = "Technology"
        elif "Politics" in selected_nav:
            st.session_state["current_page"] = "Dashboard"
            st.session_state["selected_category"] = "Politics"
        elif "Business" in selected_nav:
            st.session_state["current_page"] = "Dashboard"
            st.session_state["selected_category"] = "Business"
        elif "Sports" in selected_nav:
            st.session_state["current_page"] = "Dashboard"
            st.session_state["selected_category"] = "Sports"
        elif "Health" in selected_nav:
            st.session_state["current_page"] = "Dashboard"
            st.session_state["selected_category"] = "Health"
        elif "Science" in selected_nav:
            st.session_state["current_page"] = "Dashboard"
            st.session_state["selected_category"] = "Science"
        elif "Entertainment" in selected_nav:
            st.session_state["current_page"] = "Dashboard"
            st.session_state["selected_category"] = "Entertainment"
        elif "Ask NEWSMIND" in selected_nav:
            st.session_state["current_page"] = "Ask NEWSMIND AI"
        elif "Saved" in selected_nav:
            st.session_state["current_page"] = "Saved Articles"
        elif "Settings" in selected_nav:
            st.session_state["current_page"] = "Settings"
        elif "About" in selected_nav:
            st.session_state["current_page"] = "About"

        st.markdown("<hr style='margin: 14px 0 10px 0;'>", unsafe_allow_html=True)

        # Connection Status
        is_live, provider_name, _ = news_service.check_api_status()
        if is_live:
            st.markdown(f"<div class='status-pill-green'>🟢 {provider_name} Live</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='status-pill-yellow'>🟡 {provider_name}</div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Main Application Router
# -----------------------------------------------------------------------------
def main():
    """Main routing and execution flow."""
    render_sidebar()
    render_header()
    render_search_suggestions()

    page = st.session_state["current_page"]

    if page == "Dashboard":
        render_dashboard_view()
    elif page == "For You":
        render_for_you_view()
    elif page == "Ask NEWSMIND AI":
        render_assistant_view()
    elif page == "Saved Articles":
        render_saved_view()
    elif page == "Settings":
        render_settings_view()
    elif page == "About":
        render_about_view()
    else:
        render_dashboard_view()


if __name__ == "__main__":
    main()
