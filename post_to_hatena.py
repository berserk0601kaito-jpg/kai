import urllib.request
import base64
import re
import sys
import os

HATENA_ID = "Kai_mental"
BLOG_ID = "kai-mental.hatenablog.com"
API_KEY = "fymp84ybsr"

def post_article(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # タイトルをfrontmatterから取得
    title_match = re.search(r'^title:\s*(.+)$', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else '無題'

    # カテゴリを取得
    cat_match = re.search(r'^category:\s*(.+)$', content, re.MULTILINE)
    category = cat_match.group(1).strip() if cat_match else 'メンタル'

    # frontmatterを除いた本文を取得
    body = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL).strip()

    # XML特殊文字をエスケープ
    def esc(s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

    xml_body = f'''<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom"
       xmlns:app="http://www.w3.org/2007/app">
  <title>{esc(title)}</title>
  <content type="text/x-markdown">{esc(body)}</content>
  <category term="{esc(category)}" />
  <app:control><app:draft>no</app:draft></app:control>
</entry>'''

    credentials = base64.b64encode(f'{HATENA_ID}:{API_KEY}'.encode()).decode()
    url = f'https://blog.hatena.ne.jp/{HATENA_ID}/{BLOG_ID}/atom/entry'

    req = urllib.request.Request(
        url,
        data=xml_body.encode('utf-8'),
        headers={
            'Content-Type': 'application/atom+xml; charset=utf-8',
            'Authorization': f'Basic {credentials}'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req) as resp:
            print(f'✅ 投稿成功: {title} (status={resp.status})')
    except Exception as e:
        print(f'❌ 投稿失敗: {title} - {e}')

if __name__ == '__main__':
    for filepath in sys.argv[1:]:
        if os.path.exists(filepath):
            post_article(filepath)
        else:
            print(f'ファイルが見つかりません: {filepath}')
