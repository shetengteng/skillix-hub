// index.html — overview renderer + interactions.
// Reads window.__AW_DATA__ (pure JSON) and builds all DOM client-side.

(function () {
  var DATA = window.__AW_DATA__ || { runs: [] };
  var RUNS = Array.isArray(DATA.runs) ? DATA.runs : [];

  var STATUS_PILL = {
    'running':        'pill-accent',
    'awaiting_agent': 'pill-info',
    'waiting_user':   'pill-warn',
    'completed':      'pill-ok',
    'failed':         'pill-bad',
    'aborted':        'pill-dim'
  };
  var LIVE_STATUSES = { 'running': 1, 'awaiting_agent': 1, 'waiting_user': 1 };

  // ---------- helpers --------------------------------------------------------

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function pillClass(status) { return STATUS_PILL[status] || 'pill-dim'; }
  function isLive(status)    { return !!LIVE_STATUSES[status]; }

  function formatCompactTs(ts) {
    if (!ts) return '';
    if (ts.indexOf('T') === -1) return ts;
    var parts = ts.split('T');
    var date = parts[0], time = parts[1] || '';
    if (time.charAt(time.length - 1) === 'Z') time = time.slice(0, -1);
    time = time.slice(0, 8);
    if (date.length >= 10) date = date.slice(5, 10);
    return date + ' ' + time;
  }

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(sel));
  }

  function setText(name, value) {
    $$('[data-bind="' + name + '"]').forEach(function (el) {
      el.textContent = value == null ? '—' : String(value);
    });
  }
  function setHtml(slot, html) {
    var el = $('[data-slot="' + slot + '"]');
    if (el) el.innerHTML = html || '';
  }

  // ---------- aggregations ---------------------------------------------------

  function statBlocks() {
    var total = RUNS.length;
    var completed = 0, failed = 0, active = 0, aborted = 0;
    for (var i = 0; i < total; i++) {
      var st = RUNS[i].status || '';
      if (st === 'completed')      completed++;
      else if (st === 'failed')    failed++;
      else if (isLive(st))         active++;
      else if (st === 'aborted')   aborted++;
    }
    var fourthLabel, fourthVal, fourthTone;
    if (active) { fourthLabel = 'Active';  fourthVal = active;  fourthTone = 'warn'; }
    else        { fourthLabel = 'Aborted'; fourthVal = aborted; fourthTone = 'dim'; }

    return [
      stat('Total runs', total,     'accent'),
      stat('Completed',  completed, completed ? 'ok' : 'dim'),
      stat('Failed',     failed,    failed    ? 'bad' : 'dim'),
      stat(fourthLabel,  fourthVal, fourthTone)
    ].join('');
  }

  function stat(label, value, tone) {
    return '<div class="stat">' +
             '<span class="label">' + esc(label) + '</span>' +
             '<span class="value ' + tone + '">' + esc(value) + '</span>' +
           '</div>';
  }

  function aggregateWorkflows() {
    var byName = {};
    var order = [];
    for (var i = 0; i < RUNS.length; i++) {
      var r = RUNS[i];
      var name = r.workflow_name || '—';
      var b = byName[name];
      if (!b) {
        b = byName[name] = {
          name: name, total: 0, completed: 0, failed: 0,
          active: 0, aborted: 0, last_run_at: ''
        };
        order.push(name);
      }
      b.total++;
      var st = r.status || '';
      if (st === 'completed')    b.completed++;
      else if (st === 'failed')  b.failed++;
      else if (isLive(st))       b.active++;
      else if (st === 'aborted') b.aborted++;
      var ts = r.updated_at || '';
      if (ts > b.last_run_at) b.last_run_at = ts;
    }
    return order.map(function (n) { return byName[n]; })
      .sort(function (a, b) {
        if (a.last_run_at === b.last_run_at) return 0;
        return a.last_run_at < b.last_run_at ? 1 : -1;
      });
  }

  function renderWorkflowRows(wfs) {
    if (!wfs.length) {
      return '<div class="wf-empty">no workflows in this scope</div>';
    }
    return wfs.map(function (wf) {
      var breakdown = [];
      if (wf.completed) breakdown.push('<span class="bd ok"><span class="m">✓</span>' + wf.completed + '</span>');
      if (wf.active)    breakdown.push('<span class="bd warn live"><span class="m">●</span>' + wf.active + '</span>');
      if (wf.failed)    breakdown.push('<span class="bd bad"><span class="m">✕</span>' + wf.failed + '</span>');
      if (wf.aborted)   breakdown.push('<span class="bd dim"><span class="m">⊘</span>' + wf.aborted + '</span>');
      var breakdownHtml = breakdown.join(' ') || '<span class="bd dim">—</span>';
      var label = wf.total === 1 ? 'run' : 'runs';
      var compact = formatCompactTs(wf.last_run_at);
      return '<div class="wf-row" data-wf-name="' + esc(wf.name) + '">' +
               '<span class="wf-name">' + esc(wf.name) + '</span>' +
               '<span class="wf-runs">' + wf.total + ' ' + label + '</span>' +
               '<span class="wf-breakdown">' + breakdownHtml + '</span>' +
               '<span class="wf-last" title="' + esc(wf.last_run_at) + '">' +
                 esc(compact || '—') +
               '</span>' +
             '</div>';
    }).join('\n');
  }

  function renderRunRows() {
    if (!RUNS.length) {
      return '<tr><td colspan="6"><div class="runs-empty">no runs in this scope yet</div></td></tr>';
    }
    return RUNS.map(function (r) {
      var status = (r.status || '').toLowerCase();
      var liveCls = isLive(status) ? ' live' : '';
      var search = [r.run_id, r.workflow_name, r.caller, r.last_alias]
        .filter(Boolean).join(' ');
      var compact = formatCompactTs(r.updated_at);
      var tsCell = r.updated_at
        ? '<span title="' + esc(r.updated_at) + '">' + esc(compact) + '</span>'
        : '—';
      var hash = encodeURIComponent(r.run_id || '');
      return '<tr data-row data-status="' + esc(status) +
             '" data-search="' + esc(search) + '">' +
               '<td><a data-row-link href="./workflow.html#' + hash + '">' +
                 esc(r.run_id) +
               '</a></td>' +
               '<td><span class="wf-name">' + esc(r.workflow_name || '—') + '</span></td>' +
               '<td><span class="pill ' + pillClass(status) + liveCls + '">' +
                 esc(status || '?') +
               '</span></td>' +
               '<td>' + (r.history_count || 0) + '</td>' +
               '<td class="last-alias"><code>' + esc(r.last_alias || '—') + '</code></td>' +
               '<td class="ts">' + tsCell + '</td>' +
             '</tr>';
    }).join('\n');
  }

  function renderStatusOptions() {
    var seen = {};
    var statuses = [];
    for (var i = 0; i < RUNS.length; i++) {
      var s = RUNS[i].status || '?';
      if (!seen[s]) { seen[s] = 1; statuses.push(s); }
    }
    statuses.sort();
    var sel = document.getElementById('status-filter');
    if (!sel) return;
    sel.insertAdjacentHTML('beforeend', statuses.map(function (s) {
      return '<option value="' + esc(s) + '">' + esc(s) + '</option>';
    }).join(''));
  }

  // ---------- interactions ---------------------------------------------------

  function wireFilters() {
    var input      = document.getElementById('q');
    var statusSel  = document.getElementById('status-filter');
    var clearBtn   = document.getElementById('clear-filter');
    var matchCount = document.getElementById('match-count');
    var runRows    = $$('tbody tr[data-row]');
    var wfRows     = $$('.wf-row');
    var activeWf   = null;

    function applyFilter() {
      var q  = (input.value || '').toLowerCase();
      var st = statusSel.value;
      var visible = 0;
      for (var i = 0; i < runRows.length; i++) {
        var row = runRows[i];
        var text   = (row.getAttribute('data-search') || '').toLowerCase();
        var status = row.getAttribute('data-status') || '';
        var show = (!q || text.indexOf(q) !== -1) && (!st || status === st);
        row.style.display = show ? '' : 'none';
        if (show) visible++;
      }
      if (matchCount) matchCount.textContent = visible + ' / ' + runRows.length;
      if (clearBtn) clearBtn.hidden = !(q || st);
    }

    function setActiveWf(name) {
      activeWf = name;
      wfRows.forEach(function (r) {
        r.classList.toggle('is-active',
          !!name && r.getAttribute('data-wf-name') === name);
      });
    }

    function clearAll() {
      input.value = '';
      statusSel.value = '';
      setActiveWf(null);
      applyFilter();
    }

    if (!input || !statusSel) return;

    input.addEventListener('input', function () {
      if (activeWf && input.value.toLowerCase() !== activeWf.toLowerCase()) {
        setActiveWf(null);
      }
      applyFilter();
    });
    statusSel.addEventListener('change', applyFilter);
    if (clearBtn) clearBtn.addEventListener('click', clearAll);

    wfRows.forEach(function (wfRow) {
      wfRow.addEventListener('click', function () {
        var name = wfRow.getAttribute('data-wf-name') || '';
        if (activeWf === name) {
          clearAll();
        } else {
          input.value = name;
          setActiveWf(name);
          applyFilter();
          var tableWrap = document.querySelector('.runs-table-wrap');
          if (tableWrap && tableWrap.scrollIntoView) {
            tableWrap.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
          }
        }
      });
    });

    runRows.forEach(function (row) {
      var link = row.querySelector('a[data-row-link]');
      if (!link) return;
      row.addEventListener('click', function (e) {
        if (e.target.tagName === 'A') return;
        window.location.href = link.getAttribute('href');
      });
    });

    applyFilter();
  }

  function init() {
    setText('total-runs',     RUNS.length);
    setText('project-root',   DATA.project_root || '.');
    setText('generated-at',   DATA.generated_at || '—');

    var wfs = aggregateWorkflows();
    setText('workflow-count', wfs.length);
    setHtml('stat-blocks',    statBlocks());
    setHtml('workflow-rows',  renderWorkflowRows(wfs));
    setHtml('run-rows',       renderRunRows());
    renderStatusOptions();

    wireFilters();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
