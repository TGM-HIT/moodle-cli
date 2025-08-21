from pathlib import Path
import json
import os

from bs4 import BeautifulSoup
import typst


def frontmatter(filename: Path):
    return json.loads(typst.query(filename, '<frontmatter>', root=os.getenv('TYPST_ROOT'), field="value", one=True))


def attachments(filename: Path):
    return json.loads(typst.query(filename, '<attachments>', root=os.getenv('TYPST_ROOT'), field="value"))


def dependencies(filename: Path):
    return json.loads(typst.query(filename, '<dependencies>', root=os.getenv('TYPST_ROOT'), field="value"))


def body(filename: Path):
    html = typst.compile(filename, root=os.getenv('TYPST_ROOT'), format='html')
    body = BeautifulSoup(html, 'html.parser').body.decode_contents()

    return body
