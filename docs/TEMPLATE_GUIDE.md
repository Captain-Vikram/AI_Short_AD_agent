# VideoEnhanced Template System

## Overview

The `VideoEnhanced` component is a professional, design-driven template system for creating dynamic infographic-style videos. It uses a configuration-driven approach where all visual properties are controlled through a `DesignSystem` JSON object.

## Architecture

### Core Components

1. **VideoEnhanced.tsx** - Main composition component that orchestrates scene rendering
2. **SceneLayer** - Renders individual scenes with animations, images, and audio
3. **ImageLayer** - Handles image display with fade animations
4. **TextOverlay** - Renders narration text with badges and positioning options
5. **FloatingElement** - Creates animated background shapes with sinusoidal motion
6. **ShapeAccent** - Rotating accent shapes for visual depth

### Animation System

All animations use Remotion's `interpolate` function with easing curves:

- **Fade in/out**: Smooth opacity transitions over 15% of scene duration
- **Floating elements**: Continuous sinusoidal oscillation with phase offset per element
- **Image zoom**: Subtle scale-up from fade-in to fade-out
- **Shape rotation**: Full 360° rotation over scene duration with opacity pulse

## Design Configuration

### DesignSystem Type

```typescript
type DesignSystem = {
  bg_color?: string; // Hex color for background
  accent_color?: string; // Primary highlight color
  text_color?: string; // Narration text color
  secondary_color?: string; // Supporting accent color
  layout?: "fullscreen" | "split" | "picture-in-picture" | "minimalist";
  animation_style?: "subtle" | "dynamic" | "bold";
  floating_elements?: boolean; // Enable animated background shapes
  show_badge?: boolean; // Show/hide scene badges
  text_position?: "bottom" | "center" | "top";
  element_scale?: number; // 0.5–2.0 multiplier for floating elements
  blur_strength?: number; // 0–15 blur intensity
  audio_gain?: number; // 0.5–3.0 audio volume
  [key: string]: unknown; // Allow custom properties
};
```

### Color Guidelines

**Contrast Requirements:**

- Accent color must have strong contrast with background (WCAG AA minimum)
- Text color must be highly readable on background
- Secondary color should complement accent without clashing

**Common Palettes:**

| Theme        | BG      | Accent  | Text    | Secondary |
| ------------ | ------- | ------- | ------- | --------- |
| Dark Tech    | #0c0f1a | #0ea5e9 | #f1f5f9 | #1e293b   |
| Warm Product | #faf5f0 | #f1635c | #1f2937 | #fed7aa   |
| Corporate    | #f8fafc | #2563eb | #0f172a | #e2e8f0   |
| Gaming       | #0d0221 | #00d4ff | #ffff00 | #3d0c66   |

### Animation Styles

**Subtle:**

- Minimal floating element movement
- Slow fade animations
- Lower element_scale (0.8–1.0)
- Lower blur_strength (3–6)
- Best for: Corporate, educational, professional content

**Dynamic:**

- Moderate floating element movement
- Standard fade animations
- Medium element_scale (1.2–1.5)
- Medium blur_strength (6–10)
- Best for: Marketing, product launches, energetic messaging

**Bold:**

- Aggressive floating element movement
- Fast-paced animations
- High element_scale (1.6–2.0)
- Higher blur_strength (10–15)
- Best for: Gaming, fitness, entertainment, urgency-driven content

### Text Positioning

- **Bottom**: Default, overlays text over lower part of image
- **Center**: Text centered on screen, overlaid on image
- **Top**: Text positioned at top, suitable for landscape layouts

## Creating Custom Designs

### Step 1: Choose a Base Palette

Start with a color scheme:

```json
{
  "bg_color": "#0c0f1a",
  "accent_color": "#0ea5e9",
  "text_color": "#f1f5f9",
  "secondary_color": "#1e293b"
}
```

### Step 2: Select Animation Style

Match to your content:

```json
{
  "animation_style": "dynamic",
  "floating_elements": true,
  "element_scale": 1.4
}
```

### Step 3: Configure Layout & Text

```json
{
  "layout": "fullscreen",
  "text_position": "bottom",
  "show_badge": true
}
```

### Step 4: Tune Effects

```json
{
  "blur_strength": 8,
  "audio_gain": 1.4
}
```

