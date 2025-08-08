#let attachment(source) = [#metadata(source)<attachments>]

#let setup(..args) = doc => {
  assert.eq(args.pos(), (), message: "no positional arguments allowed")
  let frontmatter = args.named()

  [#metadata(frontmatter)<frontmatter>]

  doc
}
