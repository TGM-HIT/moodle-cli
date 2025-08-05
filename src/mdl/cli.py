from typing_extensions import Annotated

import typer

from .moodle import Moodle


class Mdl(Moodle):
    def get_courses(self, editable=True):
        if editable:
            return self.core.course.search_courses("search", "", requiredcapabilities=['moodle/course:manageactivities'])
        else:
            return self.core.course.search_courses("search", "", limittoenrolled=1)

    def get_course_contents(self, courseid):
        return self.core.course.get_contents(courseid)

    def get_course_module(self, cmid, courseid=None):
        module = self.core.course.get_course_module(cmid)
        if courseid is not None and module.cm.course != courseid:
            raise ValueError("cmid does not belong to the given course")
        return module


app = typer.Typer(no_args_is_help=True)


@app.callback()
def main(
    base_url: Annotated[str, typer.Option(envvar="MOODLE_BASE_URL")],
    token: Annotated[str, typer.Option(envvar="MOODLE_TOKEN")],
):
    """
    Manage Moodle courses and activities
    """
    global moodle
    moodle = Mdl(f'{base_url}/webservice/rest/server.php', token)


@app.command()
def courses(editable: bool=True):
    """
    Lists the user's Moodle courses; if editable is set, only courses the user has editing
    privileges for (`moodle/course:manageactivities`) are considered.
    """
    courses = moodle.get_courses().courses
    for course in courses:
        print(f"- {course.displayname} (ID={course.id})")


@app.command()
def contents(courseid: int):
    """
    Lists the course's sections and modules.
    """
    sections = moodle.get_course_contents(2)
    for section in sections:
        print(f"- {section.section}: {section.name} (ID={section.id}){" (hidden)" if not section.visible else ""}")
        for cm in section.modules:
            print(f"  - {cm.name} (mod_{cm.modname}, ID={cm.id}){" (hidden)" if not cm.visible else ""}")


@app.command()
def module(cmid: int):
    """
    Shows the module.
    """
    cm = moodle.get_course_module(cmid).cm
    print(f"{cm.name} (mod_{cm.modname}, ID={cm.id}, in course {cm.course}){" (hidden)" if not cm.visible else ""}")


if __name__ == "__main__":
    app()
