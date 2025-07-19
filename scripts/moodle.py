from moodle import Moodle as _Moodle, BaseMoodle
from moodle.utils.decorator import lazy


class ModContentService(BaseMoodle):
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


class Moodle(_Moodle):
    def __init__(self, url: str, token: str):
        super(Moodle, self).__init__(url, token)

    @property  # type: ignore
    @lazy
    def modcontentservice(self) -> ModContentService:
        return ModContentService(self)
