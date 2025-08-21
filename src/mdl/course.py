from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ruamel.yaml import YAML

from . import typst


class CourseException(Exception):
    pass


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

    def dependencies(self, root: Path) -> set[Path]:
        dependencies = set()
        dependencies.add(root/self.source)
        dependencies.update(root/att for att in self.attachments)
        if self.source.suffix == '.typ':
            dependencies.update(root/att for att in typst.attachments(root/self.source))
            dependencies.update(root/dep for dep in typst.dependencies(root/self.source))
        return dependencies


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
            case 'label':
                cls = LabelMeta
            case 'page':
                cls = PageMeta
            case 'resource':
                cls = ResourceMeta
            case _:
                raise AssertionError("Unknown ModuleMeta class")
        return super().__new__(cls)

    def __post_init__(self):
        self.intro = _coerce_editor_content(self.intro)

    def dependencies(self, root: Path) -> set[Path]:
        return self.intro.dependencies(root) if self.intro is not None else set()


@dataclass(kw_only=True)
class AssignMeta(ModuleMeta):
    activity: Optional[EditorContent] = None
    attachments: list[Path] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()
        self.activity = _coerce_editor_content(self.activity)
        for i in range(len(self.attachments)):
            self.attachments[i] = _coerce_path(self.attachments[i])

    def dependencies(self, root: Path) -> set[Path]:
        dependencies = super().dependencies(root)
        if self.activity is not None:
            dependencies.update(self.activity.dependencies(root))
        dependencies.update(root/att for att in self.attachments)
        return dependencies


@dataclass(kw_only=True)
class FolderMeta(ModuleMeta):
    files: list[Path]

    def __post_init__(self):
        super().__post_init__()
        for i in range(len(self.files)):
            self.files[i] = _coerce_path(self.files[i])

    def dependencies(self, root: Path) -> set[Path]:
        dependencies = super().dependencies(root)
        dependencies.update(root/f for f in self.files)
        return dependencies


@dataclass(kw_only=True)
class LabelMeta(ModuleMeta):
    pass

@dataclass(kw_only=True)
class PageMeta(ModuleMeta):
    page: Optional[EditorContent] = None

    def __post_init__(self):
        super().__post_init__()
        self.page = _coerce_editor_content(self.page)

    def dependencies(self, root: Path) -> set[Path]:
        dependencies = super().dependencies(root)
        if self.page is not None:
            dependencies.update(self.page.dependencies(root))
        return dependencies


@dataclass(kw_only=True)
class ResourceMeta(ModuleMeta):
    file: Path

    def __post_init__(self):
        super().__post_init__()
        self.file = _coerce_path(self.file)

    def dependencies(self, root: Path) -> set[Path]:
        dependencies = super().dependencies(root)
        dependencies.add(root/self.file)
        return dependencies


def collect_metas(modules: list[Path], verify_with=None) -> list[ModuleMeta]:
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
                raise CourseException(f"unknown module type: {module_path} (supported: .yaml/.yml, .md, .typ)")

        meta = ModuleMeta(**meta)

        if verify_with is not None:
            moodle = verify_with
            cm = moodle.get_course_module(meta.cmid).cm
            if cm.modname != meta.mod:
                raise CourseException(f"modules is supposed to be of type mod_{meta.mod}, but is mod_{cm.modname}")
            if meta.course is not None and cm.course != meta.course:
                raise CourseException(f"modules is supposed to be in course {meta.course}, but is in {cm.course}")

        module_metas.append(meta)
    return module_metas
