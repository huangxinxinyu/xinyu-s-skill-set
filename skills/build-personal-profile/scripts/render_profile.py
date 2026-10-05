#!/usr/bin/env python3
"""Render a validated profile into one offline HTML file (standard library only)."""
import argparse
import json
from pathlib import Path

CATEGORIES = {'兴趣', '工作方式', '偏好', '目标'}
STATUSES = {'已知', '待确认'}


def validate(data):
    if not isinstance(data, dict) or data.get('version') != 1:
        raise ValueError('画像必须为 version: 1 的对象')
    person = data.get('person')
    if not isinstance(person, dict) or not all(isinstance(person.get(k), str) for k in ('name', 'intro')):
        raise ValueError('person.name 和 person.intro 必须是字符串')
    if not isinstance(data.get('questions'), list) or not all(isinstance(q, str) for q in data['questions']):
        raise ValueError('questions 必须是字符串数组')
    if not isinstance(data.get('entries'), list):
        raise ValueError('entries 必须是数组')
    ids = set()
    for entry in data['entries']:
        fields = ('id', 'category', 'title', 'detail', 'status', 'evidence')
        if not isinstance(entry, dict) or not all(isinstance(entry.get(k), str) for k in fields):
            raise ValueError('每个条目必须包含字符串 id/category/title/detail/status/evidence')
        if not entry['id'].strip() or entry['id'] in ids:
            raise ValueError('条目 id 不能为空或重复')
        if not entry['title'].strip() or not entry['evidence'].strip():
            raise ValueError('标题和依据不能为空')
        if entry['category'] not in CATEGORIES or entry['status'] not in STATUSES:
            raise ValueError('分类或状态不受支持')
        ids.add(entry['id'])
    return data


def render(data):
    validate(data)
    template = (Path(__file__).resolve().parents[1] / 'assets/profile.html').read_text(encoding='utf-8')
    payload = json.dumps(data, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    return template.replace('__PROFILE_DATA__', payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--force', action='store_true', help='明确允许覆盖已有输出')
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding='utf-8'))
        result = render(data)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('w' if args.force else 'x', encoding='utf-8') as out:
            out.write(result)
    except (ValueError, OSError) as error:
        parser.exit(1, f'生成失败：{error}\n')
    print(args.output.resolve())


if __name__ == '__main__':
    main()
