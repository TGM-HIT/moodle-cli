from enum import Enum
import json

from bs4 import BeautifulSoup
from .moodle import Moodle
import requests
import typst


class CoursesFilter(str, Enum):
    enrolled = "enrolled"
    editable = "editable"


class Mdl(Moodle):
    def get_courses(self, filter=CoursesFilter.editable):
        match filter:
            case CoursesFilter.enrolled:
                return self.core.course.search_courses("search", "", limittoenrolled=1)
            case CoursesFilter.editable:
                return self.core.course.search_courses("search", "", requiredcapabilities=['moodle/course:manageactivities'])

    def get_course_contents(self, courseid):
        return self.core.course.get_contents(courseid)

    def get_course_module(self, cmid, courseid=None):
        module = self.core.course.get_course_module(cmid)
        if courseid is not None and module.cm.course != courseid:
            raise ValueError("cmid does not belong to the given course")
        return module


def process(filename: str):
    metadata = json.loads(typst.query(filename, '<frontmatter>', field="value", one=True))
    html = typst.compile(filename, format='html')
    body = BeautifulSoup(html, 'html.parser').body.decode_contents()

    return metadata, body
