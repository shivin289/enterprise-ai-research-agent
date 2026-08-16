import pytest

from app.ai.output_parser import safe_parse_json


def test_parses_clean_json():
    assert safe_parse_json('{"a": 1}') == {"a": 1}


def test_strips_markdown_fences():
    raw = '```json\n{"a": 1}\n```'
    assert safe_parse_json(raw) == {"a": 1}


def test_passthrough_for_already_parsed_dict():
    assert safe_parse_json({"a": 1}) == {"a": 1}


def test_extracts_json_block_from_surrounding_text():
    raw = 'Sure, here you go:\n{"a": 1}\nHope that helps!'
    assert safe_parse_json(raw) == {"a": 1}


def test_raises_on_unparseable_garbage():
    with pytest.raises(Exception):
        safe_parse_json("not json at all, sorry")
