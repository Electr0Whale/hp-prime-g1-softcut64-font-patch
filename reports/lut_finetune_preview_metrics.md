# LUT Fine-Tune Preview Metrics

Simulator-only metrics from four dense Chinese app-label ROIs.

| Variant | Avg foreground | Avg midtone | Avg dark | Avg solid | Max blackish component |
| --- | ---: | ---: | ---: | ---: | ---: |
| `baseline` | 0.3334 | 0.8062 | 0.3746 | 0.1129 | 44 |
| `softcut64` | 0.2727 | 0.8629 | 0.4577 | 0.1371 | 44 |
| `lut24_ease140` | 0.304 | 0.6365 | 0.5366 | 0.3144 | 112 |
| `lut32_ease135` | 0.2938 | 0.6454 | 0.524 | 0.3064 | 112 |
| `lut32_ease150` | 0.2949 | 0.6156 | 0.5618 | 0.3397 | 112 |
| `lut32_ease170` | 0.2955 | 0.5899 | 0.598 | 0.3805 | 112 |
| `lut40_ease150` | 0.285 | 0.6211 | 0.5655 | 0.3422 | 112 |

Lower midtone usually means less gray fringe.  Higher dark/solid usually means
heavier strokes.  Larger blackish components are a warning sign for blockiness
or stroke sticking.

## Short Read

`lut32_ease135` is the conservative refinement; `lut32_ease150` remains the
balanced middle; `lut32_ease170` is visibly harder.  `lut24_ease140` keeps more
edge coverage and is the most natural-looking of the new set, while
`lut40_ease150` trims more fringe and moves closer to a sharper LCD-tuned look.
