# AssiDocs Diagram Skill

Create professional diagrams using the D2 declarative diagramming language (https://d2lang.com).
Use this for architecture diagrams, system explanations, flowcharts, ERDs, sequence diagrams, concept illustrations, and lecture materials.

## Trigger

Use when the user asks to:
- Create a diagram, flowchart, architecture diagram, system diagram
- Illustrate a concept or process visually
- Make an ERD, sequence diagram, class diagram
- Replace ASCII art with proper diagrams
- Create illustrations for lectures, presentations, or documentation
- "다이어그램", "그림", "삽화", "구조도", "흐름도", "시퀀스 다이어그램", "ERD"

## Workflow

1. **READ the reference**: Read [`d2-reference.md`](d2-reference.md) for syntax details before creating any diagram.

2. **Write the .d2 file**: Create a `.d2` file in the project directory with the diagram definition.

3. **Render to image**:
   ```bash
   d2 --theme 1 --pad 40 diagram.d2 diagram.png
   ```

4. **Verify**: Read the generated PNG to confirm it looks correct.

5. **Check aspect ratio**: Use `sips -g pixelWidth -g pixelHeight diagram.png` to get actual dimensions. When inserting into DOCX, calculate the correct width/height maintaining the original aspect ratio (max width 560px).

6. **If inserting into DOCX**: Use `ImageRun` from docx-js:
   ```javascript
   new Paragraph({
     alignment: AlignmentType.CENTER,
     children: [new ImageRun({
       type: "png",
       data: fs.readFileSync("diagram.png"),
       transformation: { width: CALC_W, height: CALC_H },
       altText: { title: "Diagram", description: "Description", name: "diagram" }
     })]
   })
   ```

## Design Guidelines

### For Lectures & Conceptual Diagrams
- Use `direction: down` for hierarchical structures
- Use `direction: right` for process flows
- Use containers to group related components
- Keep labels short and clear
- Use Korean labels where appropriate (D2 supports Korean natively)
- Use color-coded groups: light blue for main, light orange for sub-components, light green for external services
- Avoid `$` in labels (D2 interprets as substitution) — use "USD" or spell out

### Recommended Color Palette
```d2
# Main container
style.fill: "#E8F4FD"
style.stroke: "#1A73E8"

# Sub-components
style.fill: "#FFF3E0"
style.stroke: "#F57C00"

# External services
style.fill: "#E8F5E9"
style.stroke: "#388E3C"

# Warning/danger
style.fill: "#FFEBEE"
style.stroke: "#C62828"

# Neutral
style.fill: "#F5F5F5"
style.stroke: "#616161"
```

### Recommended Themes
| Use Case | Theme ID | Name |
|----------|----------|------|
| General/clean | 1 | Neutral Grey |
| Presentations | 4 | Cool Classics |
| Technical docs | 0 | Neutral Default |
| Colorful/lectures | 5 | Mixed Berry Blue |
| Hand-drawn feel | Use `--sketch` flag | Sketch mode |

### Diagram Type Selection Guide
| Need | D2 Shape/Feature |
|------|-----------------|
| System architecture | Containers + rectangles + connections |
| Database schema | `shape: sql_table` |
| API flow | `shape: sequence_diagram` |
| Class hierarchy | `shape: class` |
| Process flow | Rectangles + diamonds + directed connections |
| Comparison matrix | Grid diagram (`grid-rows`, `grid-columns`) |
| Cloud infra | Containers + `shape: cloud` + `shape: cylinder` |
| User journey | `shape: person` + directed connections |

## Common Patterns

### Architecture Diagram
```d2
direction: down
gateway: "Gateway" {
  style.fill: "#E8F4FD"
  style.stroke: "#1A73E8"
  style.border-radius: 8
  component_a: "Component A" { style.fill: "#FFF3E0"; style.stroke: "#F57C00" }
  component_b: "Component B" { style.fill: "#FFF3E0"; style.stroke: "#F57C00" }
}
external: "External Service" { style.fill: "#E8F5E9"; style.stroke: "#388E3C" }
gateway.component_a -> external: "API call"
```

### Process Flow
```d2
direction: right
start: "Start" { shape: circle; style.fill: "#4CAF50"; style.font-color: white }
process: "Process Data"
decision: "Valid?" { shape: diamond }
success: "Done" { shape: circle; style.fill: "#4CAF50"; style.font-color: white }
error: "Error" { shape: rectangle; style.fill: "#FFEBEE"; style.stroke: "#C62828" }
start -> process -> decision
decision -> success: "Yes"
decision -> error: "No"
error -> process: "Retry"
```

### Concept Explanation (Lecture Style)
```d2
direction: down
classes: {
  main: { style.fill: "#E3F2FD"; style.stroke: "#1565C0"; style.border-radius: 8; style.font-size: 16 }
  sub: { style.fill: "#FFF8E1"; style.stroke: "#F9A825"; style.border-radius: 6 }
}
concept: "Main Concept" { class: main }
detail_a: "Detail A" { class: sub }
detail_b: "Detail B" { class: sub }
detail_c: "Detail C" { class: sub }
concept -> detail_a
concept -> detail_b
concept -> detail_c
```

## CLI Quick Reference

```bash
# Basic PNG (recommended for DOCX insertion)
d2 --theme 1 --pad 40 input.d2 output.png

# SVG (for web/HTML)
d2 --theme 1 input.d2 output.svg

# Hand-drawn style
d2 --sketch --theme 1 input.d2 output.png

# High resolution
d2 --scale 2 --theme 1 input.d2 output.png

# List available themes
d2 themes
```

## Dependencies
- **d2**: Install via `brew install d2` (macOS) or see https://d2lang.com/tour/install
