import pytest
from radar.content import ContentManager

def test_content_manager_init():
    mgr = ContentManager()
    assert "viral" in mgr.presets
    assert "gaming" in mgr.presets

def test_get_hashtags_by_key():
    mgr = ContentManager()
    tags = mgr.get_hashtags(["tech"])
    assert "#tech" in tags
    assert "#coding" in tags

def test_get_hashtags_by_index():
    mgr = ContentManager()
    # "viral" is the first key
    tags = mgr.get_hashtags(["1"])
    assert "#fyp" in tags
    assert "#viral" in tags

def test_get_hashtags_combined():
    mgr = ContentManager()
    tags = mgr.get_hashtags(["tech", "funny"])
    assert "#tech" in tags
    assert "#funny" in tags

def test_prepare_caption():
    mgr = ContentManager()
    caption = mgr.prepare_caption("Check this out", ["viral"])
    assert caption.startswith("Check this out")
    assert "#fyp" in caption

def test_prepare_caption_no_categories():
    mgr = ContentManager()
    caption = mgr.prepare_caption("Just text")
    assert caption == "Just text"

def test_get_hashtags_invalid_key():
    mgr = ContentManager()
    tags = mgr.get_hashtags(["nonexistent"])
    assert tags == ""

def test_get_hashtags_invalid_index():
    mgr = ContentManager()
    tags = mgr.get_hashtags(["999"])
    assert tags == ""
