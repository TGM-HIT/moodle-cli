#import "moodle.typ"

#show: moodle.setup(
  mod: "assign",
  course: 2,
  cmid: 2,
  intro: (source: "activity.typ"),
)

#quote(block: true)[
  asdf
]

#moodle.attachment("super-advocado.jpg")
#html.elem("img", attrs: (src: "@@PLUGINFILE@@/super-advocado.jpg", alt: "Advocado"))

```java
public static void main(String[] args) {

}
```

...
