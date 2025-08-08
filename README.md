# Moodle Command Line Interface

This Python CLI application allows managing Moodle modules through the [Module Content Service](https://github.com/TGM-HIT/moodle-local_modcontentservice). It supports the following operations:

- querying courses
  - list a user's enrolled or editable courses
  - list a course's contents
  - display a specific module of a course

  these are achieved through standard Moodle API endpoints
- updating modules
  - replace an assignment's description, activity instructions, and additional files
  - replace a folder's description and files
  - replace a page's description and page content
  - replace a resource's description and file

  these are achieved through [Module Content Service API endpoints](https://github.com/TGM-HIT/moodle-local_modcontentservice?tab=readme-ov-file#endpoint-functions)

## Example usage

This example requires the same prerequisites described at [Module Content Service, Example usage](https://github.com/TGM-HIT/moodle-local_modcontentservice?tab=readme-ov-file#example-usage), and that the Moodle CLI is installed. If they are fulfilled, you should be able to use the following script:

```bash
export MOODLE_TOKEN='YOUR-WEBSERVICE-TOKEN'
export MOODLE_BASE_URL='http://localhost:8000'

# confirm that the expected module exists
mdl module 2
# example output: Assignment (mod_assign, ID=2, in course 2)

# create a file for the module's content
cat > example.md <<EOF
---
mod: assign
cmid: 2
intro:
  source: example.md
  attachments:
    - example.jpg
---
# Assignment

Hello *world*

![Example](@@PLUGINFILE@@/example.jpg)
EOF

# upload to Moodle
mdl upload example.md
```

The following things happen in this script:

- The URL and credentials to use with the target moodle server are specified as environment variables; alternatively, you can specify them via `--base-url` and `--token`.
- The `mdl module` command is used to confirm that the target module is of the expected type. Note that this is also done by `mdl upload` unless `--no-verify` is specified.
- A file `example.md` with the desired content is created. The file starts with a YAML front matter block identifying the target module and where to find the content (here, the file itself), as well as attachments. For multi-file setups, this data can also be specified in a separate YAML file instead.
- The `mdl upload` command is used to update the module; multiple files may be specified for batch updates. The following steps can potentially happen per module:
  - The specified file is scanned for the module data.
    - For `.yaml`/`.yml`, the whole file is parsed as YAML.
    - For `.md`, this is the front matter.
    - For `.typ`, the `<frontmatter>` metadata is [queried](https://typst.app/docs/reference/introspection/query/#command-line-queries) and must contain a dictionary of the same shape.
  - For Markdown content, the front matter is stripped so that only the content is uploaded.
  - For Typst content, the document is compiled to HTML, and additionally the `<attachments>` metadata is queried and added to the attachments specified in the module data.
  - If there are attachments (e.g. images in the content, files for a `folder` module), they are uploaded to Moodle. In content, references to attachments need to be specified as `@@PLUGINFILE@@/<filename>`, where `<filename>` is the name of the uploaded file.
  - The content types (here: that of `example.md`) are inferred from the file extension.
  - The module is updated through the Module Content Service API.

## Installation

This tool is not published on PyPI and resides in a private Github repo, so it must be installed manually. The recommended way is to clone the repository and [install it via uv](https://docs.astral.sh/uv/guides/tools/#installing-tools):

```bash
git clone https://github.com/TGM-HIT/moodle-cli
uv tool install ./moodle-cli

mdl --help
```

This is a regular `pyproject.toml`-based project, so other ways of installation (e.g. `pip install ./moodle-cli`) should also work.

## Module configuration files

The central `mdl upload` command requires module data to be specified in a file. The common structure (in YAML syntax) is as follows:

```yaml
# string; one of `assign`, `folder`, `page`, `resource`
mod: <module name>
# optional int; used to verify the module belongs to the expected course
# found e.g. in the URL: `/course/view.php?id=<course ID>`
course: <course ID>
# int; the module ID
# found e.g. in the URL: `/mod/<module name>/view.php?id=<module ID>`
cmid: <module ID>
# optional; the module's description as rich text content
intro:
  # string; the file to use as the module's description content
  source: <file name>
  # optional; list of files (primarily images) embedded in the description
  attachments:
    - <file name>
    - ...
```

For Typst files, the module is specified in a metadata element labelled with `<frontmatter>`:

```typ
#metadata((mod: <module name>, ...))<frontmatter>
```

Beyond these, the following module-specific fields are supported:

- Assignments:

  ```yaml
  mod: assign
  ...
  # optional; activity instructions in the same format as `intro`
  activity:
    ...
  # optional; list of files attached to the assignment
  attachments:
    - <file name>
    - ...
  ```
- Folders

  ```yaml
  mod: folder
  ...
  # list of files in the folder
  files:
    - <file name>
    - ...
  ```
- Pages:

  ```yaml
  mod: page
  ...
  # optional; page content in the same format as `intro`
  page:
    ...
  ```
- Resources:

  ```yaml
  mod: resource
  ...
  # file name of the resource file
  file: <file name>
  ```


### Rich text content

The common `intro` and module-specific fields (e.g. `activity`, `page`) represent rich text content. These values are specified as a `source`, which is transmitted to Moodle as text, and optional `attachments`, which are files that are embedded in the text. When referencing embedded files, the text must use the `@@PLUGINFILE@@/<filename>` syntax. Here, `@@PLUGINFILE@@` is a prefix that Moodle normally inserts when post-processing form input.

The `source` file must have a proper extension, so that the Moodle content type can be inferred. The extensions `.md`, `.txt`, `.html`, `.htm` and `.typ` are supported, other extensions will be treated as HTML.

- If a markdown source contains YAML front matter, it will be stripped before being used as the content.
- Typst sources are compiled to HTML, and the `<attachments>` metadata is queried for additional files to upload. For example, if the module data specifies `source: example.typ` and `attachments: [example.jpg]`, and the Typst file contains `#metadata("thumbnail.jpg")<attachments>`, both images will be uploaded to Moodle.

### Input files

The data structure described above can be contained in different kinds of input files:

- `.yaml` or `.yml`: the whole file is parsed as YAML. This is the preferred format for cases where e.g. `intro` _and_ `activity` are specified – or neither, e.g. in the case of a `folder` without description.
- `.md`: the file must start with a YAML front matter block, which is used for the module data. The front matter will usually refer to the file itself as some `source`.
- `.typ`: the file must contain a `<frontmatter>` metadata element. The front matter will usually refer to the file itself as some `source`. When doing so, you can of course use `<attachments>` instead of adding the attachments to the module data.
