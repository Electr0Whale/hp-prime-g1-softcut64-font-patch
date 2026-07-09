# Round3 Preview Metrics

These metrics are from simulator screenshots only.  They are useful for ranking
candidate directions, not as a substitute for real LCD validation.

## Aggregate Metrics

| Variant | Avg foreground ratio | Avg midtone ratio | Avg dark ratio | Max blackish component |
| --- | ---: | ---: | ---: | ---: |
| `baseline` | 0.3334 | 0.8062 | 0.3746 | 44 |
| `softcut64` | 0.2727 | 0.8629 | 0.4577 | 44 |
| `boost48_125` | 0.2896 | 0.528 | 0.621 | 156 |
| `boost48_150` | 0.2896 | 0.3904 | 0.719 | 280 |
| `lut32_ease150` | 0.2949 | 0.6156 | 0.5618 | 112 |
| `lut48_contrast150` | 0.2792 | 0.5436 | 0.5777 | 120 |

## Reading The Numbers

- Lower midtone ratio generally means less fuzzy gray fringe.
- Higher dark ratio generally means heavier strokes.
- A much larger blackish component can indicate blockiness or stroke sticking.

## Interpretation

`lut32_ease150` sits between `softcut64` and the aggressive variants: it
increases dark stroke coverage without pushing the blackish component as high as
`boost48_150`.  `boost48_150` is the hardest-looking candidate in this set.
`lut48_contrast150` is crisp, but still heavier than `lut32_ease150` in the
dense Chinese ROIs.

## Per-ROI Midtone Ratio

| ROI | `baseline` | `softcut64` | `boost48_125` | `boost48_150` | `lut32_ease150` | `lut48_contrast150` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `label_function` | 0.7833 | 0.8897 | 0.5175 | 0.4056 | 0.6458 | 0.5755 |
| `label_spreadsheet` | 0.766 | 0.7948 | 0.4481 | 0.3278 | 0.5041 | 0.4213 |
| `label_statistics` | 0.8184 | 0.8724 | 0.5304 | 0.3259 | 0.6355 | 0.557 |
| `label_datasampler` | 0.8571 | 0.8949 | 0.6159 | 0.5024 | 0.6769 | 0.6206 |
