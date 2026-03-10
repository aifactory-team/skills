# D2 Language Complete Reference

## 1. Core Syntax

### Nodes
```d2
hello                        # bare node (label = key)
server: "Web Server"         # node with custom label
server.label: "Web Server"   # explicit label
a; b; c                      # multiple on one line
"my node"                    # quoted key for special chars
```

### Connections
```d2
a -> b           # directed
a <- b           # reverse directed
a <-> b          # bidirectional
a -- b           # undirected
a -> b -> c      # chained
a -> b: "label"  # with label
a -> a           # self-reference
```

### Connection Styling
```d2
a -> b: {
  style.stroke: red
  style.stroke-width: 3
  style.stroke-dash: 5
  style.animated: true
  style.opacity: 0.5
  source-arrowhead: { shape: diamond; style.filled: true }
  target-arrowhead: { shape: circle; style.filled: false }
}
```

Arrowhead shapes: `triangle`, `arrow`, `diamond`, `circle`, `box`, `cf-one`, `cf-one-required`, `cf-many`, `cf-many-required`, `cross`

### Comments
```d2
# full-line comment
a -> b  # end-of-line comment
```

## 2. All Shape Types

```d2
myNode: { shape: <type> }
```

| Shape | Description |
|-------|-------------|
| `rectangle` | Default |
| `square` | 1:1 ratio |
| `circle` | 1:1 ratio |
| `oval` | Ellipse |
| `diamond` | Decision |
| `hexagon` | |
| `cloud` | |
| `cylinder` | Database |
| `queue` | Sideways cylinder |
| `package` | |
| `step` | Parallelogram variant |
| `parallelogram` | |
| `document` | Wavy bottom |
| `callout` | Speech bubble |
| `stored_data` | |
| `person` | Stick figure |
| `page` | Folded corner |
| `c4-person` | C4 model person |
| `image` | Standalone image (requires `icon:`) |
| `class` | UML class |
| `sql_table` | DB table |
| `sequence_diagram` | Sequence diagram container |

## 3. Containers (Nesting)

```d2
# Dot notation
aws.server.process

# Block syntax
aws: "Amazon Web Services" {
  server: "App Server" {
    process
  }
}

# Parent reference with underscore
aws: {
  server
  _.internet -> server   # _ = parent scope
}
```

## 4. All Style Properties

```d2
myNode.style.fill: "#e8f4fd"
myNode.style.stroke: "#2196F3"
myNode.style.font-color: "#333"
myNode.style.stroke-width: 3
myNode.style.stroke-dash: 5
myNode.style.border-radius: 8
myNode.style.double-border: true
myNode.style.shadow: true
myNode.style.3d: true
myNode.style.multiple: true
myNode.style.fill-pattern: dots    # dots | lines | grain | none
myNode.style.opacity: 0.5
myNode.style.animated: true
myNode.style.font-size: 18
myNode.style.bold: true
myNode.style.italic: true
myNode.style.underline: true
myNode.style.text-transform: uppercase  # uppercase | lowercase | title | none
```

Gradient fill:
```d2
myNode.style.fill: "linear-gradient(#f5f5f5, #cccccc)"
```

## 5. Layout Direction

```d2
direction: down    # down (default) | right | left | up
```

Per-container direction (TALA layout only):
```d2
outer: {
  direction: right
  inner: { direction: down }
}
```

## 6. Themes

### CLI
```bash
d2 --theme 1 input.d2 output.png      # Neutral Grey
d2 --dark-theme 200 input.d2 out.svg   # Dark Mauve
d2 --sketch input.d2 output.svg        # hand-drawn style
```

### In-file
```d2
vars: { d2-config: { theme-id: 5 } }
```

### Light Theme IDs
| ID | Name |
|----|------|
| 0 | Neutral Default |
| 1 | Neutral Grey |
| 3 | Flagship Terrastruct |
| 4 | Cool Classics |
| 5 | Mixed Berry Blue |
| 6 | Grape Soda |
| 7 | Aubergine |
| 8 | Colorblind Clear |
| 100 | Vanilla Nitro Cola |
| 101 | Orange Creamsicle |
| 102 | Shirley Temple |
| 103 | Earth Tones |
| 104 | Everglade Green |
| 105 | Buttered Toast |
| 300 | Terminal |
| 302 | Origami |

### Dark Theme IDs
| ID | Name |
|----|------|
| 200 | Dark Mauve |
| 201 | Dark Flagship Terrastruct |

## 7. Special Shapes

### SQL Table
```d2
users: {
  shape: sql_table
  id: int {constraint: primary_key}
  email: varchar(255) {constraint: [unique, not_null]}
  name: varchar(100)
}
posts: {
  shape: sql_table
  id: int {constraint: primary_key}
  user_id: int {constraint: foreign_key}
}
posts.user_id -> users.id
```

### UML Class
```d2
Animal: {
  shape: class
  +name: string
  -_id: uuid
  +speak(): string
}
```
Visibility: `+` public, `-` private, `#` protected, `~` package

### Sequence Diagram
```d2
seq: {
  shape: sequence_diagram
  alice; bob
  alice -> bob: Hello
  bob -> alice: Hi
  alice -> alice: thinking...
  alice.note: "Ready"
}
```

### Grid Diagram
```d2
grid: {
  grid-rows: 2
  grid-columns: 3
  grid-gap: 10
  a; b; c; d; e; f
}
```

## 8. Icons and Images

```d2
# Icon on node
server: { icon: https://icons.terrastruct.com/aws/Compute/EC2.svg }

# Standalone image
logo: { shape: image; icon: ./logo.png }

# Local file
myNode: { icon: ./images/icon.png }
```

Icon library: https://icons.terrastruct.com

## 9. Markdown and LaTeX in Labels

```d2
note: |md
  # Title
  **Bold** and _italic_
  - item 1
  - item 2
|

formula: |latex
  E = mc^2
|

code: |python
  def hello():
      print("hello")
|
```

## 10. Variables and Classes

### Variables
```d2
vars: {
  primary: "#2196F3"
}
a.style.fill: ${primary}
```

### Style Classes (reusable styles)
```d2
classes: {
  blue_box: {
    style.fill: "#e3f2fd"
    style.stroke: "#1565c0"
    style.border-radius: 6
  }
}
web.class: blue_box
api.class: blue_box
```

## 11. Positioning

```d2
title: "My Diagram" { near: top-center }
legend: { near: bottom-right }
myNode: { width: 300; height: 150 }
```

Near values: `top-left`, `top-center`, `top-right`, `center-left`, `center-right`, `bottom-left`, `bottom-center`, `bottom-right`

## 12. CLI Reference

```bash
d2 input.d2 output.png          # basic render
d2 input.d2 output.svg          # SVG output
d2 input.d2 output.pdf          # PDF output
d2 -w input.d2 output.svg       # watch mode (live reload)
d2 -t 1 input.d2 output.png     # with theme
d2 -s input.d2 output.svg       # sketch (hand-drawn) mode
d2 -l elk input.d2 output.svg   # ELK layout engine
d2 --pad 40 input.d2 out.png    # padding
d2 --scale 2 input.d2 out.png   # 2x scale
d2 fmt input.d2                 # auto-format
d2 themes                       # list themes
d2 layout                       # list layout engines
```

### Korean Font Support
```bash
d2 --font-regular NotoSansKR-Regular.ttf \
   --font-bold NotoSansKR-Bold.ttf \
   input.d2 output.png
```
