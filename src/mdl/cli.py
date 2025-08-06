from pathlib import Path
from typing_extensions import Annotated

from ruamel.yaml import YAML
import sys
import typer

from . import Mdl, CoursesFilter


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
    Uploads one or more modules to Moodle.
    """

    module_metas = []
    for module_path in modules:
        ext = module_path.suffix
        match ext:
            case '.yaml' | '.yml':
                meta = YAML(typ='safe').load(module_path)
            case '.md':
                modules = YAML(typ='safe').load_all(module_path)
                meta = next(modules)

        if verify:
            cm = moodle.get_course_module(meta['cmid']).cm
            if cm.modname != meta['mod']:
                exit(f"modules is supposed to be of type mod_{meta['mod']}, but is mod_{cm.modname}")
            if 'course' in meta and cm.course != meta['course']:
                exit(f"modules is supposed to be in course {meta['course']}, but is in {cm.course}")

        module_metas.append(meta)

    if dry_run:
        print("performing a dry-run, exiting...")
        return


@app.command()
def test():
    from . import process

    filename = Path('content/activity.typ')
    metadata, body = process(filename)
    if metadata['mod'] != 'assign':
        raise ValueError(f"Unsupported module type: {metadata['mod']}")

    if len(metadata['attachments']) != 0:
        result = moodle.upload(*(
            (attachment, open(filename.parent/attachment, 'rb'))
            for attachment in set(metadata['attachments'])
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


if __name__ == "__main__":
    app()
