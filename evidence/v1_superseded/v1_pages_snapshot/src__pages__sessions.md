---
title: "Sessions"
---

# Session Explorer

Explore individual typing sessions with detailed metrics and visualizations.

```js
import { loadKeystrokeData, getSectionStats } from "../data/keystroke.js";
import * as Plot from "@observablehq/plot";
import * as d3 from "d3";
```

```js
const allData = await loadKeystrokeData();
const sectionStats = await getSectionStats();
```

## Filters

```js
const sections = Array.from(new Set(allData.map(d => d.test_section_id))).sort(d3.ascending);
const selectedSections = view(Inputs.checkbox(sections, { label: "Test Sections:", value: sections }));
```

```js
const minWpm = view(Inputs.range([0, d3.max(allData, d => d.wpm)], { label: "Min WPM:", step: 1, value: 0 }));
const maxWpm = view(Inputs.range([0, d3.max(allData, d => d.wpm)], { label: "Max WPM:", step: 1, value: d3.max(allData, d => d.wpm) }));
```

```js
const filteredData = allData.filter(d => 
  selectedSections.includes(d.test_section_id) &&
  d.wpm >= minWpm && d.wpm <= maxWpm
);
```

**Showing ${filteredData.length.toLocaleString()} of ${allData.length.toLocaleString()} sessions**

## Session Metrics

<div class="grid grid-cols-4" style="margin-bottom: 1rem;">
  <div class="card">
    <h2>${filteredData.length.toLocaleString()}</h2>
    <p>Sessions</p>
  </div>
  <div class="card">
    <h2>${d3.mean(filteredData, d => d.wpm).toFixed(1)}</h2>
    <p>Avg WPM</p>
  </div>
  <div class="card">
    <h2>${d3.mean(filteredData, d => d.error_rate).toFixed(3)}</h2>
    <p>Avg Error Rate</p>
  </div>
  <div class="card">
    <h2>${d3.mean(filteredData, d => d.iki_mean_ms).toFixed(1)} ms</h2>
    <p>Avg IKI</p>
  </div>
</div>

## Scatter Plot Matrix

```js
const dimensions = [
  { key: "wpm", label: "WPM" },
  { key: "error_rate", label: "Error Rate" },
  { key: "iki_mean_ms", label: "IKI Mean (ms)" },
  { key: "hold_mean_ms", label: "Hold Mean (ms)" },
  { key: "session_duration_s", label: "Duration (s)" },
  { key: "n_keystrokes", label: "Keystrokes" }
];
```

```js
const n = dimensions.length;
const size = 200;
const padding = 10;

Plot.plot({
  width: n * size + padding * (n - 1),
  height: n * size + padding * (n - 1),
  marginLeft: 40,
  marginBottom: 40,
  marks: dimensions.flatMap((x, i) => 
    dimensions.map((y, j) => {
      if (i === j) return Plot.text(filteredData, { 
        x: (size * i + padding * i + size / 2), 
        y: (size * j + padding * j + size / 2), 
        text: x.label, 
        fontSize: 14,
        fontWeight: "bold"
      });
      if (i > j) return Plot.dot(filteredData, { 
        x: (d, i) => d[x.key] ? (d[x.key] - d3.min(filteredData, d => d[x.key])) / (d3.max(filteredData, d => d[x.key]) - d3.min(filteredData, d => d[x.key])) * size + size * i + padding * i : null,
        y: (d, i) => d[y.key] ? (d[y.key] - d3.min(filteredData, d => d[y.key])) / (d3.max(filteredData, d => d[y.key]) - d3.min(filteredData, d => d[y.key])) * size + size * j + padding * j : null,
        fill: "steelblue", opacity: 0.1, r: 1.5
      });
      return null;
    })
  )
})
```

## Distribution Comparison by Section

```js
Plot.plot({
  title: "WPM Distribution by Test Section",
  width: 800,
  height: 400,
  x: { label: "WPM", grid: true },
  y: { label: "Density", grid: true },
  color: { legend: true, scheme: "tableau10" },
  marks: [
    Plot.density(filteredData, { x: "wpm", fill: "test_section_id", opacity: 0.3, bandwidth: 5 })
  ]
})
```

```js
Plot.plot({
  title: "Error Rate Distribution by Test Section",
  width: 800,
  height: 400,
  x: { label: "Error Rate", grid: true },
  y: { label: "Density", grid: true },
  color: { legend: true, scheme: "tableau10" },
  marks: [
    Plot.density(filteredData, { x: "error_rate", fill: "test_section_id", opacity: 0.3, bandwidth: 0.01 })
  ]
})
```

## Box Plots by Section

```js
Plot.plot({
  title: "WPM by Test Section",
  width: 800,
  height: 400,
  x: { label: "Test Section", type: "band", domain: selectedSections },
  y: { label: "WPM", grid: true },
  marks: [
    Plot.boxY(filteredData, { x: "test_section_id", y: "wpm", fill: "test_section_id", opacity: 0.5 }),
    Plot.ruleY([0])
  ]
})
```

```js
Plot.plot({
  title: "Error Rate by Test Section",
  width: 800,
  height: 400,
  x: { label: "Test Section", type: "band", domain: selectedSections },
  y: { label: "Error Rate", grid: true },
  marks: [
    Plot.boxY(filteredData, { x: "test_section_id", y: "error_rate", fill: "test_section_id", opacity: 0.5 }),
    Plot.ruleY([0])
  ]
})
```

## Session Data Table

```js
import { DataTable } from "@observablehq/framework";

DataTable(filteredData, {
  columns: [
    { name: "participant_id", label: "Participant" },
    { name: "test_section_id", label: "Section" },
    { name: "wpm", label: "WPM", format: ".1f" },
    { name: "error_rate", label: "Error Rate", format: ".3f" },
    { name: "iki_mean_ms", label: "IKI Mean (ms)", format: ".1f" },
    { name: "iki_std_ms", label: "IKI Std (ms)", format: ".1f" },
    { name: "hold_mean_ms", label: "Hold Mean (ms)", format: ".1f" },
    { name: "hold_std_ms", label: "Hold Std (ms)", format: ".1f" },
    { name: "n_keystrokes", label: "Keystrokes", format: ",d" },
    { name: "n_chars", label: "Chars", format: ",d" },
    { name: "n_backspace", label: "Backspaces", format: ",d" },
    { name: "n_delete", label: "Deletes", format: ",d" },
    { name: "edits", label: "Edits", format: ",d" },
    { name: "session_duration_s", label: "Duration (s)", format: ".1f" },
    { name: "sentence_length", label: "Sentence Len" },
    { name: "user_input_length", label: "Input Len" }
  ],
  sortable: true,
  search: true
})
```

## Section Summary

```js
DataTable(sectionStats.filter(d => selectedSections.includes(d.test_section_id)), {
  columns: [
    { name: "test_section_id", label: "Test Section" },
    { name: "sessions", label: "Sessions", format: ",d" },
    { name: "avgWpm", label: "Avg WPM", format: ".1f" },
    { name: "avgErrorRate", label: "Avg Error Rate", format: ".3f" },
    { name: "avgIkiMean", label: "Avg IKI (ms)", format: ".1f" },
    { name: "avgHoldMean", label: "Avg Hold (ms)", format: ".1f" },
    { name: "avgSentenceLength", label: "Avg Sentence Length", format: ".1f" },
    { name: "avgUserInputLength", label: "Avg Input Length", format: ".1f" }
  ],
  sortable: true
})
```