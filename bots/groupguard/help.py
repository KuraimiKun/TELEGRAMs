"""Bounded, searchable discovery from the same command registry used by the pipeline."""
from __future__ import annotations

import re
from html import escape

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bots.groupguard.command_metadata import REGISTRY
from core.i18n import Translate

FAMILIES=tuple(dict.fromkeys(item.module for item in REGISTRY.values()))
PAGE=12


def render(t: Translate, query: str = '', page: int = 0) -> tuple[str,InlineKeyboardMarkup]:
    words=query.lower().strip().lstrip('/')
    if words in FAMILIES:
        names=[item.name for item in REGISTRY.values() if item.module==words]
        heading=t('gg-help-family-'+words)
    elif words:
        names=[item.name for item in REGISTRY.values() if words in item.name or words in item.module]
        heading=t('gg-help-search',query=escape(words[:64]))
    else:
        names=[]
        heading=t('gg-help-index')
    page=max(0,min(page,max(0,(len(names)-1)//PAGE)))
    shown=names[page*PAGE:(page+1)*PAGE]
    rows=[]
    for name in shown:
        item=REGISTRY[name]
        detail=t('gg-help-unsupported') if item.unsupported else t('gg-help-group-only') if not item.pm else t('gg-help-connected')
        if item.canonical!=name:
            detail+=' · /'+item.canonical
        rows.append('/'+name+' — '+detail)
    # Family names are stable machine query values; the descriptions are localized.
    if not words:
        rows=[t('gg-help-family-title-'+family)+' · /help '+family for family in FAMILIES]
    text=heading+'\n\n'+'\n'.join(rows)
    keyboard=[]
    safe_query=re.fullmatch(r'[a-z0-9_]{0,32}',words) is not None
    if page and safe_query:
        keyboard.append(InlineKeyboardButton(text=t('gg-help-previous'),callback_data=f'gg_h:{page-1}:{words}'))
    if (page+1)*PAGE<len(names) and safe_query:
        keyboard.append(InlineKeyboardButton(text=t('gg-help-next'),callback_data=f'gg_h:{page+1}:{words}'))
    return text,InlineKeyboardMarkup(inline_keyboard=[keyboard] if keyboard else [])
