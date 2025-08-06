from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _coerce_path(obj):
    assert isinstance(obj, (Path, str, type(None)))
    if isinstance(obj, str):
        obj = Path(obj)
    return obj


def _coerce_editor_content(obj):
    assert isinstance(obj, (EditorContent, dict, type(None)))
    if isinstance(obj, dict):
        obj = EditorContent(**obj)
    return obj


@dataclass(kw_only=True)
class EditorContent:
    source: Path
    attachments: list[Path] = field(default_factory=list)

    def __post_init__(self):
        self.source = _coerce_path(self.source)
        for i in range(len(self.attachments)):
            self.attachments[i] = _coerce_path(self.attachments[i])


@dataclass(kw_only=True)
class ModuleMeta:
    mod: str
    course: Optional[int] = None
    cmid: int
    intro: Optional[EditorContent] = None

    def __new__(cls, *args, **kwargs):
        match kwargs['mod']:
            case 'assign':
                cls = AssignMeta
            case 'folder':
                cls = FolderMeta
            case 'page':
                cls = PageMeta
            case 'resource':
                cls = ResourceMeta
        return super().__new__(cls)

    def __post_init__(self):
        self.intro = _coerce_editor_content(self.intro)


@dataclass(kw_only=True)
class AssignMeta(ModuleMeta):
    activity: Optional[EditorContent] = None
    attachments: list[Path] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self.activity = _coerce_editor_content(self.activity)
        for i in range(len(self.attachments)):
            self.attachments[i] = _coerce_path(self.attachments[i])


@dataclass(kw_only=True)
class FolderMeta(ModuleMeta):
    files: list[Path]

    def __post_init__(self):
        super().__post_init__()
        for i in range(len(self.files)):
            self.files[i] = _coerce_path(self.files[i])


@dataclass(kw_only=True)
class PageMeta(ModuleMeta):
    page: Optional[EditorContent] = None

    def __post_init__(self):
        super().__post_init__()
        self.page = _coerce_editor_content(self.page)


@dataclass(kw_only=True)
class ResourceMeta(ModuleMeta):
    file: Path

    def __post_init__(self):
        super().__post_init__()
        self.file = _coerce_path(self.file)
