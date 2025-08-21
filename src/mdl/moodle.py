from moodle import Moodle as _Moodle, BaseMoodle
from moodle.utils.decorator import lazy


class ModContentService(BaseMoodle):
    def update_section_content(self, *, section: int, summary: dict=None):
        if summary is None:
            summary = dict(text='')

        data = self.moodle.post(
            "local_modcontentservice_update_section_content",
            section=section,
            summary=summary,
        )
        return data

    def update_assign_content(self, *, cmid: int, intro: dict=None, activity: dict=None, attachments: int=None):
        if intro is None:
            intro = dict(text='')
        if activity is None:
            activity = dict(text='')
        if attachments is None:
            attachments = 0

        data = self.moodle.post(
            "local_modcontentservice_update_assign_content",
            cmid=cmid,
            intro=intro,
            activity=activity,
            attachments=attachments,
        )
        return data

    def update_folder_content(self, *, cmid: int, intro: dict=None, files: int):
        if intro is None:
            intro = dict(text='')

        data = self.moodle.post(
            "local_modcontentservice_update_folder_content",
            cmid=cmid,
            intro=intro,
            files=files,
        )
        return data

    def update_label_content(self, *, cmid: int, intro: dict=None):
        if intro is None:
            intro = dict(text='')

        data = self.moodle.post(
            "local_modcontentservice_update_label_content",
            cmid=cmid,
            intro=intro,
        )
        return data

    def update_page_content(self, *, cmid: int, intro: dict=None, page: dict):
        if intro is None:
            intro = dict(text='')

        data = self.moodle.post(
            "local_modcontentservice_update_page_content",
            cmid=cmid,
            intro=intro,
            page=page,
        )
        return data

    def update_resource_content(self, *, cmid: int, intro: dict=None, files: int):
        if intro is None:
            intro = dict(text='')

        data = self.moodle.post(
            "local_modcontentservice_update_resource_content",
            cmid=cmid,
            intro=intro,
            files=files,
        )
        return data


class Moodle(_Moodle):
    def __init__(self, url: str, token: str):
        super(Moodle, self).__init__(url, token)

    @property  # type: ignore
    @lazy
    def modcontentservice(self) -> ModContentService:
        return ModContentService(self)
