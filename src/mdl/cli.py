from pathlib import Path
from typing_extensions import Annotated

import sys
import typer

from . import course, Mdl, CoursesFilter


app = typer.Typer(rich_markup_mode='markdown', no_args_is_help=True)

moodle = None


def exit(*msg, code=1):
    print(file=sys.stderr, *msg)
    raise typer.Exit(code=code)


def require_moodle():
    if moodle is None:
        exit(f"base-url and token are required for this command")


@app.callback()
def main(
    base_url: Annotated[str, typer.Option(
        envvar="MOODLE_BASE_URL",
        help="the URL of your Moodle installation not including `/webservice/rest/server.php`",
        rich_help_panel="Connection",
        show_default=False,
    )]=None,
    token: Annotated[str, typer.Option(
        envvar="MOODLE_TOKEN",
        help="the webservice token used to access Moodle, a 32 digit hex string",
        rich_help_panel="Connection",
        show_default=False,
    )]=None,
):
    """
    Manage Moodle courses and activities.
    """
    global moodle
    if base_url is not None and token is not None:
        moodle = Mdl(f'{base_url}/webservice/rest/server.php', token)


@app.command()
def courses(
    filter: Annotated[CoursesFilter, typer.Option(
        help="""
        what subset of the user's courses to show

        - `enrolled` selects all the user's courses
        - `editable` selects the user's courses for which they have editing privileges
          (`moodle/course:manageactivities`)
        """,
    )]=CoursesFilter.editable,
):
    """
    Lists the user's Moodle courses.
    """
    require_moodle()
    courses = moodle.get_courses(filter).courses
    for course in courses:
        print(f"- {course.displayname} (ID={course.id})")


@app.command()
def contents(
    courseid: Annotated[int, typer.Argument(
        help="the ID of the course whose contents to display",
        show_default=False,
    )],
):
    """
    Lists a course's sections and modules.
    """
    require_moodle()
    sections = moodle.get_course_contents(2)
    for section in sections:
        print(f"- {section.section}: {section.name} (ID={section.id}){" (hidden)" if not section.visible else ""}")
        for cm in section.modules:
            print(f"  - {cm.name} (mod_{cm.modname}, ID={cm.id}){" (hidden)" if not cm.visible else ""}")


@app.command()
def module(
    cmid: Annotated[int, typer.Argument(
        help="the ID of the module (\"course module ID\") to display",
        show_default=False,
    )],
):
    """
    Shows a module.
    """
    require_moodle()
    cm = moodle.get_course_module(cmid).cm
    print(f"{cm.name} (mod_{cm.modname}, ID={cm.id}, in course {cm.course}){" (hidden)" if not cm.visible else ""}")


@app.command()
def upload(
    modules: Annotated[list[Path], typer.Argument(
        help="the manifests specifying the modules to upload",
        show_default=False,
    )],
    verify: Annotated[bool, typer.Option(
        help="whether to verify the module type and course before uploading a module",
    )]=True,
    dry_run: Annotated[bool, typer.Option(
        help="whether to not actually upload anything",
    )]=False,
):
    """
    Uploads one or more modules to Moodle. Each module is specified as a file.

    The files may be of the following types:

    - `.yaml`/`.yml`: contains module information in YAML format

    - `.md`: contains module information in a YAML format prelude, enclosed in `---`

    - `.typ`: contains module information in metadata labelled `<frontmatter>`;
      if used for rich text, attachments can be added through metadata labelled `<attachments>`



    By using a prelude, the module may be self-contained. In that case, the contained module
    information will usually contain a reference to itself, e.g. `source: module.md` inside a file
    `module.md`.



    File paths are always resolved relative to the specified file. For self-contained files, that
    means a self-reference can always be written as a file name without a path component.
    """
    if verify or not dry_run:
        require_moodle()

    try:
        module_metas = course.collect_metas(modules, verify_with=moodle if verify else None)
    except course.CourseException as ex:
        exit(*ex.args)

    if dry_run:
        print("performing a dry-run, exiting...")
        return

    for (module_path, module) in zip(modules, module_metas):
        root = module_path.parent
        result = moodle.upload_module(root, module)
        if result != 'ok':
            exit(f"unexpected response while processing {module_path}: {result}")


@app.command()
def list(
    modules: Annotated[list[Path], typer.Argument(
        help="the manifests specifying the modules to scan",
        show_default=False,
    )],
    sort: Annotated[bool, typer.Option(
        help="whether to print the files in alphabetical order",
    )]=False,
):
    """
    Lists files that contribute content to the specified modules. The files are the same types as
    accepted by the `upload` command. The list of contributing files is constructed by taking all
    `source`s and `attachments`.

    A `.md` or `.typ` input file that does not specify itself as a source in its frontmatter is not
    considered to contribute content.

    Note that this does _not_ automatically consider imports and includes inside `.typ` files. Typst
    files can add `<dependencies>` metadata to augment the list of files, but must do so manually
    and need to take care about relative paths.
    """

    try:
        module_metas = course.collect_metas(modules)
    except course.CourseException as ex:
        exit(*ex.args)

    dependencies = set()
    for (module_path, module) in zip(modules, module_metas):
        root = module_path.parent
        dependencies.update(module.dependencies(root))

    if sort:
        dependencies = sorted(dependencies)

    for path in dependencies:
        print(path)


if __name__ == "__main__":
    app()
