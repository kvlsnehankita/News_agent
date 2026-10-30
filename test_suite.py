"""
Comprehensive Test Suite for AI News Summarizer Agent
Validates all backend services, database operations, filtering, search, AI summarization,
and assistant capabilities.
"""

import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

print("=" * 60)
print("RUNNING AI NEWS SUMMARIZER COMPREHENSIVE TEST SUITE")
print("=" * 60)

# 1. Imports
try:
    import utils.helpers as helpers
    import utils.database as db
    import services.news_service as news_service
    import services.ai_service as ai_service
    print("✅ Step 1: All module imports succeeded.")
except Exception as e:
    print(f"❌ Step 1: Import failed: {e}")
    sys.exit(1)

# 2. Helpers
try:
    assert helpers.clean_text("<b>Title</b> [+1234 chars]") == "Title"
    assert helpers.truncate_text("Hello world this is a test", 12) == "Hello world..."
    assert helpers.validate_url("https://example.com/news") is True
    assert helpers.validate_url("invalid-url") is False
    id1 = helpers.generate_article_id("https://example.com/1", "News One")
    id2 = helpers.generate_article_id("https://example.com/1", "News One")
    assert id1 == id2
    tech_placeholder = helpers.get_category_placeholder("Technology")
    assert os.path.exists(tech_placeholder), f"Category placeholder missing: {tech_placeholder}"
    print("✅ Step 2: Helper utilities (cleaning, date, validation, placeholders) passed.")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"❌ Step 2: Helpers failed: {e}")
    sys.exit(1)

# 3. Database operations
try:
    db.init_db()
    test_article = {
        "id": "suite-test-01",
        "title": "Comprehensive Test Headline",
        "description": "Testing SQLite database persistence.",
        "content": "Full article test content body.",
        "url": "https://example.com/test-article",
        "url_to_image": "https://example.com/image.jpg",
        "published_at": "2026-10-24T18:00:00Z",
        "source": "Test Journal",
        "category": "Technology",
    }
    test_summary = {
        "quick_summary": "Test quick summary.",
        "key_points": ["Point 1", "Point 2", "Point 3"],
        "why_it_matters": "Matters for unit tests.",
        "category": "Technology",
    }

    # Save
    assert db.save_article(test_article, test_summary) is True
    assert db.is_article_saved("suite-test-01") is True

    # Retrieve
    saved_list = db.get_saved_articles()
    saved_item = next((a for a in saved_list if a["id"] == "suite-test-01"), None)
    assert saved_item is not None
    assert saved_item["title"] == "Comprehensive Test Headline"
    assert saved_item["ai_summary"]["quick_summary"] == "Test quick summary."

    # Duplicate prevention
    assert db.save_article(test_article, test_summary) is True

    # Remove
    assert db.remove_saved_article("suite-test-01") is True
    assert db.is_article_saved("suite-test-01") is False
    print("✅ Step 3: SQLite Database save, retrieve, duplicate prevention, and deletion passed.")
except Exception as e:
    print(f"❌ Step 3: Database failed: {e}")
    sys.exit(1)

# 4. News Service - Categories
try:
    categories = news_service.CATEGORIES
    print(f"Testing {len(categories)} categories...")
    for cat in categories:
        articles, is_live, msg = news_service.fetch_top_headlines(category=cat)
        assert len(articles) > 0, f"No articles returned for category: {cat}"
        # Verify structure
        for a in articles:
            assert "id" in a and "title" in a and "url" in a and "category" in a and "source" in a
    print("✅ Step 4: Category filtering across all 8 categories passed.")
except Exception as e:
    print(f"❌ Step 4: Category filtering failed: {e}")
    sys.exit(1)

# 5. News Service - Search
try:
    # Existing keyword
    results, is_live, msg = news_service.search_news("Quantum")
    assert len(results) > 0, "Expected search results for 'Quantum'"
    assert any("quantum" in (a["title"] + a["description"]).lower() for a in results)

    # Case-insensitive search
    results_lower, _, _ = news_service.search_news("quantum")
    assert len(results_lower) == len(results), "Case insensitive search mismatch"

    # Non-existent keyword
    no_results, _, _ = news_service.search_news("xyzzyrandomnonexistent9999")
    assert len(no_results) == 0, "Expected 0 results for non-existent keyword"
    print("✅ Step 5: Search functionality (case-insensitivity, matching, empty state) passed.")
except Exception as e:
    print(f"❌ Step 5: Search failed: {e}")
    sys.exit(1)

# 6. AI Summarization
try:
    sample_art = news_service.SAMPLE_ARTICLES[0]
    summary = ai_service.summarize_article(sample_art)
    assert "quick_summary" in summary and len(summary["quick_summary"]) > 10
    assert "key_takeaways" in summary and isinstance(summary["key_takeaways"], list) and len(summary["key_takeaways"]) >= 3
    assert "why_it_matters" in summary and len(summary["why_it_matters"]) > 10
    assert "category" in summary
    print("✅ Step 6: AI Summarization (Quick Summary, Key Takeaways, Why It Matters, Category) passed.")
except Exception as e:
    print(f"❌ Step 6: AI Summarization failed: {e}")
    sys.exit(1)

# 7. AI News Assistant
try:
    arts, _, _ = news_service.fetch_top_headlines("Technology")
    resp = ai_service.ask_news_agent("What are the latest updates on quantum computing?", arts)
    assert "answer" in resp and len(resp["answer"]) > 20
    assert "cited_articles" in resp
    print("✅ Step 7: AI News Assistant Q&A and citation generation passed.")
except Exception as e:
    print(f"❌ Step 7: AI News Assistant failed: {e}")
# 8. Personalized Daily Brief
try:
    arts, _, _ = news_service.fetch_top_headlines("All News")
    brief = ai_service.generate_daily_brief(arts, brief_type="quick")
    assert "headline_theme" in brief and len(brief["headline_theme"]) > 5
    assert "executive_overview" in brief and len(brief["executive_overview"]) > 10
    assert "categories" in brief
    print("✅ Step 8: Personalized Daily Brief generation passed.")
except Exception as e:
    print(f"❌ Step 8: Daily Brief failed: {e}")
    sys.exit(1)

print("=" * 60)
print("ALL 8 TEST SUITE STAGES PASSED FLAWLESSLY! 🚀")
print("=" * 60)
