import * as d3 from "d3";

/**
 * Load keystroke session statistics from Parquet file.
 * Returns an array of objects with all 25 columns.
 */
export async function loadKeystrokeData() {
  const data = await FileAttachment("keystroke_session_stats.parquet").parquet();
  return data;
}

/**
 * Get summary statistics for the dashboard.
 */
export async function getSummaryStats() {
  const data = await loadKeystrokeData();
  
  const participants = new Set(data.map(d => d.participant_id)).size;
  const sessions = data.length;
  const avgWpm = d3.mean(data, d => d.wpm);
  const avgErrorRate = d3.mean(data, d => d.error_rate);
  const avgIkiMean = d3.mean(data, d => d.iki_mean_ms);
  const avgHoldMean = d3.mean(data, d => d.hold_mean_ms);
  
  return {
    participants,
    sessions,
    avgWpm: Math.round(avgWpm * 10) / 10,
    avgErrorRate: Math.round(avgErrorRate * 1000) / 1000,
    avgIkiMean: Math.round(avgIkiMean * 10) / 10,
    avgHoldMean: Math.round(avgHoldMean * 10) / 10
  };
}

/**
 * Get data grouped by participant.
 */
export async function getParticipantStats() {
  const data = await loadKeystrokeData();
  
  const byParticipant = d3.rollup(
    data,
    v => ({
      sessions: v.length,
      avgWpm: d3.mean(v, d => d.wpm),
      avgErrorRate: d3.mean(v, d => d.error_rate),
      avgIkiMean: d3.mean(v, d => d.iki_mean_ms),
      avgHoldMean: d3.mean(v, d => d.hold_mean_ms),
      totalKeystrokes: d3.sum(v, d => d.n_keystrokes),
      totalBackspaces: d3.sum(v, d => d.n_backspace)
    }),
    d => d.participant_id
  );
  
  return Array.from(byParticipant, ([participant_id, stats]) => ({
    participant_id,
    ...stats
  })).sort((a, b) => d3.descending(a.avgWpm, b.avgWpm));
}

/**
 * Get data grouped by test section.
 */
export async function getSectionStats() {
  const data = await loadKeystrokeData();
  
  const bySection = d3.rollup(
    data,
    v => ({
      sessions: v.length,
      avgWpm: d3.mean(v, d => d.wpm),
      avgErrorRate: d3.mean(v, d => d.error_rate),
      avgIkiMean: d3.mean(v, d => d.iki_mean_ms),
      avgHoldMean: d3.mean(v, d => d.hold_mean_ms),
      avgSentenceLength: d3.mean(v, d => d.sentence_length),
      avgUserInputLength: d3.mean(v, d => d.user_input_length)
    }),
    d => d.test_section_id
  );
  
  return Array.from(bySection, ([test_section_id, stats]) => ({
    test_section_id,
    ...stats
  })).sort((a, b) => d3.ascending(a.test_section_id, b.test_section_id));
}

/**
 * Get distribution data for histograms.
 */
export async function getDistributions() {
  const data = await loadKeystrokeData();
  
  return {
    wpm: data.map(d => d.wpm).filter(d => !isNaN(d)),
    errorRate: data.map(d => d.error_rate).filter(d => !isNaN(d)),
    ikiMean: data.map(d => d.iki_mean_ms).filter(d => !isNaN(d)),
    holdMean: data.map(d => d.hold_mean_ms).filter(d => !isNaN(d)),
    sentenceLength: data.map(d => d.sentence_length),
    keystrokes: data.map(d => d.n_keystrokes),
    backspaces: data.map(d => d.n_backspace)
  };
}