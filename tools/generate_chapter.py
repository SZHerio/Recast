# Универсальный генератор главы книги заданий из JSON-спецификации.
# Один источник правды даёт SNBT, оба языка, авторский источник и stable_ids,
# поэтому паритет ключей не может разойтись вручную.
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
ROOT = r'C:\Users\SZHerio\curseforge\minecraft\Instances\main1.20'
NS = 'industrial_frontier.quest'


def build(spec_path):
    with io.open(spec_path, encoding='utf-8') as handle:
        spec = json.load(handle)

    key, cid, group = spec['key'], spec['chapter_id'], spec['group_id']
    quests = spec['quests']
    ru, en, stable = {}, {}, {}

    if spec.get('group_key'):
        ru[f'{NS}.group.{spec["group_key"]}'] = spec['group_ru']
        en[f'{NS}.group.{spec["group_key"]}'] = spec['group_en']
        stable[f'if.group.{spec["group_key"]}'] = group

    ru[f'{NS}.chapter.{key}.title'] = spec['title_ru']
    en[f'{NS}.chapter.{key}.title'] = spec['title_en']
    ru[f'{NS}.chapter.{key}.subtitle'] = spec['sub_ru']
    en[f'{NS}.chapter.{key}.subtitle'] = spec['sub_en']
    stable[f'if.chapter.{key}'] = cid

    ids = {q['slug']: '3' + cid[1:4] + f'{i:012d}' for i, q in enumerate(quests, 1)}
    out = ['{', '\tdefault_hide_dependency_lines: false', '\tdefault_quest_shape: "square"',
           f'\tfilename: "{spec["file"]}"', f'\tgroup: "{group}"', f'\ticon: "{spec["icon"]}"',
           f'\tid: "{cid}"', f'\torder_index: {spec.get("order", 0)}', '\tquest_links: [ ]', '\tquests: [']
    source = []

    for index, quest in enumerate(quests, 1):
        qid = ids[quest['slug']]
        tid = '4' + cid[1:4] + f'{index:012d}'
        rid = '5' + cid[1:4] + f'{index:012d}'
        base = f'{NS}.{key}.{quest["slug"]}'
        ru[f'{base}.title'] = quest['ru']['title']
        en[f'{base}.title'] = quest['en']['title']
        ru[f'{base}.subtitle'] = quest['ru']['subtitle']
        en[f'{base}.subtitle'] = quest['en']['subtitle']
        for j, line in enumerate(quest['ru']['desc'], 1):
            ru[f'{base}.desc.{j}'] = line
        for j, line in enumerate(quest['en']['desc'], 1):
            en[f'{base}.desc.{j}'] = line
        ru[f'{base}.task'] = quest['ru']['task']
        en[f'{base}.task'] = quest['en']['task']
        stable[f'if.quest.{key}.{quest["slug"]}'] = qid
        stable[f'if.task.{key}.{quest["slug"]}'] = tid
        stable[f'if.reward.{key}.{quest["slug"]}'] = rid

        out.append('\t\t{')
        deps = quest.get('deps') or []
        if len(deps) == 1:
            out.append(f'\t\t\tdependencies: ["{ids[deps[0]]}"]')
        elif len(deps) > 1:
            out.append('\t\t\tdependencies: [')
            for dep in deps:
                out.append(f'\t\t\t\t"{ids[dep]}"')
            out.append('\t\t\t]')
        out.append('\t\t\tdescription: [')
        for j in range(1, len(quest['ru']['desc']) + 1):
            out.append(f'\t\t\t\t"{{{base}.desc.{j}}}"')
        out.append('\t\t\t]')
        out.append(f'\t\t\ticon: "{quest["icon"]}"')
        out.append(f'\t\t\tid: "{qid}"')
        if spec.get('optional'):
            out.append('\t\t\toptional: true')
        out += ['\t\t\trewards: [{', f'\t\t\t\tid: "{rid}"', '\t\t\t\ttype: "xp"',
                f'\t\t\t\txp: {spec.get("xp", 25)}', '\t\t\t}]']
        if quest.get('shape'):
            out.append(f'\t\t\tshape: "{quest["shape"]}"')
        if quest.get('size'):
            out.append(f'\t\t\tsize: {quest["size"]}d')
        out.append(f'\t\t\tsubtitle: "{{{base}.subtitle}}"')
        out.append(f'\t\t\ttags: ["{spec["tag"]}"]')
        # Задача по умолчанию — отметка. Предметная задача обнаруживает предмет
        # в инвентаре и не забирает его: правило сборки — квест не поглощает
        # произведённое. Порядок ключей SNBT совпадает с уже собранными главами.
        item = quest.get('item')
        out.append('\t\t\ttasks: [{')
        out.append(f'\t\t\t\tid: "{tid}"')
        if item:
            out += ['\t\t\t\titem: {', f'\t\t\t\t\tCount: {quest.get("count", 1)}',
                    f'\t\t\t\t\tid: "{item}"', '\t\t\t\t}']
        out.append(f'\t\t\t\ttitle: "{{{base}.task}}"')
        out.append(f'\t\t\t\ttype: "{"item" if item else "checkmark"}"')
        out.append('\t\t\t}]')
        out.append(f'\t\t\ttitle: "{{{base}.title}}"')
        out.append(f'\t\t\tx: {float(quest["x"])}d')
        out.append(f'\t\t\ty: {float(quest["y"])}d')
        out.append('\t\t}')
        source.append({'alias': f'if.quest.{key}.{quest["slug"]}', 'engine_id': qid,
                       'purpose': quest['en']['subtitle'],
                       'task_kind': 'item' if item else 'checkmark',
                       'grind_class': 'GREEN' if item else 'NONE'})

    out.append('\t]')
    out.append(f'\tsubtitle: ["{{{NS}.chapter.{key}.subtitle}}"]')
    out.append(f'\ttitle: "{{{NS}.chapter.{key}.title}}"')
    out.append('}')

    io.open(os.path.join(ROOT, 'config', 'ftbquests', 'quests', 'chapters', spec['file'] + '.snbt'),
            'w', encoding='utf-8', newline='\n').write('\n'.join(out) + '\n')
    io.open(os.path.join(ROOT, 'authoring', 'quests', spec['file'] + '.json'),
            'w', encoding='utf-8', newline='\n').write(json.dumps({
                'schema_version': 1, 'chapter_alias': f'if.chapter.{key}', 'engine_id': cid,
                'compiled_path': f'config/ftbquests/quests/chapters/{spec["file"]}.snbt',
                'optional': bool(spec.get('optional')), 'quests': source}, ensure_ascii=False, indent=2) + '\n')

    lang_root = os.path.join(ROOT, 'config', 'paxi', 'resourcepacks', 'IndustrialFrontier-Core',
                             'assets', 'industrial_frontier', 'lang')
    for name, added in (('ru_ru.json', ru), ('en_us.json', en)):
        path = os.path.join(lang_root, name)
        with io.open(path, encoding='utf-8-sig') as handle:
            data = json.load(handle)
        data.update(added)
        data = {k: data[k] for k in sorted(data)}
        io.open(path, 'w', encoding='utf-8', newline='\n').write(
            json.dumps(data, ensure_ascii=False, indent=2) + '\n')

    stable_path = os.path.join(ROOT, 'docs', 'registries', 'stable_ids.json')
    with io.open(stable_path, encoding='utf-8-sig') as handle:
        registry = json.load(handle)
    registry['ids'].update(stable)
    io.open(stable_path, 'w', encoding='utf-8', newline='\n').write(
        json.dumps(registry, ensure_ascii=False, indent=2) + '\n')

    assert set(ru) == set(en), 'RU/EN parity broken'
    print(f'{spec["file"]}: {len(quests)} квестов, {len(ru)} ключей')


if __name__ == '__main__':
    build(sys.argv[1])
