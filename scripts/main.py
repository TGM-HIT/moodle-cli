import json
import sys

from bs4 import BeautifulSoup
from .moodle import Moodle
import requests
import typst

base_url = 'http://localhost:8000'
url = f'{base_url}/webservice/rest/server.php'
token = '50b52d459bb40fed93221a5bb20d2e82'

moodle = Moodle(url, token)


def process(filename: str):
    metadata = json.loads(typst.query(filename, '<frontmatter>', field="value", one=True))
    html = typst.compile(filename, format='html')
    body = BeautifulSoup(html, 'html.parser').body.decode_contents()

    return metadata, body

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python main.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    metadata, body = process(filename)
    if metadata['mod'] != 'assign':
        raise ValueError(f"Unsupported module type: {metadata['mod']}")

    if len(metadata['attachments']) != 0:
        result = moodle.upload(*(
            (filename, open(filename, 'rb'))
            for filename in set(metadata['attachments'])
        ))
        itemid = result[0].itemid
    else:
        itemid = None

    result = moodle.modcontentservice.update_assign_content(
        cmid=metadata['cmid'],
        intro=dict(text=body),
        attachments=itemid,
    )
    print(result)

    # result = moodle.upload(
    #     ('super-advocado.jpg', open('/home/clemens/Pictures/super-advocado.jpg', 'rb')),
    # )
    # itemid = result[0].itemid

    # result = moodle.modcontentservice.update_page_content(cmid=2, page=dict(
    #     text='<p><img class="img-fluid" src="@@PLUGINFILE@@/super-advocado.jpg" alt="advocado" width="1024" height="1024"></p>',
    #     itemid=itemid,
    # ))
    # print(result)

    # result = moodle.upload(
    #     ('Apothecary.jpg', open('/home/clemens/Pictures/WerewolfDarkArts/cropped/Apothecary.jpg', 'rb')),
    # )
    # itemid = result[0].itemid

    # result = moodle.modcontentservice.update_resource_content(cmid=3, files=itemid)
    # print(result)

    # result = moodle.upload(
    #     ('super-advocado.jpg', open('/home/clemens/Pictures/super-advocado.jpg', 'rb')),
    #     ('Apothecary.jpg', open('/home/clemens/Pictures/WerewolfDarkArts/cropped/Apothecary.jpg', 'rb')),
    # )
    # itemid = result[0].itemid

    # result = moodle.modcontentservice.update_folder_content(cmid=4, files=itemid, intro=dict(text='test'))
    # print(result)

    # result = moodle.upload(
    #     ('super-advocado.jpg', open('/home/clemens/Pictures/super-advocado.jpg', 'rb')),
    # )
    # itemid = result[0].itemid

    # result = moodle.upload(
    #     ('super-advocado.jpg', open('/home/clemens/Pictures/super-advocado.jpg', 'rb')),
    # )
    # att_itemid = result[0].itemid

    # result = moodle.modcontentservice.update_assign_content(cmid=2, intro=dict(
    #     text='<p><img class="img-fluid" src="@@PLUGINFILE@@/super-advocado.jpg" alt="advocado" width="1024" height="1024"></p>',
    #     itemid=itemid,
    # ), attachments=att_itemid)
    # print(result)
