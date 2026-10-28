"""Normalization, boundary and adversarial contracts independent of moderation effects."""
import time

import pytest
from pydantic import ValidationError

from bots.groupguard.blocklist_matcher import literal_match, match, tokens
from bots.groupguard.blocklist_types import Entry, trigger
from bots.groupguard.chatconfig import ChatConfig
from bots.groupguard.handlers.blocklists import entry_options


@pytest.mark.parametrize('text,pattern,mode,expected', [
    ('A CAFÉ   BAR!', 'cafe bar', 'word', True),
    ('scasino casinoes', 'casino', 'word', False),
    ('casino, now', 'casino', 'word', True),
    ('casino_foo', 'casino', 'word', False),
    ('中文广告中文', '广告', 'word', False),
    ('中文 广告!', '广告', 'word', True),
    (' spam hello', 'spam', 'prefix', True),
    ('hello spam', 'spam', 'prefix', False),
    ('Spam!', 'spam', 'exact', False),
    ('  SPAM  ', 'spam', 'exact', True),
    ('cat', 'c?t', 'word', True),
    ('c t', 'c?t', 'word', False),
    ('ct', 'c*t', 'word', True),
    ('caaaaat', 'c*t', 'word', True),
    ('c a t', 'c*t', 'word', False),
    ('c a t', 'c**t', 'exact', True),
    ('catty', 'c*t', 'word', False),
    ('a?b', r'a\?b', 'word', True),
    ('axb', r'a\?b', 'word', False),
    ('a*b', r'a\*b', 'word', True),
    ('a**b', r'a\*\*b', 'exact', True),
    ('a*b', r'a\*\*b', 'exact', False),
    (r'a\b', r'a\\b', 'exact', True),
    ('σπαμ', 'ΣΠΑΜ', 'word', True),
    ('ß'*256, 'ß'*256, 'exact', True),
])
def test_normalized_wildcards_boundaries(text, pattern, mode, expected):
    assert match(text, pattern, mode) is expected


def test_hostile_patterns_are_bounded_without_backtracking():
    started = time.monotonic()
    text = 'a'*32768 + 'secret'
    for n in range(150):
        assert not match(text, '*a'*31 + 'z' + str(n))
    assert time.monotonic() - started < 8
    assert not match(text, 'secret')  # Explicit source bound, no fabricated suffix match.
    with pytest.raises(ValueError):
        tokens('?'*33)


def test_legacy_literal_phrases_and_unknown_storage_preserved():
    old = ['casino*', 'A café  bar', 'x'*500]
    cfg = ChatConfig.from_storage(dict(blocklist=old, blocklist_warn=True, opaque={'x': 1}))
    assert cfg.blocklist == old and cfg.blocklist_mode == 'warn'
    assert [Entry.model_validate(v).pattern for v in cfg.blocklist_entries] == old
    assert all(v['legacy'] for v in cfg.blocklist_entries)
    assert literal_match('casino*', old[0]) and not literal_match('casinos', old[0])
    assert cfg.model_extra['opaque'] == {'x': 1}
    assert ChatConfig.from_storage(cfg.model_dump()).model_dump() == cfg.model_dump()


@pytest.mark.parametrize('raw', ['reason {tban}', '{ban 5m}', '{sban 1h}', '{not_a_mode}', '{tmute forever}'])
def test_malformed_entry_modes_never_become_permanent(raw):
    with pytest.raises(ValueError):
        entry_options(raw)


def test_entry_overrides_config_modes_and_typed_prefixes():
    reason, action, seconds, silent = entry_options('because {stmute 5m}')
    assert (reason, action, seconds, silent) == ('because', 'tmute', 300, True)
    assert trigger('lookalike:spam').kind == 'lookalike'
    assert trigger('username:spam*').kind == 'username'
    with pytest.raises(ValidationError):
        ChatConfig(blocklist_mode='tban')
    with pytest.raises(ValidationError):
        ChatConfig(blocklist_mode='sban')
    with pytest.raises(ValidationError):
        trigger('word', action='ban', duration_seconds=300)
    with pytest.raises(ValidationError):
        trigger('?'*33)


@pytest.mark.parametrize('one,two',[('குமார்','கமர்'),('का','क'),('ガード','カード'),('เกา','กา')])
def test_essential_script_marks_do_not_collapse_distinct_words(one,two):
    assert not match(one,two,'exact')


def test_unicode_expansion_is_bounded_and_rejected_at_entry_save():
    from bots.groupguard.blocklist_matcher import MAX_TEXT, normalize
    assert len(normalize('ﷺ'))>1
    with pytest.raises(ValidationError):
        trigger('ﷺ'*256)
    assert not match('ﷺ'*MAX_TEXT+' secret','secret')


@pytest.mark.parametrize('one,two',[('का','क'),('ガ','カ'),('கி','க')])
def test_full_word_does_not_split_an_essential_mark_cluster(one,two):
    assert not match(one,two,'word')
