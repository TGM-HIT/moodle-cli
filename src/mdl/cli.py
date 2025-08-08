from pathlib import Path
from typing_extensions import Annotated

from ruamel.yaml import YAML
import sys
import typer

from . import typst, Mdl, CoursesFilter
from .course import ModuleMeta


app = typer.Typer(rich_markup_mode='markdown', no_args_is_help=True)


def exit(*msg, code=1):
    print(file=sys.stderr, *msg)
    raise typer.Exit(code=code)

@app.callback()
def main(
    base_url: Annotated[str, typer.Option(
        envvar="MOODLE_BASE_URL",
        help="the URL of your Moodle installation not including `/webservice/rest/server.php`",
        rich_help_panel="Connection",
        show_default=False,
    )],
    token: Annotated[str, typer.Option(
        envvar="MOODLE_TOKEN",
        help="the webservice token used to access Moodle, a 32 digit hex string",
        rich_help_panel="Connection",
        show_default=False,
    )],
):
    """
    Manage Moodle courses and activities.
    """
    global moodle
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



    By using a prelude, the module may be self-contained. In that case, the contained module
    information will usually contain a reference to itself, e.g. `source: module.md` inside a file
    `module.md`.



    File paths are always resolved relative to the specified file. For self-contained files, that
    means a self-reference can always be written as a file name without a path component.
    """

    module_metas = []
    for module_path in modules:
        ext = module_path.suffix
        match ext:
            case '.yaml' | '.yml':
                meta = YAML(typ='safe').load(module_path)
            case '.md':
                meta = next(YAML(typ='safe').load_all(module_path))
            case '.typ':
                meta = typst.frontmatter(module_path)
            case _:
                exit(f"unknown module type: {module_path} (supported: .yaml/.yml, .md, .typ)")

        meta = ModuleMeta(**meta)

        if verify:
            cm = moodle.get_course_module(meta.cmid).cm
            if cm.modname != meta.mod:
                exit(f"modules is supposed to be of type mod_{meta.mod}, but is mod_{cm.modname}")
            if meta.course is not None and cm.course != meta.course:
                exit(f"modules is supposed to be in course {meta.course}, but is in {cm.course}")

        module_metas.append(meta)

    if dry_run:
        print("performing a dry-run, exiting...")
        return

    for (module_path, module) in zip(modules, module_metas):
        root = module_path.parent
        result = moodle.upload_module(root, module)
        if result != 'ok':
            exit(f"unexpected response while processing {module_path}: {result}")


if __name__ == "__main__":
    app()