## Rendering with Designs

### Using the Designer Agent

Automatically generate optimized designs:

```powershell
python agents.py designer --script script.json --design video_design.json
```

The Designer agent will:

1. Analyze script content and themes
2. Choose appropriate color schemes
3. Select matching animation style
4. Generate complete design specification

### Manual Rendering

Render with a specific design:

```powershell
python agents.py render --props remotion_props.json --design video_design.json
```

### Modifying Designs

Edit `video_design.json` and re-render:

```json
{
  "bg_color": "#0c0f1a",
  "accent_color": "#0ea5e9",
  "animation_style": "bold",
  "element_scale": 1.8
}
```

Then render again without regenerating assets.

## Advanced Customization

### Adding Custom Design Properties

The `DesignSystem` type allows custom properties via `[key: string]: unknown`. You can add:

```json
{
  "custom_font": "Poppins",
  "custom_spacing": 24,
  "gradient_angle": 135,
  "particle_count": 6
}
```

And access them in component code (for future enhancements).

### Extending Floating Elements

Modify `element_scale` to control floating element size:

- 0.5–0.8: Subtle, corporate
- 1.0–1.4: Standard, energetic
- 1.5–2.0: Bold, eye-catching

### Audio Gain Tuning

Adjust `audio_gain` to match video loudness:

- 0.5–0.8: Quiet background
- 1.0–1.4: Standard volume (default 1.4)
- 1.5–2.0: Loud, forward
- 2.0–3.0: Very loud (risk of clipping)

### Blur Strength Effects

`blur_strength` creates depth and focus:

- 0–3: Sharp, minimal depth
- 4–8: Balanced, moderate depth
- 9–12: Soft, cinematic feel
- 13–15: Heavy blur, artistic

## Examples

### Tech SaaS Ad

```json
{
  "bg_color": "#0c0f1a",
  "accent_color": "#0ea5e9",
  "text_color": "#f1f5f9",
  "secondary_color": "#1e293b",
  "animation_style": "dynamic",
  "floating_elements": true,
  "element_scale": 1.5,
  "blur_strength": 10,
  "audio_gain": 1.4
}
```

### Luxury Product

```json
{
  "bg_color": "#0a0e27",
  "accent_color": "#d4af37",
  "text_color": "#f5f5f5",
  "secondary_color": "#1a1f3a",
  "animation_style": "subtle",
  "floating_elements": true,
  "show_badge": false,
  "element_scale": 0.9,
  "blur_strength": 8,
  "audio_gain": 1.2
}
```

### Fitness/Energy

```json
{
  "bg_color": "#0f0a05",
  "accent_color": "#ff6b35",
  "text_color": "#fffbf0",
  "secondary_color": "#2d1810",
  "animation_style": "bold",
  "floating_elements": true,
  "element_scale": 2.0,
  "blur_strength": 12,
  "audio_gain": 1.5
}
```

## Performance Considerations

- **Floating elements**: 4 floating circles per scene, each with sinusoidal animation
- **Shape accents**: 2 rotating shapes with opacity pulse
- **Frame rate**: 30 fps (standard for videos)
- **Resolution**: Configurable via VIDEO_WIDTH/VIDEO_HEIGHT in .env

For longer videos or lower-end devices, consider:

- Setting `floating_elements: false`
- Using `animation_style: "subtle"`
- Reducing `blur_strength`

## Troubleshooting

**Colors look washed out:**

- Increase contrast between `bg_color` and `accent_color`
- Use pure colors (#0000ff) rather than muted ones
- Check WCAG contrast ratios

**Text is hard to read:**

- Change `text_position` to improve composition
- Increase `blur_strength` to separate text from background
- Use brighter `text_color` or darker `bg_color`

**Animations feel stiff:**

- Increase `animation_style` from "subtle" to "dynamic" or "bold"
- Raise `element_scale` for larger, more visible motion
- Reduce scene durations for faster pacing

**Audio too quiet/loud:**

- Adjust `audio_gain` (1.4 is default)
- Check system volume
- Re-generate audio with higher/lower TTS gain settings

## Next Steps

- Review [design_system_examples.json](./design_system_examples.json) for preset designs
- Run the Designer agent to auto-generate optimized designs
- Experiment with custom designs and share what works!
