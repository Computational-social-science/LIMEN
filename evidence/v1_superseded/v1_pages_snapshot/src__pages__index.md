---
title: "Keystroke Observatory Dashboard"
---

# Keystroke Observatory Dashboard

Explore keystroke dynamics from 157K typing sessions across multiple participants and test sections.

```js
import { loadKeystrokeData, getSummaryStats, getParticipantStats, getSectionStats, getDistributions } from "../data/keystroke.js";
import * as Plot from "@observablehq/plot";
import * as d3 from "d3";
```

```js
const summary = await getSummaryStats();
const participantStats = await getParticipantStats();
const sectionStats = await getSectionStats();
const distributions = await getDistributions();
```

## Overview

<div class="grid grid-cols-4" style="margin-bottom: 1rem;">
  <div class="card">
    <h2>${summary.participants.toLocaleString()}</h2>
    <p>Participants</p>
  </div>
  <div class="card">
    <h2>${summary.sessions.toLocaleString()}</h2>
    <p>Sessions</p>
  </div>
  <div class="card">
    <h2>${summary.avgWpm}</h2>
    <p>Avg WPM</p>
  </div>
  <div class="card">
    <h2>${summary.avgErrorRate}</h2>
    <p>Avg Error Rate</p>
  </div>
</div>

<div class="grid grid-cols-2" style="margin-bottom: 1rem;">
  <div class="card">
    <h2>${summary.avgIkiMean} ms</h2>
    <p>Avg IKI (Inter-Key Interval)</p>
  </div>
  <div class="card">
    <h2>${summary.avgHoldMean} ms</h2>
    <p>Avg Hold Duration</p>
  </div>
</div>

## Distributions

### Words Per Minute (WPM)

```js
Plot.plot({
  title: "WPM Distribution",
  width: 800,
  height: 300,
  x: { label: "WPM", grid: true },
  y: { label: "Count", grid: true },
  marks: [
    Plot.binX({ y: "count" }, distributions.wpm, { thresholds: 50, fill: "steelblue", opacity: 0.7 }),
    Plot.ruleY([0])
  ]
})
```

### Error Rate

```js
Plot.plot({
  title: "Error Rate Distribution",
  width: 800,
  height: 300,
  x: { label: "Error Rate", grid: true },
  y: { label: "Count", grid: true },
  marks: [
    Plot.binX({ y: "count" }, distributions.errorRate, { thresholds: 50, fill: "coral", opacity: 0.7 }),
    Plot.ruleY([0])
  ]
})
```

### Inter-Key Interval (IKI) Mean

```js
Plot.plot({
  title: "Mean IKI Distribution",
  width: 800,
  height: 300,
  x: { label: "Mean IKI (ms)", grid: true },
  y: { label: "Count", grid: true },
  marks: [
    Plot.binX({ y: "count" }, distributions.ikiMean, { thresholds: 50, fill: "seagreen", opacity: 0.7 }),
    Plot.ruleY([0])
  ]
})
```

### Hold Duration Mean

```js
Plot.plot({
  title: "Mean Hold Duration Distribution",
  width: 800,
  height: 300,
  x: { label: "Mean Hold (ms)", grid: true },
  y: { label: "Count", grid: true },
  marks: [
    Plot.binX({ y: "count" }, distributions.holdMean, { thresholds: 50, fill: "goldenrod", opacity: 0.7 }),
    Plot.ruleY([0])
  ]
})
```

## By Participant

### Top 20 Participants by WPM

```js
const topParticipants = participantStats.slice(0, 20);
```

```js
Plot.plot({
  title: "Top 20 Participants by Average WPM",
  width: 800,
  height: 500,
  x: { label: "Average WPM", grid: true },
  y: { 
    label: "Participant ID", 
    domain: topParticipants.map(d => d.participant_id).reverse(),
    grid: true 
  },
  marks: [
    Plot.barX(topParticipants, { x: "avgWpm", y: "participant_id", fill: "steelblue", opacity: 0.7, sort: { x: "-y" } }),
    Plot.ruleX([0])
  ]
})
```

### Participant Statistics Table

```js
import { DataTable } from "@observablehq/framework";

DataTable(participantStats, {
  columns: [
    { name: "participant_id", label: "Participant" },
    { name: "sessions", label: "Sessions", format: ",d" },
    { name: "avgWpm", label: "Avg WPM", format: ".1f" },
    { name: "avgErrorRate", label: "Avg Error Rate", format: ".3f" },
    { name: "avgIkiMean", label: "Avg IKI (ms)", format: ".1f" },
    { name: "avgHoldMean", label: "Avg Hold (ms)", format: ".1f" },
    { name: "totalKeystrokes", label: "Total Keystrokes", format: ",d" },
    { name: "totalBackspaces", label: "Total Backspaces", format: ",d" }
  ],
  sortable: true,
  search: true
})
```

## By Test Section

### Section Performance

```js
Plot.plot({
  title: "Average WPM by Test Section",
  width: 800,
  height: 300,
  x: { label: "Test Section", type: "band", domain: sectionStats.map(d => d.test_section_id) },
  y: { label: "Average WPM", grid: true },
  marks: [
    Plot.barY(sectionStats, { x: "test_section_id", y: "avgWpm", fill: "steelblue", opacity: 0.7 }),
    Plot.ruleY([0])
  ]
})
```

```js
Plot.plot({
  title: "Average Error Rate by Test Section",
  width: 800,
  height: 300,
  x: { label: "Test Section", type: "band", domain: sectionStats.map(d => d.test_section_id) },
  y: { label: "Average Error Rate", grid: true },
  marks: [
    Plot.barY(sectionStats, { x: "test_section_id", y: "avgErrorRate", fill: "coral", opacity: 0.7 }),
    Plot.ruleY([0])
  ]
})
```

### Section Statistics Table

```js
DataTable(sectionStats, {
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

## Correlations

### WPM vs Error Rate

```js
const allData = await loadKeystrokeData();
```

```js
Plot.plot({
  title: "WPM vs Error Rate (all sessions)",
  width: 800,
  height: 400,
  x: { label: "WPM", grid: true },
  y: { label: "Error Rate", grid: true },
  marks: [
    Plot.dot(allData, { x: "wpm", y: "error_rate", fill: "steelblue", opacity: 0.1, r: 2 }),
    Plot.ruleY([0]),
    Plot.ruleX([0])
  ]
})
```

### IKI vs WPM

```js
Plot.plot({
  title: "Mean IKI vs WPM (all sessions)",
  width: 800,
  height: 400,
  x: { label: "Mean IKI (ms)", grid: true },
  y: { label: "WPM", grid: true },
  marks: [
    Plot.dot(allData, { x: "iki_mean_ms", y: "wpm", fill: "seagreen", opacity: 0.1, r: 2 }),
    Plot.ruleY([0]),
    Plot.ruleX([0])
  ]
})
```

### Session Duration vs WPM

```js
Plot.plot({
  title: "Session Duration vs WPM",
  width: 800,
  height: 400,
  x: { label: "Session Duration (s)", grid: true },
  y: { label: "WPM", grid: true },
  marks: [
    Plot.dot(allData, { x: "session_duration_s", y: "wpm", fill: "goldenrod", opacity: 0.1, r: 2 }),
    Plot.ruleY([0]),
    Plot.ruleX([0])
  ]
})
```