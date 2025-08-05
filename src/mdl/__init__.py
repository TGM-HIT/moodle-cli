import json
from pathlib import Path
import sys

from bs4 import BeautifulSoup
from .moodle import Moodle
import requests
import typst

base_url = 'http://localhost:8000'
url = f'{base_url}/webservice/rest/server.php'
token = '519d3ee448bc9ee4d4d96a7ba7edf64a'

moodle = Moodle(url, token)


def process(filename: str):
    metadata = json.loads(typst.query(filename, '<frontmatter>', field="value", one=True))
    html = typst.compile(filename, format='html')
    body = BeautifulSoup(html, 'html.parser').body.decode_contents()

    return metadata, body

def list_my_courses(editable=True):
    if editable:
        return moodle.core.course.search_courses("search", "", requiredcapabilities=['moodle/course:manageactivities'])
    else:
        return moodle.core.course.search_courses("search", "", limittoenrolled=1)

def get_course_contents(courseid):
    return moodle.core.course.get_contents(courseid)

def get_course_module(cmid, courseid=None):
    module = moodle.core.course.get_course_module(cmid)
    if courseid is not None and module.cm.course != courseid:
        raise ValueError("cmid does not belong to the given course")
    return module

def main():
    print(f"Courses:")
    for course in list_my_courses().courses:
        print(f"- {course.displayname} (ID={course.id})")

    print(f"Test Course Contents:")
    for section in get_course_contents(2):
        print(f"- {section.section}: {section.name} (ID={section.id}){" (hidden)" if not section.visible else ""}")
        for module in section.modules:
            print(module)
            print(f"  - {module.name} (mod_{module.modname}, ID={module.id}){" (hidden)" if not section.visible else ""}")

    print(f"Test Assignment:")
    print(get_course_module(2, courseid=2))

    # if len(sys.argv) < 2:
    #     print("Usage: python main.py <filename>")
    #     sys.exit(1)

    # filename = Path(sys.argv[1])
    # metadata, body = process(filename)
    # if metadata['mod'] != 'assign':
    #     raise ValueError(f"Unsupported module type: {metadata['mod']}")

    # if len(metadata['attachments']) != 0:
    #     result = moodle.upload(*(
    #         (attachment, open(filename.parent/attachment, 'rb'))
    #         for attachment in set(metadata['attachments'])
    #     ))
    #     itemid = result[0].itemid
    # else:
    #     itemid = None

    # result = moodle.modcontentservice.update_assign_content(
    #     cmid=metadata['cmid'],
    #     intro=dict(text=body),
    #     attachments=itemid,
    # )
    # print(result)

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

if __name__ == '__main__':
    main()
