import json
import sys

from bs4 import BeautifulSoup
from moodle import Moodle
import typst

url = 'http://localhost:8000/webservice/rest/server.php'
token = '2e884e3588b06e1c8d0b43150eff366e'

def process(filename: str):
    metadata = json.loads(typst.query(filename, '<frontmatter>', field="value", one=True))
    soup = BeautifulSoup(typst.compile(filename, format='html'), 'html.parser')

    return { **metadata, 'body': soup.body.decode_contents() }

def upload(data: dict, url: str, token: str):
    if data['mod'] != 'page':
        raise ValueError(f"Unsupported module type: {data['mod']}")
    moodle = Moodle(url, token)
    result = moodle('local_modcontentservice_update_page_content', cmid=data['cmid'], body=data['body'])
    return result

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python main.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    data = process(filename)
    result = upload(data, url, token)
    print(result)
