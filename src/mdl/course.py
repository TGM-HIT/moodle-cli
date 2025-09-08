from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from moodle.core.course import ContentOption
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
class SectionMeta:
    course: Optional[int] = None
    section: int
    summary: Optional[EditorContent] = None

    def __post_init__(self):
        self.summary = _coerce_editor_content(self.summary)

    def dependencies(self, root: Path) -> set[Path]:
        return self.summary.dependencies(root) if self.summary is not None else set()


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
    files: list[tuple[Path, Path]]

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.files, list):
            for i in range(len(self.files)):
                f = _coerce_path(self.files[i])
                self.files[i] = (f, f)
        else:
            self.files = [
                (_coerce_path(k), _coerce_path(v))
                for k, v in self.files.items()
            ]

    def dependencies(self, root: Path) -> set[Path]:
        dependencies = super().dependencies(root)
        dependencies.update(root/f for _, f in self.files)
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


def collect_metas(modules: list[Path], verify_with=None) -> list[tuple[Path, ModuleMeta | SectionMeta]]:
    def read_input(input_path: Path):
        ext = input_path.suffix
        match ext:
            case '.yaml' | '.yml':
                return YAML(typ='safe').load(input_path)
            case '.md':
                return next(YAML(typ='safe').load_all(input_path))
            case '.typ':
                return typst.frontmatter(input_path)
            case _:
                raise CourseException(f"unknown input type: {input_path} (supported: .yaml/.yml, .md, .typ)")

    def prepare_module_meta(meta) -> ModuleMeta:
        meta = ModuleMeta(**meta)

        if verify_with is not None:
            moodle = verify_with
            cm = moodle.get_course_module(meta.cmid).cm
            if cm.modname != meta.mod:
                raise CourseException(f"modules is supposed to be of type mod_{meta.mod}, but is mod_{cm.modname}")
            if meta.course is not None and cm.course != meta.course:
                raise CourseException(f"modules is supposed to be in course {meta.course}, but is in {cm.course}")

        return meta

    def prepare_section_meta(meta) -> SectionMeta:
        meta.pop('mod')
        meta = SectionMeta(**meta)

        if verify_with is not None:
            moodle = verify_with
            sections = moodle.core.course.get_contents(meta.course, [ContentOption('excludemodules', True)])
            if not any(section.id == meta.section for section in sections):
                raise CourseException(f"section is supposed to be in course {meta.course}")

        return meta

    module_metas = []
    def collect(input_value, root=None, nesting_info=None):
        if isinstance(input_value, dict):
            # the top level inputs are paths, so we shouldn't get here without nesting info
            assert nesting_info is not None
            name, i = nesting_info
            meta = input_value
            # root remains the same; the input is relative to the same file
            # name will be of the for "<inputfile>:children[i].children[j]"
            if name.endswith("]"):
                name = f"{name}.children[{i}]"
            else:
                name = f"{name}:children[{i}]"
        else:
            if root is not None:
                # nested input: interpret relative to root
                input_value = root/input_value
            meta = read_input(input_value)
            root = input_value.parent
            name = str(input_value)

        children = meta.pop('children', None)

        if 'mod' in meta:
            if not meta['mod'].startswith('$'):
                meta = prepare_module_meta(meta)
            elif meta['mod'] == '$section':
                meta = prepare_section_meta(meta)
            else:
                raise ValueError(f"{name}: unknown special module type '{meta['mod']}'")

            module_metas.append((name, root, meta))
        elif meta != {}:
            raise ValueError(f"unexpected extra content in {name}: {meta}")
        elif children is None:
            raise ValueError(f"{name} contained neither a module nor children")

        if children is not None:
            for i, input_value in enumerate(children):
                collect(input_value, root, (name, i))

    for input_path in modules:
        collect(input_path)

    return module_metas
