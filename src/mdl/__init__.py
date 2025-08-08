from enum import Enum
from pathlib import Path

from .course import ModuleMeta
from .moodle import Moodle


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

    def upload_module(self, root: Path, module: ModuleMeta):
        def upload_files(files):
            if len(files) == 0:
                return None

            result = self.upload(*(
                (f.name, open(root/f, 'rb'))
                for f in set(files)
            ))
            itemid = result[0].itemid
            return itemid

        def prepare_editor(editor):
            if editor == None:
                return None

            source = root/editor.source
            attachments = editor.attachments
            suffix = editor.source.suffix

            if suffix == '.typ':
                # compile Typst document to HTML
                text = typst.body(source)

                # extract attachments from Typst metadata
                attachments += [Path(att) for att in typst.attachments(source)]

            else:
                # read text file
                with open(source, 'rt') as f:
                    text = f.read()

                if suffix == '.md' and text.startswith('---'):
                    # this markdown file has a prelude; skip it
                    import re

                    matches = re.finditer(r'^---( [|>][+-]?\d*)?\n', text, re.MULTILINE)
                    next(matches)  # the initial document separator
                    try:
                        match = next(matches)
                    except StopIteration:
                        # no second match: assume that this was not a prelude
                        pass
                    else:
                        # remove the prelude
                        text = text[match.end():]

            match suffix:
                case '.txt':
                    format = 2
                case '.md':
                    format = 4
                case '.html' | '.htm' | '.typ' | _:
                    format = 1
            itemid = upload_files(attachments)

            result = dict(text=text, format=format)
            if itemid is not None:
                result['itemid'] = itemid
            return result


        intro = prepare_editor(module.intro)

        match module.mod:
            case 'assign':
                activity = prepare_editor(module.activity)
                attachments = upload_files(module.attachments)

                result = self.modcontentservice.update_assign_content(
                    cmid=module.cmid,
                    intro=intro,
                    activity=activity,
                    attachments=attachments,
                )
            case 'folder':
                files = upload_files(module.files)

                result = self.modcontentservice.update_folder_content(
                    cmid=module.cmid,
                    intro=intro,
                    files=files,
                )
            case 'page':
                page = prepare_editor(module.page)

                result = self.modcontentservice.update_page_content(
                    cmid=module.cmid,
                    intro=intro,
                    page=page,
                )
            case 'resource':
                files = upload_files([module.file])

                result = self.modcontentservice.update_resource_content(
                    cmid=module.cmid,
                    intro=intro,
                    files=files,
                )

        return result
