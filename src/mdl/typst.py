import json
from pathlib import Path

from bs4 import BeautifulSoup
import typst


def frontmatter(filename: Path):
    return json.loads(typst.query(filename, '<frontmatter>', field="value", one=True))


def attachments(filename: Path):
    return json.loads(typst.query(filename, '<attachments>', field="value"))


def body(filename: Path):
    html = typst.compile(filename, format='html')
    body = BeautifulSoup(html, 'html.parser').body.decode_contents()

    return body
