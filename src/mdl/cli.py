from typing_extensions import Annotated

import typer

from .moodle import Moodle


class Mdl(Moodle):
    def get_courses(self, editable=True):
        if editable:
            return self.core.course.search_courses("search", "", requiredcapabilities=['moodle/course:manageactivities'])
        else:
            return self.core.course.search_courses("search", "", limittoenrolled=1)


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
    for course in moodle.get_courses().courses:
        print(f"- {course.displayname} (ID={course.id})")


if __name__ == "__main__":
    app()
