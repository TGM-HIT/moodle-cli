from typing_extensions import Annotated

import typer

from . import Mdl


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


@app.command()
def test():
    from pathlib import Path

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
