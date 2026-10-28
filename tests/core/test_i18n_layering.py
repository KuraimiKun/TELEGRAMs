from pathlib import Path

from core.i18n import Translator


def test_translator_with_bot_layering():
    bot_locales = Path("bots/socialdownload/locales")
    translator = Translator(bot_locales_dir=bot_locales)

    # English resolution
    en_welcome = translator.get("en", "start-welcome", name="Alice")
    assert "Alice" in en_welcome
    assert "TikTok" in en_welcome

    # Arabic resolution
    ar_welcome = translator.get("ar", "start-welcome", name="أحمد")
    assert "أحمد" in ar_welcome
    assert "تيك توك" in ar_welcome

    # Russian resolution
    ru_welcome = translator.get("ru", "start-welcome", name="Иван")
    assert "Иван" in ru_welcome
    assert "TikTok" in ru_welcome

    # Spanish resolution
    es_welcome = translator.get("es", "start-welcome", name="Carlos")
    assert "Carlos" in es_welcome
    assert "TikTok" in es_welcome

    # Core base key resolution
    core_saved = translator.get("en", "saved")
    assert "Saved" in core_saved

    # Fallback to key itself for non-existent key
    assert translator.get("ar", "non-existent-key") == "non-existent-key"


def test_numbers_are_not_locale_grouped():
    from core.i18n import Translator

    t = Translator()
    assert "Payments of 123456789" in t.get("en", "adm-payments", id=123456789)
    assert "2160p" in t.get("en", "dl-quality-locked", quality=2160) or "2160" in t.get("en", "vip-plan-days", days=2160)


def test_long_external_text_is_preserved_without_interpreting_fluent_or_html():
    translator=Translator(Path('bots/groupguard/locales'))
    external=('&lt;unsafe&gt; { $not_a_variable } '+'😀')*180
    result=translator.get('en','gg-fed-stat',user='42',rows=external)
    assert external in result and 'gg-fed-stat' not in result
    assert '\ue000' not in result and '\ue001' not in result
    assert '{ $not_a_variable }' in result


def test_external_text_and_result_expansion_stay_bounded(tmp_path):
    import pytest

    from core.i18n import Translator
    locale=tmp_path/'en'
    locale.mkdir()
    (locale/'messages.ftl').write_text('repeat = { $text } { $text } { $text }\n')
    translator=Translator(tmp_path)
    with pytest.raises(ValueError,match='argument_too_long'):
        translator.get('en','repeat',text='a'*65537)
    with pytest.raises(ValueError,match='result_too_long'):
        translator.get('en','repeat',text='a'*50000)


def test_numeric_plural_branches_keep_ids_literal_and_string_selectors_work(tmp_path):
    patterns={
        'en': [('one','one warning'),('other','many warnings')],
        'ru': [('one','одно предупреждение'),('few','несколько предупреждений'),('many','много предупреждений'),('other','дробное число')],
        'ar': [('zero','لا إنذارات'),('one','إنذار واحد'),('two','إنذاران'),('few','إنذارات قليلة'),('many','إنذارات عديدة'),('other','إنذارات')],
    }
    for code,branches in patterns.items():
        folder=tmp_path/code
        folder.mkdir()
        cases='\n'.join(('   *' if name=='other' else '    ')+f'[{name}] {text}' for name,text in branches)
        (folder/'messages.ftl').write_text('plural = { $count ->\n'+cases+'\n    }\n'
            '    ID: { $id }\n'
            'mode = { $mode ->\n    [on] enabled\n   *[other] disabled\n    }\n'
            'number = { NUMBER($count, useGrouping: 0) }\n')
    translator=Translator(tmp_path)
    examples={'en':{1:'one warning',2:'many warnings'},
        'ru':{1:'одно',2:'несколько',5:'много',1.5:'дробное'},
        'ar':{0:'لا إنذارات',1:'واحد',2:'إنذاران',3:'قليلة',11:'عديدة',100:'إنذارات'}}
    for code,cases in examples.items():
        for count,expected in cases.items():
            result=translator.get(code,'plural',count=count,id=123456789)
            assert expected in result
            assert 'ID: 123456789' in result
        assert translator.get(code,'mode',mode='on')=='enabled'
        assert translator.get(code,'mode',mode='off')=='disabled'
    assert translator.get('en','number',count=1234)=='1234'


def test_published_native_script_and_region_aliases_preserve_legacy_fallbacks():
    groupguard=Translator(Path('bots/groupguard/locales'))
    for supplied,expected in {'tl-PH':'fil','fil-PH':'fil','ml_IN':'ml-in','ta-IN':'ta',
            'zh-Hant-TW':'zh-tw','zh-Hans-CN':'zh-cn','pt-BR-x-test':'pt-br',
            'be-BY':'be','uk-UA':'uk','ms-MY':'ms'}.items():
        assert groupguard.resolve(supplied)==expected
        assert groupguard.bind(supplied)('gg-help-family-title-portability')==groupguard.get(expected,'gg-help-family-title-portability')
    platform=Translator()
    assert platform.resolve('be-BY')=='ru' and platform.resolve('uk-UA')=='ru'
    assert platform.resolve('tl-PH')=='en'


def test_cached_locale_sources_keep_bundle_args_isolated_and_reload_changed_files(tmp_path):
    from core.i18n import _resource

    folder=tmp_path/'en'
    folder.mkdir()
    path=folder/'messages.ftl'
    path.write_text('own = First { $name }\n')
    one=Translator(tmp_path)
    hits=_resource.cache_info().hits
    two=Translator(tmp_path)
    assert _resource.cache_info().hits>hits
    assert one.get('en','own',name='Alice')=='First Alice'
    assert two.get('en','own',name='Bob')=='First Bob'
    assert one.get('en','own',name='Carol')=='First Carol'
    path.write_text('own = Changed source { $name }\n')
    three=Translator(tmp_path)
    assert three.get('en','own',name='Diana')=='Changed source Diana'
    assert one.get('en','own',name='Alice')=='First Alice'
