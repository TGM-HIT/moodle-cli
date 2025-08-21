#import "@preview/moodular:0.1.0" as moodular: c4l

#let attachment(source) = [#metadata(source)<attachments>]
#let dependency(source) = [#metadata(source)<dependencies>]

#let setup(..args) = doc => {
  assert.eq(args.pos(), (), message: "no positional arguments allowed")
  let frontmatter = args.named()

  show: moodular.preview()
  show image: it => attachment(it.source) + it

  [#metadata(frontmatter)<frontmatter>]

  doc
}
