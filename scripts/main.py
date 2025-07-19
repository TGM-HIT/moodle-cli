import json
import sys

from bs4 import BeautifulSoup
from .moodle import Moodle
import requests
import typst

base_url = 'http://localhost:8000'
url = f'{base_url}/webservice/rest/server.php'
token = '3b29d57634d4a547d48f52638b374a30'

moodle = Moodle(url, token)


def process(filename: str):
    metadata = json.loads(typst.query(filename, '<frontmatter>', field="value", one=True))
    soup = BeautifulSoup(typst.compile(filename, format='html'), 'html.parser')

    return metadata, soup.body.decode_contents()

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

    # result = moodle.upload_files(
    #     ('super-advocado.jpg', open('/home/clemens/Pictures/super-advocado.jpg', 'rb')),
    # )
    # itemid = result[0]['itemid']

    # result = moodle.modcontentservice.update_page_content(cmid=2, page=dict(
    #     text='<p><img class="img-fluid" src="@@PLUGINFILE@@/super-advocado.jpg" alt="advocado" width="1024" height="1024"></p>',
    #     itemid=itemid,
    # ))
    # print(result)

    # result = moodle.upload_files(
    #     ('Apothecary.jpg', open('/home/clemens/Pictures/WerewolfDarkArts/cropped/Apothecary.jpg', 'rb')),
    # )
    # itemid = result[0]['itemid']

    # result = moodle.modcontentservice.update_resource_content(cmid=3, files=itemid)
    # print(result)

    result = moodle.upload_files(
        ('super-advocado.jpg', open('/home/clemens/Pictures/super-advocado.jpg', 'rb')),
        ('Apothecary.jpg', open('/home/clemens/Pictures/WerewolfDarkArts/cropped/Apothecary.jpg', 'rb')),
    )
    itemid = result[0]['itemid']

    result = moodle.modcontentservice.update_folder_content(cmid=4, files=itemid, intro=dict(text='test'))
    print(result)
