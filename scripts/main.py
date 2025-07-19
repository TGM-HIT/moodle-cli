import json
import sys

from bs4 import BeautifulSoup
from moodle import Moodle
import requests
import typst

base_url = 'http://localhost:8000'
url = f'{base_url}/webservice/rest/server.php'
token = '3b29d57634d4a547d48f52638b374a30'


def process(filename: str):
    metadata = json.loads(typst.query(filename, '<frontmatter>', field="value", one=True))
    soup = BeautifulSoup(typst.compile(filename, format='html'), 'html.parser')

    return metadata, soup.body.decode_contents()


def upload_page(url: str, token: str, *, cmid: int, intro: dict=None, page: dict):
    if intro is None:
        intro = dict(text='')

    moodle = Moodle(url, token)
    result = moodle('local_modcontentservice_update_page_content', cmid=cmid, intro=intro, page=page)
    return result


def upload_files(*files, itemid = 0, filepath = '/'):
    r = requests.post(
        f'{base_url}/webservice/upload.php',
        params={
            'token': token,
            'itemid': itemid,
            'filepath': filepath,
        },
        files={ f'file_{i}': file for i, file in enumerate(files, start=1) },
    )
    r.raise_for_status()
    return r.json()

if __name__ == '__main__':
    # if len(sys.argv) < 2:
    #     print("Usage: python main.py <filename>")
    #     sys.exit(1)

    # filename = sys.argv[1]
    # metadata, body = process(filename)
    # if metadata['mod'] != 'page':
    #     raise ValueError(f"Unsupported module type: {metadata['mod']}")

    # result = upload_page(url, token,
    #     cmid=metadata['cmid'],
    #     intro=dict(text=''),
    #     page=dict(text=body),
    # )
    # print(result)

    result = upload_files(
        ('super-advocado.jpg', open('/home/clemens/Pictures/super-advocado.jpg', 'rb')),
        # ('Apothecary.jpg', open('/home/clemens/Pictures/WerewolfDarkArts/cropped/Apothecary.jpg', 'rb')),
    )
    itemid = result[0]['itemid']
    # print(result)

    result = upload_page(url, token,
        cmid=2,
        # intro=dict(
        #     text='This is the intro',
        #     # format=1,
        #     # itemid=-1,
        # ),
        page=dict(
            text='<p><img class="img-fluid" src="@@PLUGINFILE@@/super-advocado.jpg" alt="advocado" width="1024" height="1024"></p>',
            # format=1,
            itemid=itemid,
        ),
    )
    print(result)
