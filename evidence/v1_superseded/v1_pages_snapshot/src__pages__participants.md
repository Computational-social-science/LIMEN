---
title: "Participants"
---

# Participant Analysis

Detailed view of individual participant performance across all sessions.

```js
import { getParticipantStats, loadKeystrokeData } from "../data/keystroke.js";
import * as Plot from "@observablehq/plot";
import * as d3 from "d3";
```

```js
const participantStats = await getParticipantStats();
const allData = await loadKeystrokeData();
```

## Participant Selector

```js
const participantIds = Array.from(new Set(allData.map(d => d.participant_id))).sort(d3.ascending);
const selectedParticipant = view(Inputs.select(participantIds, { label: "Select Participant:", value: participantIds[0] }));
```

```js
const participantData = allData.filter(d => d.participant_id === selectedParticipant);
const pStats = participantStats.find(d => d.participant_id === selectedParticipant);
```

## Summary for Participant ${selectedParticipant}

<div class="grid grid-cols-4" style="margin-bottom: 1rem;">
  <div class="card">
    <h2>${pStats.sessions}</h2>
    <p>Sessions</p>
  </div>
  <div class="card">
    <h2>${pStats.avgWpm.toFixed(1)}</h2>
    <p>Avg WPM</p>
  </div>
  <div class="card">
    <h2>${pStats.avgErrorRate.toFixed(3)}</h2>
    <p>Avg Error Rate</p>
  </div>
  <div class="card">
    <h2>${pStats.totalKeystrokes.toLocaleString()}</h2>
    <p>Total Keystrokes</p>
  </div>
</div>

<div class="grid grid-cols-2" style="margin-bottom: 1rem;">
  <div class="card">
    <h2>${pStats.avgIkiMean.toFixed(1)} ms</h2>
    <p>Avg IKI</p>
  </div>
  <div class="card">
    <h2>${pStats.avgHoldMean.toFixed(1)} ms</h2>
    <p>Avg Hold</p>
  </div>
</div>

## Session Timeline

```js
Plot.plot({
  title: `Session Performance Over Time - Participant ${selectedParticipant}`,
  width: 800,
  height: 400,
  x: { label: "Session Index", grid: true },
  y: { label: "WPM", grid: true },
  marks: [
    Plot.line(participantData, { x: d => participantData.indexOf(d), y: "wpm", stroke: "steelblue", strokeWidth: 2 }),
    Plot.dot(participantData, { x: d => participantData.indexOf(d), y: "wpm", fill: "steelblue", r: 3 })
  ]
})
```

## Distributions for This Participant

```js
const wpmValues = participantData.map(d => d.wpm).filter(d => !isNaN(d));
const errorValues = participantData.map(d => d.error_rate).filter(d => !isNaN(d));
const ikiValues = participantData.map(d => d.iki_mean_ms).filter(d => !isNaN(d));
```

<div class="grid grid-cols-2" style="margin-bottom: 1rem;">
  <div>
    ${Plot.plot({
      title: "WPM Distribution",
      width: 400,
      height: 300,
      x: { label: "WPM", grid: true },
      y: { label: "Count", grid: true },
      marks: [
        Plot.binX({ y: "count" }, wpmValues, { thresholds: 30, fill: "steelblue", opacity: 0.7 }),
        Plot.ruleY([0])
      ]
    })}
  </div>
  <div>
    ${Plot.plot({
      title: "Error Rate Distribution",
      width: 400,
      height: 300,
      x: { label: "Error Rate", grid: true },
      y: { label: "Count", grid: true },
      marks: [
        Plot.binX({ y: "count" }, errorValues, { thresholds: 30, fill: "coral", opacity: 0.7 }),
        Plot.ruleY([0])
      ]
    })}
  </div>
</div>

<div class="grid grid-cols-2">
  <div>
    ${Plot.plot({
      title: "IKI Distribution",
      width: 400,
      height: 300,
      x: { label: "Mean IKI (ms)", grid: true },
      y: { label: "Count", grid: true },
      marks: [
        Plot.binX({ y: "count" }, ikiValues, { thresholds: 30, fill: "seagreen", opacity: 0.7 }),
        Plot.ruleY([0])
      ]
    })}
  </div>
  <div>
    ${Plot.plot({
      title: "Session Duration vs WPM",
      width: 400,
      height: 300,
      x: { label: "Duration (s)", grid: true },
      y: { label: "WPM", grid: true },
      marks: [
        Plot.dot(participantData, { x: "session_duration_s", y: "wpm", fill: "goldenrod", r: 3 }),
        Plot.ruleY([0]),
        Plot.ruleX([0])
      ]
    })}
  </div>
</div>

## Raw Session Data

```js
import { DataTable } from "@observablehq/framework";

DataTable(participantData, {
  columns: [
    { name: "test_section_id", label: "Section" },
    { name: "wpm", label: "WPM", format: ".1f" },
    { name: "error_rate", label: "Error Rate", format: ".3f" },
    { name: "iki_mean_ms", label: "IKI Mean (ms)", format: ".1f" },
    { name: "hold_mean_ms", label: "Hold Mean (ms)", format: ".1f" },
    { name: "n_keystrokes", label: "Keystrokes", format: ",d" },
    { name: "n_backspace", label: "Backspaces", format: ",d" },
    { name: "session_duration_s", label: "Duration (s)", format: ".1f" },
    { name: "sentence_length", label: "Sentence Len" },
    { name: "user_input_length", label: "Input Len" }
  ],
  sortable: true,
  search: true
})
```

## All Participants Overview

```js
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