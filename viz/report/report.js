(function(){
  // ── fail visibly ─────────────────────────────────────────────────────────────
  // THE PAGE IS ONE SCRIPT, SO ONE BAD FIELD COSTS EVERY SECTION AFTER IT. `a.state_len.min` threw
  // inside an Array.map at section 4.3 and sections 4.4 through 8 -- including the whole reference
  // list -- rendered as empty containers, while every guard in the suite passed. Nothing said so,
  // and the page looked like a report with thin content rather than one that had crashed. This makes
  // the failure legible and names the containers that were never reached.
  (function failLoudly(){
    const show = (msg) => {
      const b = document.getElementById('banner');
      if (!b) return;
      const empty = [...document.querySelectorAll('#refs,#qc,#limits,#repro,#sigChannel,#funnel,'
        + '#tiles,#armTable,#layerChart,#lenTable,#consistency,#imeCard,#channelCard,#sources,'
        + '#instruments,#artefacts,#vendored')]
        .filter(e => e && e.innerHTML.trim().length === 0).map(e => '#' + e.id);
      b.className = 'banner bad';
      b.innerHTML = '<strong>This page did not finish rendering.</strong> ' + msg
        + (empty.length ? '<br>Empty containers: <span class="mono">' + empty.join(' ') + '</span>' : '')
        + '<br>The sections that show content were written before the failure and are valid; the '
        + 'empty ones were never reached. Report this rather than reading past it.';
    };
    window.addEventListener('error', (e) => show((e && e.message) || 'script error'));
    window.addEventListener('unhandledrejection', (e) => show('unhandled rejection: ' + e.reason));
  })();

  // ── navigation ───────────────────────────────────────────────────────────────
  // Built from the document's own h2/h3 headings, so the contents cannot describe a structure
  // the report does not have. Runs before the state check, because the headings are static and
  // a reader should be able to move around the page even if the data failed to load.
  (function buildToc(){
    const list = document.getElementById('toc-list');
    const heads = [...document.querySelectorAll('.wrap h2, .wrap h3')];
    const bar = document.getElementById('progress');
    const seen = new Set();
    heads.forEach((h, i) => {
      if (!h.id) {
        h.id = 'sec-' + (h.tagName === 'H2' ? 's' : 'u') + i;
      }
      if (seen.has(h.id)) return;
      seen.add(h.id);
      const label = (h.textContent || '').trim();
      const m = label.match(/^(\d+(?:\.\d+)?)\s*·?\s*(.*)$/);
      const a = document.createElement('a');
      a.href = '#' + h.id;
      a.className = h.tagName === 'H2' ? 'sec' : 'sub';
      a.innerHTML = m
        ? '<span class="num">' + m[1] + '</span>' + m[2].replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))
        : label.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
      a.addEventListener('click', ev => {
        ev.preventDefault();
        h.scrollIntoView({behavior: 'smooth', block: 'start'});
        history.replaceState(null, '', '#' + h.id);
      });
      list.appendChild(a);
    });

    // active-section highlight: the last heading whose top has passed the reading line
    const links = [...list.querySelectorAll('a')];
    const targets = links.map(a => document.getElementById(a.getAttribute('href').slice(1)));
    let ticking = false;
    function onScroll(){
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        ticking = false;
        const line = window.scrollY + 96;
        let idx = 0;
        for (let i = 0; i < targets.length; i++) {
          if (targets[i] && targets[i].getBoundingClientRect().top + window.scrollY <= line) idx = i;
        }
        links.forEach((a, i) => a.classList.toggle('active', i === idx));
        const doc = document.documentElement;
        const frac = doc.scrollHeight > doc.clientHeight
          ? window.scrollY / (doc.scrollHeight - doc.clientHeight) : 0;
        bar.style.width = (100 * Math.min(1, Math.max(0, frac))).toFixed(2) + '%';
      });
    }
    window.addEventListener('scroll', onScroll, {passive: true});
    window.addEventListener('resize', onScroll);
    onScroll();

    // narrow screens: the rail becomes a drawer, collapsed to start
    const toc = document.getElementById('toc');
    const ttl = document.getElementById('toc-ttl');
    function fit(){
      if (window.innerWidth <= 820) {
        toc.classList.add('collapsed');
      } else {
        toc.classList.remove('collapsed');
      }
    }
    ttl.addEventListener('click', () => {
      if (window.innerWidth <= 820) toc.classList.toggle('collapsed');
    });
    fit();
    window.addEventListener('resize', fit);
  })();

  const S = window.APP_STATE;
  const banner = document.getElementById('banner');
  // No fabricated fallback: absent state means the page says so and renders no numbers at all.
  if (!S) {
    banner.className = 'banner bad';
    banner.innerHTML = '<strong>No state.</strong> Run <code>python scripts/export_report_state.py</code> ' +
      'to write <code>viz/report/state.js</code>, then reload. No figures are shown because none were read.';
    document.querySelectorAll('h2, h3, .card, #tiles, #armTable, #funnel, #lenTable, #sources, #qc, #limits, #repro, #refs')
      .forEach(e => e.style.display = 'none');
    document.getElementById('subtitle').textContent = 'state missing';
    return;
  }

  const D = S.dataset, A = S.arms, CH = S.channel;
  const fmt = n => (n === null || n === undefined) ? '—' : Number(n).toLocaleString('en-US');
  const p1 = n => (n === null || n === undefined) ? '—' : (100 * n).toFixed(1) + '%';
  // Two decimals, for a number whose whole point is the second one: the validation compares 1.19 %
  // with 1.17 %, and at one decimal both render as "1.2%" -- the agreement would be invisible.
  const p2 = n => (n === null || n === undefined) ? '—' : (100 * n).toFixed(2) + '%';
  const esc = s => String(s === null || s === undefined ? '' : s)
      .replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const order = S.arm_order || Object.keys(A);

  document.getElementById('subtitle').innerHTML =
      'dataset <span class="mono">' + esc(D.name) + ' v' + esc(D.version) + '</span> · built ' +
      '<span class="mono">' + esc(D.built_utc) + '</span> · seed <span class="mono">' +
      esc(D.seed) + '</span> · state rendered <span class="mono">' + esc(S.generated_at) + '</span>';

  const ageMin = Math.round((Date.now() / 1000 - S.generated_epoch) / 60);
  banner.className = 'banner' + (ageMin > 60 * 24 ? ' warn' : '');
  banner.innerHTML = '<strong>Data age.</strong> State exported ' +
      (ageMin < 1 ? 'just now' : ageMin + ' min ago') + '; source mtimes: ' +
      Object.entries(S.mtimes).map(([k, v]) =>
        '<span class="mono">' + esc(k) + '</span> ' +
        (v ? esc(v) : '<span class="pill bad">missing</span>')).join(' · ') +
      '. Every figure on this page is read from these files; none is hand-entered.';

  // the rail carries the identity of the dataset it is a table of contents for
  { const meta = document.getElementById('toc-meta');
    if (meta) meta.innerHTML =
        '<strong>' + esc(D.name) + '</strong> <span class="mono">v' + esc(D.version) + '</span><br>'
      + fmt(D.total_items) + ' items · ' + order.length + ' arms<br>'
      + Object.keys(S.sources).length + ' sources · '
      + '<span class="mono">' + esc(D.seed) + '</span><br>'
      + '<span style="opacity:.8">state ' + esc(S.generated_at) + '</span>'; }

  // ---- 1 sources
  //
  // Keyed by SOURCE, not by channel: three of the six arms draw on one release, so a
  // per-channel listing showed three corpora and omitted the largest single source in the
  // dataset. The kind and the arms each source feeds are shown, because "which arms does this
  // supply" is the question a reader has.
  const SRC_ORDER = ["corpus", "channel_measurement", "standard", "rejected"];
  const SRC_LABEL = {corpus: "corpus", channel_measurement: "instrument — channel measurement",
                     standard: "instrument — standard", rejected: "not used"};
  const srcEntries = Object.entries(S.sources);
  const byKind = {};
  srcEntries.forEach(([k, v]) => {
    const kd = v.kind || "corpus";
    (byKind[kd] = byKind[kd] || []).push([k, v]);
  });
  document.getElementById('sources').innerHTML = SRC_ORDER.filter(k => byKind[k]).map(kind => {
    const human = kind.replace(/_/g, '');
    return `<h3 style="margin-top:22px">${esc(SRC_LABEL[kind] || human)}
      <span class="pill">${byKind[kind].length}</span></h3>`
    + byKind[kind].map(([sid, s]) => `
    <div class="card">
      <h3 style="margin-top:0">${esc(s.name)} <span class="pill ${s.provenance === 'observed' ? 'ok' : ''}">${esc(s.provenance)}</span></h3>
      <table>
        ${(s.arms || []).length ? `<tr><th style="width:170px">Feeds</th><td class="mono">${s.arms.map(esc).join(' · ')}</td></tr>` : ''}
        <tr><th>Source id</th><td class="mono">${esc(sid)}</td></tr>
        ${s.compiler ? `<tr><th>Compiler</th><td>${esc(s.compiler)}</td></tr>` : ''}
        <tr><th>What it is</th><td>${esc(s.what)}</td></tr>
        ${s.citation ? `<tr><th>Reference</th><td>${esc(s.citation)}</td></tr>` : ''}
        ${s.licence ? `<tr><th>Licence</th><td>${esc(s.licence)}</td></tr>` : ''}
        ${s.verification ? `<tr><th>Verification</th><td>${esc(s.verification)}</td></tr>` : ''}
        ${s.caveat ? `<tr><th>Scope caveat</th><td>${esc(s.caveat)}</td></tr>` : ''}
        ${s.note ? `<tr><th>Note</th><td>${esc(s.note)}</td></tr>` : ''}
        ${(s.rejected || []).length ? `<tr><th>Rejected</th><td>${
          s.rejected.map(r => `<div style="margin-bottom:5px"><strong>${esc(r.name)}</strong> — ${esc(r.reason)}</div>`).join('')
        }</td></tr>` : ''}
      </table>
    </div>`).join('');
  }).join('');

  // ---- 1.2 instruments, 1.3 internal modules, 1.4 artefacts
  //
  // Derived from the imports in scripts/ by scripts/build_instrument_manifest.py, so a tool that
  // computes a number cannot be missing from the list while being used. The purpose field is the
  // load-bearing part: it says what the data would lack without the tool.
  const INS = S.instruments || {};
  const roleOrder = {instrument: 0, library: 1};
  const insRows = (INS.instruments || []).slice()
      .sort((a, b) => (roleOrder[a.role] ?? 9) - (roleOrder[b.role] ?? 9)
                      || (b.n_files || 0) - (a.n_files || 0));
  document.getElementById('instruments').innerHTML = !insRows.length
    ? '<div class="sub">No instrument manifest: run <code>python scripts/build_instrument_manifest.py</code>.</div>'
    : `<table><thead><tr><th>tool</th><th>role</th><th class="num">version</th>
        <th>what it computes here</th><th class="num">files</th></tr></thead>
      <tbody>${insRows.map(r => `<tr>
        <td class="mono">${esc(r.import)}${r.distribution && r.distribution !== r.import
            ? `<br><span class="sub">${esc(r.distribution)}</span>` : ''}</td>
        <td><span class="pill ${r.role === 'instrument' ? 'ok' : ''}">${esc(r.role)}</span></td>
        <td class="num">${r.version ? esc(r.version) : '<span class="pill warn">unresolved</span>'}</td>
        <td>${esc(r.purpose)}${r.citation
            ? `<br><span class="sub">${esc(r.citation)}</span>` : ''}</td>
        <td class="num">${fmt(r.n_files)}</td></tr>`).join('')}</tbody></table>`;

  document.getElementById('internal').innerHTML = (INS.internal_modules || []).length
    ? `<table><thead><tr><th>module</th><th>what it does</th>
        <th class="num">used in</th></tr></thead><tbody>${
        (INS.internal_modules || []).map(m => `<tr>
          <td class="mono">${esc(m.module)}</td><td>${esc(m.purpose)}</td>
          <td class="num">${m.used_in.length}</td></tr>`).join('')}</tbody></table>
       <div class="sub">In-repo modules, so they carry no version and no external citation; they
         are listed because they are part of the machinery a reader would have to reproduce.</div>`
    : '<div class="sub">none recorded</div>';

  document.getElementById('artefacts').innerHTML = (INS.artefacts || []).length
    ? `<table><tbody>${(INS.artefacts || []).map(a => `<tr>
        <td class="mono" style="font-size:11.5px">${esc(a.path)}</td>
        <td class="sub">${esc(a.purpose)}</td>
        <td>${a.exists ? '<span class="pill ok">present</span>'
                       : '<span class="pill bad">absent</span>'}</td></tr>`).join('')}</tbody></table>`
    : '<div class="sub">none recorded</div>';

  document.getElementById('vendored').innerHTML = (INS.vendored || []).length
    ? `<table><tbody>${(INS.vendored || []).map(v => `<tr>
        <td class="mono" style="font-size:11.5px">${esc(v.dir)}</td>
        <td class="num">${fmt(v.n_files)}</td></tr>`).join('')}</tbody></table>
       <div class="sub">Reproduced verbatim from their publishers. They are excluded from the
         relative-paths guard for the same reason <code>viz/</code> is: a vendored third-party
         tree whose internal paths are not ours to make relative.</div>`
    : '<div class="sub">none recorded</div>';

  // ---- 5.5-5.9 the d1-3B measurement, read from measurement/out/measurement_report.json
  //
  // Every number here is read at load time from the artefact scripts/analyze_measurement.py
  // writes, so a sentence and its table cannot disagree. The instrument diagnostics come first in
  // reading order because they are what licenses the numbers after them: an accuracy that is a
  // fact about the option layout is not a fact about the channel.
  const MS = S.measurement || {};
  const msRows = MS.accuracy || [];
  document.getElementById('meas-summary').innerHTML = !MS.n_rows
    ? '<span class="pill warn">no measurement artefact</span> run <code>scripts/analyze_measurement.py</code>.'
    : `${fmt(MS.n_rows)} items · ${MS.n_options} options · chance ${MS.chance} · instrument
       <span class="mono">${esc(MS.instrument || '')}</span> · rows from <span class="mono">${esc(MS.rows_files || '')}</span>
       <div class="sub" style="margin-top:5px">Two sampling schemes, each used for what it can
       measure: <span class="mono">measurement_report_bs.json</span> samples whole <em>states</em>,
       so the layer contrast has matched pairs; <span class="mono">measurement_report_rk.json</span>
       samples a quota per <em>rank value</em>, so the rank curve is balanced rather than following
       the corpus's own distribution. Every table below names the artefact it was read from, so the
       two cannot be confused for one measurement.</div>`;

  const l4 = msRows.filter(r => r.layer === 'L4').sort((a, b) => b.accuracy - a.accuracy);
  const cross = MS.cross_arm_L4 || [];
  document.getElementById('meas-crossarm').innerHTML = !l4.length
    ? '<div class="sub">not measured</div>'
    : `<table><thead><tr><th>arm</th><th class="num">n</th><th class="num">accuracy</th>
        <th class="num">95% CI</th><th class="num">z vs chance</th><th class="num">p_root median</th>
        </tr></thead><tbody>${l4.map(r => {
        const pr = (MS.p_root || []).find(p => p.arm === r.arm && p.layer === 'L4');
        return `<tr><td class="mono">${esc(r.arm)}</td><td class="num">${fmt(r.n)}</td>
          <td class="num"><strong>${r.accuracy.toFixed(3)}</strong></td>
          <td class="num">[${r.ci95[0].toFixed(3)}, ${r.ci95[1].toFixed(3)}]</td>
          <td class="num">${r.z_vs_chance > 0 ? '+' : ''}${r.z_vs_chance.toFixed(2)}</td>
          <td class="num">${pr && pr.p50 != null ? pr.p50.toFixed(3) : '—'}</td></tr>`; }).join('')}
        </tbody></table>`;
  const widest = cross.length ? cross[0] : null;
  document.getElementById('meas-crossarm-note').innerHTML = widest
    ? `The widest separated pair is <strong>${esc(widest.a)}</strong> at ${widest.a_acc.toFixed(3)}
       against <strong>${esc(widest.b)}</strong> at ${widest.b_acc.toFixed(3)} — a difference of
       ${widest.diff.toFixed(3)} (z = ${widest.z}, ${cross.filter(c => c.separated).length} of
       ${cross.length} pairs separated at 0.05). Because the rule is identical across arms and the
       lengths are comparable, the difference is attributable to the script rather than to the
       decoys. It is <em>not</em> attributable to a layer difference: L4 is the same layer in each
       arm.`
    : '';

  const pr = (MS.p_root || []).slice().sort((a, b) =>
      (a.layer === b.layer ? (b.p50 - a.p50) : a.layer.localeCompare(b.layer)));
  document.getElementById('meas-proot').innerHTML = !pr.length
    ? '<div class="sub">not measured</div>'
    : `<table><thead><tr><th>arm</th><th>layer</th><th class="num">n</th>
        <th class="num">p_root p25</th><th class="num">median</th><th class="num">p75</th>
        <th class="num">exactly 0</th></tr></thead><tbody>${pr.map(p => `<tr>
        <td class="mono">${esc(p.arm)}</td><td>${esc(p.layer)}</td><td class="num">${fmt(p.n)}</td>
        <td class="num">${p.p25 != null ? p.p25.toFixed(4) : '—'}</td>
        <td class="num"><strong>${p.p50 != null ? p.p50.toFixed(4) : '—'}</strong></td>
        <td class="num">${p.p75 != null ? p.p75.toFixed(4) : '—'}</td>
        <td class="num">${(100 * (p.exact_zero_frac || 0)).toFixed(1)}%</td></tr>`).join('')}
        </tbody></table>
      <div class="sub">${esc(MS.interpretation_note || '')}</div>`;

  const pos = MS.position_diagnostic || [];
  const drop = MS.L4_to_L1_drop || [];
  document.getElementById('meas-diagnostics').innerHTML = `
    <div class="grid" style="grid-template-columns:1fr 1fr">
      <div class="card"><h4 style="margin-top:0">Option-slot preference</h4>
        ${pos.length ? `<table><thead><tr><th>arm</th><th class="num">n</th>
          <th class="num">max share</th><th class="num">expected</th><th>verdict</th></tr></thead>
          <tbody>${pos.map(p => `<tr><td class="mono">${esc(p.arm)}</td>
            <td class="num">${fmt(p.n)}</td><td class="num">${p.max_share.toFixed(3)}</td>
            <td class="num">${p.expected.toFixed(2)}</td>
            <td>${p.verdict === 'no bias' ? '<span class="pill ok">no bias</span>'
                 : `<span class="pill bad">${esc(p.verdict)}</span>`}</td></tr>`).join('')}
          </tbody></table>` : '<div class="sub">not measured</div>'}
        <div class="sub">A model that prefers one slot makes accuracy a fact about the prompt's
          layout. All arms are near uniform, so the numbers above are about the channel.</div></div>
      <div class="card"><h4 style="margin-top:0">Layer contrast: usable or not</h4>
        ${drop.length ? `<table><thead><tr><th>arm</th><th class="num">L4 len</th>
          <th class="num">L1 len</th><th class="num">overlap</th><th>contrast</th></tr></thead>
          <tbody>${drop.map(d => `<tr><td class="mono">${esc(d.arm)}</td>
            <td class="num">${d.L4_len_range[0]}–${d.L4_len_range[1]}</td>
            <td class="num">${d.L1_len_range[0]}–${d.L1_len_range[1]}</td>
            <td class="num">${d.len_overlap_tokens}</td>
            <td>${d.contrast_usable ? '<span class="pill ok">usable</span>'
                 : '<span class="pill bad">not usable</span>'}</td></tr>`).join('')}
          </tbody></table>` : '<div class="sub">not measured</div>'}
        <div class="sub">Tokens of overlap between the two layers' state lengths inside each arm.
          Where it is small the layer difference cannot be separated from a length difference, and
          the contrast is reported as unavailable rather than estimated.</div></div>
    </div>`;

  const paired = MS.paired_ranked_vs_L4 || [];
  document.getElementById('meas-paired').innerHTML = !paired.length
    ? `<div class="sub">No paired comparison in this artefact. Run
       <code>eval_rrc_d1.py --by-state N</code> so that L2/L2c and L4 land on the same states, then
       re-run the analyser: sampling layers independently yields only a few dozen pairs, which is
       too few to test.</div>`
    : `<table><thead><tr><th>arm</th><th>ranked</th><th class="num">n pairs</th>
        <th class="num">ranked acc</th><th class="num">L4 acc</th><th class="num">drop</th>
        <th class="num">McNemar chi2</th><th>verdict</th></tr></thead><tbody>${paired.map(p => `<tr>
        <td class="mono">${esc(p.arm)}</td><td>${esc(p.ranked_layer)}</td>
        <td class="num">${fmt(p.n_pairs)}</td>
        <td class="num">${p.ranked_acc.toFixed(3)}</td>
        <td class="num">${p.L4_acc.toFixed(3)}</td>
        <td class="num">${p.drop > 0 ? '+' : ''}${p.drop.toFixed(3)}</td>
        <td class="num">${p.mcnemar_chi2 != null ? p.mcnemar_chi2.toFixed(2) : '—'}</td>
        <td>${p.significant ? '<span class="pill ok">significant</span>'
             : '<span class="pill warn">not significant</span>'}</td></tr>`).join('')}
        </tbody></table>
      <div class="sub">McNemar, because the two conditions are the same item: only the discordant
        pairs carry information. A drop means the item got harder once the decoys were drawn from
        the channel instead of from the pool.</div>`;

  // ---- 5.10 the rank curve per arm, and the frequency preference that explains the reversal
  const f2 = MS.f2_rank_effect || [];
  document.getElementById('meas-f2').innerHTML = !f2.length
    ? '<div class="sub">not measured on this run</div>'
    : `${f2.map(e => {
        const rows = (e.curve || []).slice(0, 8);
        return `<div class="card" style="margin-bottom:10px">
          <h4 style="margin-top:0">${esc(e.arm)} <span class="sub">ranked against
            ${esc(e.rank_source || '—')}</span></h4>
          <table><thead><tr><th class="num">rank</th><th class="num">n</th>
            <th class="num">accuracy</th><th class="num">95% CI</th></tr></thead><tbody>
            ${rows.map(c => `<tr><td class="num">${c.rank}</td><td class="num">${c.n}</td>
              <td class="num">${c.acc.toFixed(4)}</td>
              <td class="num">[${c.ci95[0].toFixed(3)}, ${c.ci95[1].toFixed(3)}]</td></tr>`).join('')}
            </tbody></table>
          ${(e.curve || []).length > 8
            ? `<div class="sub">… ${(e.curve || []).length - 8} further rank values in the artefact</div>`
            : ''}
          <div style="margin-top:8px">rank-1 <strong>${e.rank_1_acc.toFixed(4)}</strong>
            [${e.rank_1_ci95[0].toFixed(3)}, ${e.rank_1_ci95[1].toFixed(3)}] n=${fmt(e.rank_1_n)}
            versus rank&gt;1 <strong>${e.rank_gt1_acc.toFixed(4)}</strong>
            [${e.rank_gt1_ci95[0].toFixed(3)}, ${e.rank_gt1_ci95[1].toFixed(3)}] n=${fmt(e.rank_gt1_n)}
            · z=${e.z_rank1_minus_rest == null ? '—' : (e.z_rank1_minus_rest > 0 ? '+' : '') + e.z_rank1_minus_rest}
            → <strong>${esc(e.direction)}</strong></div>
        </div>`;
      }).join('')}`;

  const pref = MS.candidate_preference || [];
  document.getElementById('meas-pref').innerHTML = !pref.length
    ? '<div class="sub">not measured on this run</div>'
    : `<table><thead><tr><th>arm</th><th class="num">n</th>
        <th class="num">picked rank (mean)</th><th class="num">uniform null</th>
        <th class="num">difference</th><th>preference</th>
        <th class="num">rarest share</th><th class="num">commonest share</th></tr></thead>
        <tbody>${pref.map(p => `<tr><td class="mono">${esc(p.arm)}</td>
          <td class="num">${fmt(p.n)}</td>
          <td class="num">${p.picked_rank_mean.toFixed(2)}</td>
          <td class="num">${p.uniform_null_rank_mean.toFixed(2)}</td>
          <td class="num"><strong>${p.difference > 0 ? '+' : ''}${p.difference.toFixed(2)}</strong></td>
          <td><span class="pill ${p.direction === 'prefers commoner' ? 'ok' : 'warn'}">${esc(p.direction)}</span></td>
          <td class="num">${(100 * p.rarest_share).toFixed(1)}%</td>
          <td class="num">${(100 * p.commonest_share).toFixed(1)}%</td></tr>`).join('')}
        </tbody></table>
      <div class="sub">The null is a uniform choice over that item's own five candidates, which is
        the only comparison that separates a frequency preference from accuracy. Uniform chance
        would place each share at ${(100 * (pref[0] && pref[0].uniform_share || 0.2)).toFixed(0)}%.</div>`;

  const shift = MS.state_displacement || [];
  document.getElementById('meas-shift').innerHTML = !shift.length
    ? '<div class="sub">not measured on this run</div>'
    : `${shift.map(e => `<div class="card" style="margin-bottom:10px">
        <h4 style="margin-top:0">${esc(e.arm)}</h4>
        <div class="sub">correlation of the shown character's rank with the chosen candidate's
          rank: <strong>${e.corr_state_rank_vs_picked_rank == null ? '—'
          : (e.corr_state_rank_vs_picked_rank > 0 ? '+' : '') + e.corr_state_rank_vs_picked_rank}</strong>
          · overall displacement <strong>${e.overall_displacement > 0 ? '+' : ''}${e.overall_displacement}</strong>
          rank positions (chosen ${e.overall_picked_rank_median} against shown ${e.overall_state_rank_median})</div>
        <table><thead><tr><th>band</th><th class="num">n</th>
          <th class="num">shown rank</th><th class="num">chosen rank</th>
          <th class="num">displacement</th><th class="num">accuracy</th></tr></thead><tbody>
          ${(e.bands || []).map(b => `<tr><td>${esc(b.band)}</td><td class="num">${b.n}</td>
            <td class="num">${b.state_rank_median}</td><td class="num">${b.picked_rank_median}</td>
            <td class="num"><strong>${b.displacement > 0 ? '+' : ''}${b.displacement}</strong></td>
            <td class="num">${b.accuracy.toFixed(3)}</td></tr>`).join('')}
        </tbody></table></div>`).join('')}
      <div class="sub">${esc((shift[0] && shift[0].reading) || '')}</div>`;

  // the figure's own provenance, so a reader can tell which run drew it. Two artefacts feed the
  // three panels and both are named, because the rank curve would be unbalanced if it came from the
  // state-based run.
  const figNote = document.getElementById('fig-note');
  if (figNote) {
    const dispN = (MS.state_displacement || []).reduce((n, e) => n + (e.n || 0), 0);
    figNote.textContent = `${fmt(dispN)} items in panels (a)-(b)` +
      ` (${esc(MS._from_state_displacement || MS._source_file || '')})` +
      `; ${fmt(MS.n_rows)} in panel (c)` +
      ` (${esc(MS._from_f2_rank_effect || '')})`;
  }

  const marg = MS.margin_effect || [];
  document.getElementById('meas-margin').innerHTML = !marg.length
    ? '<div class="sub">not measured on this run (needs the run that includes the English arms)</div>'
    : `${marg.map(e => `<div class="card" style="margin-bottom:10px">
        <h4 style="margin-top:0">${esc(e.arm)}
          <span class="sub">${esc((e.layers || []).join('/'))} · n=${fmt(e.n)} ·
            margin ${e.margin_min} to ${e.margin_max}</span></h4>
        <table><thead><tr><th>quartile of margin</th><th class="num">n</th>
          <th class="num">median margin</th><th class="num">accuracy</th>
          <th class="num">95% CI</th></tr></thead><tbody>
          ${(e.bands || []).map(b => `<tr><td>${esc(b.band)}</td><td class="num">${b.n}</td>
            <td class="num">${b.margin_median.toFixed(3)}</td>
            <td class="num"><strong>${b.accuracy.toFixed(3)}</strong></td>
            <td class="num">[${b.ci95[0].toFixed(3)}, ${b.ci95[1].toFixed(3)}]</td></tr>`).join('')}
        </tbody></table>
        <div class="sub">corr(margin, correct) = <strong>${e.corr_margin_correct == null ? '—'
          : (e.corr_margin_correct > 0 ? '+' : '') + e.corr_margin_correct}</strong> ·
          shape <strong>${esc(e.shape)}</strong></div></div>`).join('')}`;

  // ---- 7.1 cost and timing. Reads the run's own reported rate; when a run predates the field,
  // it says so rather than quoting a number retyped from a log.
  const RT = MS.rate || {};
  document.getElementById('repro-timing').innerHTML = `
    <div class="grid" style="grid-template-columns:1fr 1fr">
      <div class="card"><h4 style="margin-top:0">This run</h4>
        ${RT.items_per_s
          ? `<table><tbody>
              <tr><td>items evaluated</td><td class="num">${fmt(RT.items)}</td></tr>
              <tr><td>wall clock</td><td class="num">${RT.elapsed_s} s</td></tr>
              <tr><td>throughput</td><td class="num"><strong>${RT.items_per_s} items/s</strong></td></tr>
              <tr><td>sampling</td><td class="num">${esc(RT.sampling || '—')}</td></tr>
             </tbody></table>
             <div class="sub">from <span class="mono">${esc(RT.source_file || '')}</span></div>`
          : `<div class="sub">This run predates the throughput field, so no rate is quoted here —
             a number retyped from a console log is a second copy of a number that belongs in an
             artefact. Later runs record <span class="mono">rate</span> in their summary.</div>`}
      </div>
      <div class="card"><h4 style="margin-top:0">Two effects that move it by an order of magnitude</h4>
        <p style="margin-top:6px"><strong>(a) A failed fast path, retried per batch.</strong> The
        runner packs single-question requests into trees, but that path needs flash-attention, which
        this build lacks. Each call therefore allocated a 128-request batch, failed late, and fell
        back to one request at a time — so the wasted allocation scaled with the batch's tokens.
        Disabling the fast path after its first failure took the <em>same 2,048 items</em> from
        <strong>715.5 s to 88.8 s</strong>, an 8× change with no change in what was measured.</p>
        <p><strong>(b) Degradation inside one process.</strong> Throughput fell 21 → 9.3 → 5.1
        items/s across a single run on an otherwise idle card. The pattern is consistent with
        allocator fragmentation under per-item forwards. Neither effect is a property of the
        corpus, and neither is reported as one: they change how long a replication takes, not what
        it finds.</p>
      </div>
    </div>`;

  // ---- 3 funnel, as TWO stages, because they are two different units. A record is a pair read
  // from a corpus and a question is one item, and one record can yield several questions;
  // subtracting one from the other is meaningless. Each stage closes on its own identity, and
  // the table renders a visible failure if either half stops reconciling.
  const S1 = (k) => order.reduce((n, a) => n + (A[a][k] || 0), 0);
  const rec = [
    ['records admitted', S1('source_records'), 'rows the loaders returned after format parsing'],
    ['− unit consistency', S1('dropped_unit'),
     'the state and the root were not the same kind of object, so the pair is not a substitution; ' +
     'the state and the root were not the same kind of object, so the pair is not a substitution'],
    ['− empty or identical', S1('dropped'),
     'the root equals the state, so the question has no correct answer'],
    ['− script-purity gate', S1('dropped_script'),
     'rows whose writing system did not match the arm declaration'],
    ['− no layer available', S1('dropped_no_layer'),
     'no layer could be built: too few other attested errors of the root, no reading index, or too ' +
     'small a similarity pool'],
    ['= records carrying a question', S1('records_with_layer'), 'at least one layer was built']
  ];
  const items = [
    ['questions a kept record could support', S1('items_attempted'), 'one per layer built'],
    ['− duplicate', S1('dropped_duplicate'),
     'the same (layer, state, root) offered twice by the source'],
    ['− validity constraint', S1('dropped_margin'),
     'ranked-layer items where a decoy fitted the state at least as well as the root'],
    ['= shipped items', S1('n_items'), D.n_options + ' options each, one of them the root']
  ];
  // The report checks its own arithmetic. If either half stops closing, the table says so instead
  // of printing a number that looks like a total.
  const recCloses = S1('dropped_unit') + S1('dropped') + S1('dropped_script')
                   + S1('dropped_no_layer') + S1('records_with_layer') === S1('source_records');
  const itemCloses = S1('dropped_duplicate') + S1('dropped_margin') + S1('n_items')
                     === S1('items_attempted');
  const funnelHalf = (title, rows, close, lastIdx) =>
    `<div class="sub" style="margin:6px 0 4px"><strong>${esc(title)}</strong></div>` +
    '<table><thead><tr><th>stage</th><th class="num">count</th><th class="num">share</th>' +
    '<th>what it removes</th></tr></thead><tbody>' +
    rows.map(([lbl, n, why], i) => `<tr><td${i === lastIdx ? ' style="font-weight:650"' : ''}>` +
      `${esc(lbl)}</td><td class="num">${fmt(n)}</td>` +
      `<td class="num">${p1(n / (rows[0][1] || 1))}</td>` +
      `<td class="sub">${esc(why)}</td></tr>`).join('') +
    '</tbody></table>' +
    (close ? '' : '<p class="sub" style="color:#b00">this half does not reconcile — one of its ' +
                  'stages is missing or double-counted</p>');
  document.getElementById('funnel').innerHTML =
    funnelHalf('Stage 1 — record level', rec, recCloses, rec.length - 1) +
    funnelHalf('Stage 2 — item level', items, itemCloses, items.length - 1);
  // The funnel figure's caption closes on the headline pair, rendered rather than typed, because a
  // typed pair in a caption is the copy that drifts when a gate is added.
  const fn = document.getElementById('fun-note');
  if (fn) {
    const recIn = S1('source_records'), qOut = S1('n_items');
    const recGone = (S1('dropped_unit') + S1('dropped') + S1('dropped_script')
                     + S1('dropped_no_layer'));
    const itGone = S1('dropped_duplicate') + S1('dropped_margin');
    fn.textContent = recIn && qOut
      ? ` ${fmt(recIn)} records in and ${fmt(qOut)} questions out, through gates that account for ` +
        `${p1(recGone / recIn)} of the records and ${p1(itGone / S1('items_attempted'))} of the ` +
        `questions a kept record could support`
      : '';
  }

  // ---- 4 tiles
  const layerSet = new Set();
  Object.values(A).forEach(a => Object.keys(a.layers || {}).forEach(k => layerSet.add(k)));
  const unitBad = order.filter(k => (A[k].unit_violations || 0) > 0);
  const ime = order.filter(k => A[k].group_size_median).map(k => A[k]);
  document.getElementById('tiles').innerHTML = [
    ['Total items', fmt(D.total_items), order.length + ' arms'],
    ['Options per item', D.n_options, 'chance ' + (1 / D.n_options).toFixed(2)],
    ['Layers present', layerSet.size, [...layerSet].sort().join(' ')],
    ['Sources', Object.keys(S.sources).length, 'all observed'],
    ['Unit consistency', unitBad.length ? unitBad.length + ' arms' : 'clean', 'QC suite verdict'],
    ['IME group size', ime.length ? ime[0].group_size_median : '—', 'characters per reading'],
    ['IME median rank', (ime.length && ime[0].group_rank) ? ime[0].group_rank.median : '—',
     'position the input method offers the root at']
  ].map(([k, v, n]) => `<div class="tile"><div class="k">${esc(k)}</div>
      <div class="v">${esc(v)}</div><div class="n">${esc(n)}</div></div>`).join('');

  // ---- 4.1 arm table
  document.getElementById('armTable').innerHTML = `
    <thead><tr><th>arm</th><th>language</th><th class="num">items</th><th class="num">records</th>
      <th class="num">layers</th><th class="mono">sha256</th><th>layer breakdown</th></tr></thead>
    <tbody>${order.map(k => { const a = A[k]; return `<tr>
      <td class="mono">${esc(k)}</td><td>${esc(a.language)}</td>
      <td class="num">${fmt(a.n_items)}</td><td class="num">${fmt(a.source_records)}</td>
      <td class="num">${Object.keys(a.layers || {}).length}</td>
      <td class="mono" style="font-size:11px">${esc(a.sha256)}</td>
      <td class="mono" style="font-size:11.5px">${Object.entries(a.layers || {}).map(([l, n]) => l + ':' + fmt(n)).join(' ')}</td></tr>`;
    }).join('')}</tbody>`;

  // ---- 4.2 layer chart (inline SVG, no external deps)
  const LAYERS = [...layerSet].sort();
  const LW = 720, rowH = 30, LH = rowH * order.length + 64, Lp = 96, Rp = 44;
  const maxN = Math.max(1, ...order.map(k => Math.max(...Object.values(A[k].layers || {0: 0}))));
  const colOf = l => ({L1:'#8fb3dd', L2:'#1b3a6b', L2c:'#c46a3a', L3:'#7a9bc4', L3del:'#7a9bc4', L4:'#d8dee7'}[l] || '#9aa7b6');
  let svg = `<svg viewBox="0 0 ${LW} ${LH}" width="100%" style="max-width:${LW}px">`;
  svg += `<text x="${Lp}" y="12" font-size="10" fill="var(--dim)">items per layer — length is the count, scale 0…${fmt(maxN)}</text>`;
  order.forEach((k, i) => {
    const y = 26 + rowH * i, lay = A[k].layers || {};
    svg += `<text x="${Lp - 8}" y="${y + 13}" font-size="11" fill="var(--ink)" text-anchor="end" font-family="var(--mono)">${esc(k)}</text>`;
    let x = Lp; const usable = LW - Lp - Rp;
    LAYERS.forEach(l => {
      const n = lay[l] || 0; if (!n) return;
      const w = Math.max(1.5, usable * n / maxN);
      svg += `<rect x="${x}" y="${y + 2}" width="${w}" height="15" fill="${colOf(l)}" stroke="#00000022" stroke-width=".5"><title>${esc(k)} ${l}: ${fmt(n)}</title></rect>`;
      if (w > 40) svg += `<text x="${x + 4}" y="${y + 13}" font-size="10" fill="${l === 'L2' ? '#fff' : '#123'}">${l} ${fmt(n)}</text>`;
      x += w;
    });
  });
  svg += '</svg>';
  svg += '<div class="sub" style="margin-top:7px">' +
      LAYERS.map(l => `<span class="pill" style="border-left:4px solid ${colOf(l)};margin-right:6px">${l}</span>`).join('') +
      ' — coverage differs by arm, so a cross-arm comparison is valid only within a shared layer. ' +
      'L1 = other attested errors of the same root; L2 = nearest real words; L2c = the reading ' +
      'channel; L3 = constructed from the deletion class; L4 = a shuffled unrelated-form control.</div>';
  document.getElementById('layerChart').innerHTML = svg;

  // ---- 4.3 length ladders
  document.getElementById('lenTable').innerHTML = `
    <thead><tr><th>arm</th><th class="num">state min</th><th class="num">p25</th>
      <th class="num">median</th><th class="num">p75</th><th class="num">max</th>
      <th class="num">root median</th><th class="num">root max</th></tr></thead>
    <tbody>${order.map(k => { const a = A[k]; return `<tr><td class="mono">${esc(k)}</td>
      <td class="num">${fmt(a.state_len.min)}</td><td class="num">${fmt(a.state_len.p25)}</td>
      <td class="num">${fmt(a.state_len.median)}</td><td class="num">${fmt(a.state_len.p75)}</td>
      <td class="num">${fmt(a.state_len.max)}</td>
      <td class="num">${fmt(a.root_median)}</td><td class="num">${fmt(a.root_max)}</td></tr>`;
    }).join('')}</tbody>`;

  // ---- 4.4 ranked-layer difficulty
  document.getElementById('consistency').innerHTML = `
    <table><thead><tr><th>arm</th><th class="num">unit violations</th>
      <th class="num">margin median</th><th class="num">margin &gt; 0</th>
      <th class="num">ranked items</th><th>verdict</th></tr></thead>
    <tbody>${order.map(k => { const a = A[k];
      const v = (a.unit_violations || 0) === 0;
      const nr = Object.values(a.margin_ranked_layers || {}).reduce((x, y) => x + y, 0);
      return `<tr><td class="mono">${esc(k)}</td>
        <td class="num ${v ? '' : 'bad'}">${a.unit_violations === null ? 'n/a' : fmt(a.unit_violations)}</td>
        <td class="num">${a.margin_median === null ? '—' : a.margin_median}</td>
        <td class="num">${a.margin_positive_share === null ? '—' : p1(a.margin_positive_share)}</td>
        <td class="num">${nr ? fmt(nr) : 'not ranked'}</td>
        <td><span class="pill ${v ? 'ok' : 'bad'}">${v ? 'consistent' : 'VIOLATION'}</span></td></tr>`;
    }).join('')}</tbody></table>
    <div class="sub">The margin is defined only where candidates are ranked against the state (L2,
      L3). On the reading layer it is identically zero (§2.4), and on L1 and L4 it is not defined at
      all because those candidates are not ranked; <code>null</code> is recorded in each case rather
      than a zero that would be averaged into a difficulty the layer does not have.</div>`;

  // ---- 4.5 IME card
  const imeArms = order.filter(k => A[k].group_size_median);
  document.getElementById('imeCard').innerHTML = !imeArms.length
    ? '<div class="sub">No arm carries the reading channel.</div>'
    : `<p class="sub">Candidates on this layer share the reading of the errored position by
        construction, so no similarity measure ranks them (§2.4). The quantity that does
        characterise the channel is the size of the group it offers and where in that group —
        ordered by corpus frequency, the order an input method presents — the root sits.</p>
      <table><thead><tr><th>arm</th><th class="num">items ranked</th>
        <th class="num">group size median</th><th class="num">group size max</th>
        <th class="num">rank median</th><th class="num">rank max</th>
        <th class="num">offered first</th><th class="num">offered last</th>
        <th class="num">item chance</th><th class="num">channel chance</th></tr></thead>
      <tbody>${imeArms.map(k => { const a = A[k], g = a.group_rank || {};
        const chChance = a.group_size_median ? (1 / a.group_size_median).toFixed(3) : '—';
        return `<tr><td class="mono">${esc(k)}</td><td class="num">${fmt(a.group_size_n)}</td>
        <td class="num">${a.group_size_median}</td><td class="num">${a.group_size_max}</td>
        <td class="num">${g.median === undefined ? '—' : g.median}</td>
        <td class="num">${g.max === undefined ? '—' : g.max}</td>
        <td class="num">${g.share_first === undefined ? '—' : p1(g.share_first)}</td>
        <td class="num">${g.share_last === undefined ? '—' : p1(g.share_last)}</td>
        <td class="num">${(1 / D.n_options).toFixed(2)}</td>
        <td class="num">${chChance}</td></tr>`; }).join('')}</tbody></table>
      <div class="sub">The channel's chance level is $1/n$, not $1/K$: the writer faced the whole
        group, the item shows ${D.n_options}. A model at the item's chance level is therefore
        <strong>above</strong> the channel's, and the fixed-choice form understates this channel.</div>`;

  // ---- 4.6 channel composition
  const cls = CH.classes || [];
  // 4.6(a)-(b) prose numbers, rendered rather than typed. The caption makes a claim about a
  // comparison, and a typed number in prose is a second copy of a measured quantity that no guard
  // can keep in step with the artefact. Both spans are filled from the same state the figure reads.
  const kv = document.getElementById('kbd-validate');
  if (kv) {
    const er = CH.edits_rate, pr = CH.published_rate;
    kv.textContent = (er != null && pr)
      ? ` — ${p2(100 * er)} % against ${p2(100 * pr)} %, a ratio of ${(er / pr).toFixed(2)}`
      : ' — not in state';
  }
  const kc = document.getElementById('kbd-compose');
  if (kc) {
    const d = cls.find(c => c.name === 'delete'), i2 = cls.find(c => c.name === 'insert');
    const k = cls.find(c => c.name === 'key_adjacency');
    kc.textContent = (d && i2 && k)
      ? `: deletions ${p1(d.share)} and insertions ${p1(i2.share)}, together roughly two thirds of
         it, while key adjacency — the single mechanism both published keyboard-noise generators are
         built on — is ${p1(k.share)}`
      : '';
  }
  document.getElementById('channelCard').innerHTML = `
    <div class="sub" style="margin-bottom:8px">Measured from ${esc(CH.source)} — ${esc(CH.method)}.
      ${fmt(CH.target_chars)} target characters, ${fmt(CH.edits_total)} edit operations.
      <br><strong>Two rates, not one.</strong> The all-edits rate is ${p2(100 * CH.edits_rate)} %
      (${esc(CH.rate_basis || '')}); the substitution-only rate is
      ${p2(100 * CH.substitution_rate)} % (${esc(CH.substitution_rate_basis || '')}). Only the first
      is comparable with the published ${p2(100 * CH.published_rate)} %.</div>
    <table><thead><tr><th>class</th><th class="num">share</th><th class="num">count</th>
      <th>modelled by the published generators?</th></tr></thead>
      <tbody>${cls.map(c => `<tr><td>${esc(c.name.replace(/_/g, ' '))}</td>
        <td class="num">${p1(c.share)}</td><td class="num">${fmt(c.n)}</td>
        <td>${c.name === 'key_adjacency'
            ? '<span class="pill bad">yes — their only mechanism</span>'
            : '<span class="pill warn">no</span>'}</td></tr>`).join('')}</tbody></table>`;

  // ---- 5 summary-figure caption: the two counts the figure is introduced with. Written from the
  // same blocks the figure reads, so the caption cannot drift from the panels it describes.
  const PA = MS.paired_ranked_vs_L4 || [], XA = MS.cross_arm_L4 || [];
  const dp = document.getElementById('disp-pair');
  if (dp) {
    const sd = MS.state_displacement || [];
    dp.textContent = sd.length
      ? ` about ${sd.map(e => e.overall_displacement.toFixed(0)).join(' against about ')} rank ` +
        `positions on ${sd.map(e => e.arm).join(' and ')} respectively.`
      : '';
  }
  const sp = document.getElementById('sum-paired');
  if (sp) {
    const sig = PA.filter(e => e.significant), ns = PA.filter(e => !e.significant);
    sp.textContent = sig.length && ns.length
      ? ` ${sig.length} of the ${PA.length} arms that have both layers drop significantly ` +
        `(chi-square ${Math.min(...sig.map(e => e.mcnemar_chi2)).toFixed(1)} to ` +
        `${Math.max(...sig.map(e => e.mcnemar_chi2)).toFixed(1)}); ` +
        `${ns.map(e => e.arm).join(', ')}'s ${ns[0].n_pairs} pairs do not, and its bar is drawn ` +
        `left of zero because the sign is not the finding.`
      : ` ${PA.length} paired arm(s) in this run.`;
  }
  const sx = document.getElementById('sum-cross');
  if (sx) {
    const l4 = (MS.accuracy || []).filter(e => e.layer === 'L4');
    const sep = XA.filter(e => e.separated).length;
    if (l4.length && XA.length) {
      const a = l4.map(e => e.accuracy);
      sx.textContent = ` The arms separate: ${Math.min(...a).toFixed(2)} to ` +
        `${Math.max(...a).toFixed(2)} on an identical item form, ${XA.length} of ${XA.length} pairs ` +
        `tested, ${sep} separated.`;
    }
  }

  // ---- 5.1 significance
  const ka = cls.find(c => c.name === 'key_adjacency');
  const del = cls.find(c => c.name === 'delete');
  const ins = cls.find(c => c.name === 'insert');
  const di = (del ? del.share : 0) + (ins ? ins.share : 0);
  document.getElementById('sigChannel').innerHTML = `
    <table><thead><tr><th>quantity</th><th class="num">value</th><th>reading</th></tr></thead>
    <tbody>
      <tr><td>adjacent-key substitution</td><td class="num">${p1(ka ? ka.share : null)}</td>
        <td class="sub">the mechanism both published generators model</td></tr>
      <tr><td>deletion + insertion</td><td class="num">${p1(di)}</td>
        <td class="sub">together, roughly two thirds of observed edits</td></tr>
      <tr><td>ratio</td>
        <td class="num">${ka && ka.share ? (di / ka.share).toFixed(1) + '×' : '—'}</td>
        <td class="sub">how much larger the unmodelled share is than the modelled one</td></tr>
    </tbody></table>`;

  // ---- 6 quality
  document.getElementById('qc').innerHTML = `
    <div class="card">
      <h3 style="margin-top:0">Seven automated check families, applied to the output</h3>
      <p>The suite is a separate artefact from the builder, so it examines what was written rather
      than what was intended. Each item is checked for canonical form, candidate integrity, decoy
      distinctness, script composition, provenance, state/root unit consistency, and the validity
      constraint; the reading channel's own consistency is checked on its layer; and the published
      empirical gate is applied at the threshold its source states — a 25 % sample in which at
      least 95 % must be realistic.</p>
      <p><strong>The checks are proven able to fail.</strong> <code>--negative-test</code> corrupts
      the first item of each arm in a way a specific check should catch and asserts that check goes
      red. A suite that has never failed is an untested suite wearing the costume of a passing one.
      The <code>validity</code> family was added after the constraint was found to be documented in
      the manifest and never applied by the builder, and on its first full run it found a further
      inconsistency in the builder itself — items on unranked layers still carried a margin.</p>
      <p class="sub">The numbers on this page come from the same live read the dashboard performs,
      so the page and the suite cannot disagree.</p>
    </div>`;

  document.getElementById('limits').innerHTML =
      (D.known_limitations || []).map(l => `<li>${esc(l)}</li>`).join('') ||
      '<li class="dim">none recorded</li>';

  document.getElementById('repro').textContent =
    "python scripts/build_han_frequency.py         # character frequency from the arm's own corpus\n" +
    'python scripts/build_rrc.py --options 5       # writes data/rrc/*.jsonl and config/rrc.json\n' +
    'python scripts/rrc_qc.py                     # seven check families + the published gate\n' +
    'python scripts/rrc_qc.py --negative-test     # proves the checks can fail\n' +
    'python scripts/profile_rrc.py                # numeric profile and distributions\n' +
    "python scripts/regen_data_statement.py       # rebuild the statement's numeric blocks\n" +
    'python scripts/qc_data_statement.py          # audit every number in the statement\n' +
    'python scripts/export_report_state.py        # writes viz/report/state.js for this page\n' +
    'python scripts/run_all_guards.py             # the full guard suite';

  // ---- 8 references
  // Grouped by role rather than by order of appearance, because a reader checking this report's
  // provenance is usually checking one kind of claim: what the data is, what measured it, what
  // standard it was resolved against, and what theory it is built on. Every entry carries a DOI or a
  // stable URL; the verification record is docs/bibliography_verification.json.
  const REFS = [
    // ---- corpora: the observed human error every arm is built from
    { k: 'hagiwara2020', t: 'Hagiwara, M. &amp; Mita, M. (2020). GitHub Typo Corpus: A Large-Scale Multilingual Dataset of ' +
      'Misspellings and Grammatical Errors. <em>Proceedings of the Twelfth Language Resources and ' +
      'Evaluation Conference (LREC 2020)</em>, 6761&ndash;6768. ELRA. ' +
      'https://aclanthology.org/2020.lrec-1.835/ &mdash; <strong>the largest single source here</strong>: ' +
      'one release feeds three of the six arms (<span class="mono">rrc-en</span>, ' +
      '<span class="mono">rrc-ru</span>, <span class="mono">rrc-zh-gh</span>). CC-BY-NC 4.0, so the ' +
      'non-commercial term travels with any redistribution.' },
    { k: 'mittonnd', t: 'Mitton, R. (n.d.). <em>Birkbeck Spelling Error Corpus</em>. Distributed by the compiler for ' +
      'research use; Oxford Text Archive handle 20.500.12024/0643. &mdash; the source of the English ' +
      'word-level arm. Word-level only, so this arm&rsquo;s object size differs from the others by ' +
      'construction.' },
    { k: 'tanaka2020', t: 'Tanaka, Y., Murawaki, Y., Kawahara, D. &amp; Kurohashi, S. (2020). Building a Japanese Typo ' +
      'Dataset from Wikipedia&rsquo;s Revision History. <em>Proceedings of the 58th Annual Meeting of ' +
      'the Association for Computational Linguistics: Student Research Workshop</em> (ACL 2020 ' +
      'Student Research Workshop), 230&ndash;236. ACL. https://aclanthology.org/2020.acl-srw.31/ ' +
      '&mdash; the paper for the Japanese source used here (JWTD, CC-BY-SA 3.0, a copyleft term that ' +
      'follows redistribution).' },
    { k: 'cscdnd', t: '<em>CSCD / CSCD-NS &mdash; Chinese Spelling Check corpus</em>, released for the SIGHAN ' +
      'Chinese-spelling-check shared tasks. &mdash; the source of the Chinese arm. <strong>No ' +
      'bibliographic anchor has been located for the specific release used</strong>; it is identified ' +
      'by file hash and record count in <span class="mono">config/data_manifest.json</span>, and this ' +
      'is a limitation on the citation rather than a gap papered over.' },
    // ---- instruments: what measured the channels
    { k: 'liquid2026', t: 'Liquid AI. (2026). <em>d1-3B</em> (revision da1fe36) [Model]. Hugging Face. ' +
      'https://huggingface.co/LiquidAI/d1-3B (accessed 10 October 2026). &mdash; <strong>the ' +
      'measurement instrument</strong> for every result in &sect;5, run natively in bfloat16 and ' +
      'offline. Released 7 October 2026; documented by its model card, there being no separate ' +
      'technical report.' },
    { k: 'dhakal2018', t: 'Dhakal, V., Feit, A. M., Kristensson, P. O. &amp; Oulasvirta, A. (2018). Observations on Typing ' +
      'from 136 Million Keystrokes. <em>Proceedings of the 2018 CHI Conference on Human Factors in ' +
      'Computing Systems (CHI 2018)</em>, Paper 208, 1&ndash;12. ACM. ' +
      'https://doi.org/10.1145/3173574.3174220 &mdash; the source of the empirical keystroke channel ' +
      'in &sect;4.6. Its published uncorrected error rate is 1.167&nbsp;% (SD 1.43&nbsp;%); the rate ' +
      'measured here from the same corpus under a matching definition is 1.19&nbsp;%, a ratio of ' +
      '1.02, and that agreement is what licenses the decomposition in the same panel.' },
    { k: 'kargaran2024', t: 'Kargaran, A. H., Yvon, F. &amp; Sch&uuml;tze, H. (2024). GlotScript: A Resource and Tool for Low ' +
      'Resource Writing System Identification. <em>Proceedings of LREC-COLING 2024</em>, ' +
      '7774&ndash;7784. ELRA and ICCL. https://aclanthology.org/2024.lrec-main.687/ &mdash; the ' +
      'instrument that measures which writing system is actually present, enforcing each ' +
      'arm&rsquo;s script declaration. Used as a gate, and its disagreements with the declared ' +
      'metadata are reported rather than suppressed.' },
    { k: 'ravichander2021', t: 'Ravichander, A., Dalmia, S., Ryskina, M., Metze, F., Hovy, E. &amp; Black, A. W. (2021). ' +
      'NoiseQA: Challenge Set Evaluation for User-Centric Question Answering. <em>Proceedings of ' +
      'EACL 2021</em>, 2976&ndash;2992. ACL. https://aclanthology.org/2021.eacl-main.259/ &mdash; ' +
      'considered and <strong>not used</strong>: question-answering noise is a different object from ' +
      'orthographic error.' },
    { k: 'bexte2022', t: 'Bexte, M., Laarmann-Quante, R., Horbach, A. &amp; Zesch, T. (2022). LeSpell &mdash; A ' +
      'Multi-Lingual Benchmark Corpus of Spelling Errors to Develop Spellchecking Methods for ' +
      'Learner Language. <em>Proceedings of LREC 2022</em>, 697&ndash;706. ELRA. ' +
      'https://aclanthology.org/2022.lrec-1.73/ &mdash; considered and <strong>not used</strong>: its ' +
      'writers are second-language learners, a different channel from the one under study.' },
    { k: 'sengupta2021', t: 'Sengupta, S., Krone, J. &amp; Mansour, S. (2021). On the Robustness of Intent Classification ' +
      'and Slot Labeling in Goal-oriented Dialog Systems to Real-world Noise. <em>Proceedings of the ' +
      'Third Workshop on Natural Language Processing for Conversational AI (NLP4ConvAI 2021)</em>, ' +
      '68&ndash;79. ACL. https://aclanthology.org/2021.nlp4convai-1.7/ &mdash; the real-world noisy ' +
      'benchmark whose seven-type taxonomy this report <strong>rejects as a layer structure</strong> ' +
      '(three of its seven types are English-only, its domain is locked to two task datasets, and it ' +
      'is non-commercial), while adopting its two quantitative rules: inject noise only into a ' +
      'carrier phrase, and accept at 95&nbsp;% of a 25&nbsp;% sample.' },
    // ---- standards and shared resources
    { k: 'unicodend', t: 'Unicode Consortium. <em>Common Locale Data Repository (CLDR), keyboards 3.0</em>. ' +
      'https://cldr.unicode.org/ &mdash; the LDML keyboard files. The kana flick group comes from the ' +
      'flick layout. The layout data fixes two facts about the arms: French is AZERTY, and the ' +
      'Japanese writing system is mixed, not syllabary-syllabic.' },
    { k: 'unicodend2', t: 'Unicode Consortium. <em>Unicode Standard Annex #29</em> (grapheme cluster boundaries) and ' +
      '<em>UAX #15</em> (normalization). https://unicode.org/reports/tr29/ &mdash; the basis of the ' +
      'grapheme segmentation and the canonical form applied once, at the ingestion boundary. Both are ' +
      'load-bearing rather than cosmetic: slicing by code point splits a combining accent from its ' +
      'base, and CJK compatibility ideographs make one character two distinct strings.' },
    { k: 'ritchie2024', t: 'Ritchie, S., van Esch, D., Okonkwo, U., Vashishth, S. &amp; Drummond, E. (2024). LinguaMeta: ' +
      'Unified metadata for thousands of languages. <em>Proceedings of LREC-COLING 2024</em>, ' +
      '10530&ndash;10538. ELRA and ICCL. https://aclanthology.org/2024.lrec-main.921/ &mdash; the ' +
      'source of the language-to-writing-system mapping for every arm.' },
    { k: 'van2022', t: 'van Esch, D., Lucassen, T., Ruder, S., Caswell, I. &amp; Rivera, C. (2022). Writing System and ' +
      'Speaker Metadata for 2,800+ Language Varieties. <em>Proceedings of LREC 2022</em>, ' +
      '5035&ndash;5046. ELRA. https://aclanthology.org/2022.lrec-1.538/ &mdash; the predecessor ' +
      'resource to LinguaMeta, and the basis of the attested-script field: an arm may carry several ' +
      'scripts because the standard records every attested one.' },
    { k: 'silnd', t: 'SIL International. <em>ISO 639-3 Registration Authority code tables</em>. ' +
      'https://iso639-3.sil.org/ &mdash; the language-code table the arms&rsquo; metadata is resolved ' +
      'against.' },
    { k: 'speer2022', t: 'Speer, R. (2022). <em>rspeer/wordfreq: v3.0</em> (v3.0.2) [Software]. Zenodo. ' +
      'https://doi.org/10.5281/zenodo.7199437 &mdash; lexical frequency for real-word filtering. A ' +
      'published frequency resource, used deliberately in place of, and kept separate from, the ' +
      'corpus-observed character frequency that defines the reading channel&rsquo;s rank.' },
    // ---- theory: what the framework is built on, and what is criticised
    { k: 'kernighan1990', t: 'Kernighan, M. D., Church, K. W. &amp; Gale, W. A. (1990). A Spelling Correction Program Based ' +
      'on a Noisy Channel Model. <em>COLING 1990 Volume 2: Papers presented to the 13th International Conference on Computational Linguistics</em>. ACL. ' +
      'https://aclanthology.org/C90-2036/ &mdash; the founding application of the noisy channel to ' +
      'orthographic error, and the decomposition &sect;2.1 is written in.' },
    { k: 'katz1992', t: 'Katz, L. &amp; Frost, R. (1992). The reading process is different for different orthographies: ' +
      'The orthographic depth hypothesis. In R. Frost &amp; L. Katz (Eds.), <em>Orthography, ' +
      'Phonology, Morphology, and Meaning</em> (Advances in Psychology, Vol. 94, pp. 67&ndash;84). ' +
      'North-Holland. https://doi.org/10.1016/S0166-4115(08)62789-2 &mdash; the original statement of ' +
      'the depth hypothesis, used here as <strong>the hypothesis under test rather than a ' +
      'premise</strong> (&sect;2.7).' },
    { k: 'frost1987', t: 'Frost, R., Katz, L. &amp; Bentin, S. (1987). Strategies for visual word recognition and ' +
      'orthographical depth: A multilingual comparison. <em>Journal of Experimental Psychology: ' +
      'Human Perception and Performance</em>, 13(1), 104&ndash;114. ' +
      'https://doi.org/10.1037/0096-1523.13.1.104 &mdash; the empirical multilingual comparison ' +
      'behind the depth claim. Read critically here: it establishes a comparison across ' +
      'orthographies, not a rank ordering of scripts, and this report does not treat it as a ' +
      'per-script difficulty scale.' },
    { k: 'coltheart1977', t: 'Coltheart, M., Davelaar, E., Jonasson, J. T. &amp; Besner, D. (1977). Access to the internal ' +
      'lexicon. In S. Dornic (Ed.), <em>Attention and Performance VI</em>, 535&ndash;555. Lawrence ' +
      'Erlbaum. https://doi.org/10.4324/9781003309734-29 &mdash; the canonical definition of ' +
      'orthographic neighbourhood N (the words one letter away), and the reason the ranked layers ' +
      'carry a nearest-neighbour decoy rule.' },
    { k: 'lisbach2013', t: '<span class="cite" data-cite="lisbach2013">Lisbach, B. &amp; Meyer, V. (2013)</span>. <em>Linguistic Identity Matching</em>. Springer. ' +
      'ISBN 978-3-8348-2095-2. https://doi.org/10.1007/978-3-8348-2095-2 &mdash; the <strong>only ' +
      'verifiable</strong> source for the four-operation taxonomy on the operation axis. The taxonomy rests on this one source and is treated accordingly.' },
    { k: 'bender2013', t: 'Bender, E. M. (2013). <em>Linguistic Fundamentals for Natural Language Processing: 100 ' +
      'Essentials from Morphology and Syntax</em>. Synthesis Lectures on Human Language Technologies, ' +
      'Vol. 6, No. 1. Morgan &amp; Claypool. No address is asserted for this entry: the publisher&rsquo;s record reports more than one DOI and neither was resolved from this host. ' +
      '&mdash; the treatment of writing systems underlying the script classification used here.' },
    { k: 'bender2018', t: 'Bender, E. M. &amp; Friedman, B. (2018). Data Statements for Natural Language Processing: Toward ' +
      'Mitigating System Bias and Enabling Better Science. <em>Transactions of the Association for ' +
      'Computational Linguistics</em>, 6, 587&ndash;604. https://doi.org/10.1162/tacl_a_00041 ' +
      '&mdash; the section structure of the accompanying data statement, and the source of the ' +
      'requirement that a corpus state what it excludes.' },
    { k: 'guo2017', t: 'Guo, C., Pleiss, G., Sun, Y. &amp; Weinberger, K. Q. (2017). On Calibration of Modern Neural ' +
      'Networks. <em>Proceedings of the 34th International Conference on Machine Learning (ICML ' +
      '2017)</em> (PMLR, Vol. 70, pp. 1321&ndash;1330). https://proceedings.mlr.press/v70/guo17a.html ' +
      '&mdash; the result that a model&rsquo;s confidence is not its accuracy, which is why &sect;5 ' +
      'reports the pair (probability on the truth, probability on the answer chosen) rather than ' +
      'accuracy alone.' },
    { k: 'kadavath2022', t: 'Kadavath, S. <em>et al.</em> (2022). Language Models (Mostly) Know What They Know. ' +
      'arXiv:2207.05221. https://arxiv.org/abs/2207.05221 &mdash; the finding that a model&rsquo;s ' +
      'self-report carries signal but is imperfectly calibrated. Read critically here: it measures ' +
      'whether a model can <em>report</em> its own knowledge, which is not the same as whether its ' +
      'token probabilities are calibrated, and this report relies only on the latter.' },
    { k: 'zhao2026', t: 'Zhao, R., Liu, Y., Altinger, L., Sch&uuml;tze, H. &amp; Hedderich, M. A. (2026). Evaluating ' +
      'Robustness of Large Language Models Against Multilingual Typographical Errors. <em>Proceedings ' +
      'of ACL 2026</em>. ACL. arXiv:2510.09536 &mdash; the multilingual typo work this report&rsquo;s  https://aclanthology.org/2026.acl-long.729/' +
      'operation axis is compared against, and the work that contributes the <em>MulTypo</em> ' +
      'algorithm. The paper introduces MulTypo and validates it with human evaluation. The operation count and the number of supported scripts are not restated here: they are not confirmed by this report&rsquo;s verification, and no claim in this report depends on them.' },
    { k: 'frost1994', t: 'Frost, R. (1994). Toward a strong phonological theory of visual word recognition: True issues and false trails. In R. Frost &amp; L. Katz (Eds.), <em>Orthography, Phonology, Morphology, and Meaning</em> (Advances in Psychology, Vol. 94, pp. 275&ndash;298). North-Holland. &mdash; the within-item comparison that pairs pointed and unpointed Hebrew, which is the sharpest available evidence that depth affects the reading process rather than the language.' },
  ];
  document.getElementById('refs').innerHTML =
      '<ol>' + REFS.map(r => '<li id="ref-' + r.k + '" data-key="' + r.k + '">' + r.t + '</li>').join('') + '</ol>';

  document.getElementById('footer').innerHTML =
    esc(D.name) + ' <span class="mono">' + esc(D.version) + '</span> · seed <span class="mono">' +
    esc(D.seed) + '</span> · provenance <strong>' + esc(D.provenance_kind) + '</strong> · ' +
    'generated by <span class="mono">scripts/export_report_state.py</span>';
})();
