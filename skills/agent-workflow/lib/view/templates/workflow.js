// workflow.html — hash-driven single-run renderer.
// Reads window.__AW_DATA__ (pure JSON), selects the run by location.hash,
// and builds the DOM client-side.

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

  function pad2(n) { n = String(n); return n.length < 2 ? '0' + n : n; }

  function formatDuration(ms) {
    if (ms == null) return '—';
    ms = parseInt(ms, 10);
    if (isNaN(ms) || ms < 0) return '—';
    if (ms < 1000)    return ms + 'ms';
    if (ms < 60000)   return (ms / 1000).toFixed(2) + 's';
    if (ms < 3600000) {
      var s = Math.floor(ms / 1000);
      return Math.floor(s / 60) + 'm' + pad2(s % 60) + 's';
    }
    var s2 = Math.floor(ms / 1000);
    return Math.floor(s2 / 3600) + 'h' + pad2(Math.floor((s2 % 3600) / 60)) + 'm';
  }

  function formatShortTs(ts) {
    if (!ts) return '';
    if (ts.indexOf('T') === -1) return ts;
    var t = ts.split('T')[1] || '';
    if (t.charAt(t.length - 1) === 'Z') t = t.slice(0, -1);
    return t.slice(0, 8);
  }

  function truncate(s, limit) {
    s = String(s == null ? '' : s);
    if (s.length <= limit) return s;
    return s.slice(0, Math.max(1, limit - 1)) + '…';
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
    $$('[data-slot="' + slot + '"]').forEach(function (el) {
      el.innerHTML = html || '';
    });
  }

  // ---------- status pill ----------------------------------------------------

  function statusPill(status) {
    var s = (status || '?').toLowerCase();
    var live = isLive(s);
    return '<span class="pill ' + pillClass(s) + (live ? ' live' : '') + '">' +
             esc(s) +
           '</span>';
  }

  // ---------- timeline node --------------------------------------------------

  function renderNode(n) {
    var classes = ['tnode'];
    if (n.indent > 0) classes.push('indent-' + Math.min(n.indent, 2));
    if (n.is_cursor)  classes.push('is-cursor');
    if (n.is_loop)    classes.push('is-loop');

    return '<div class="' + classes.join(' ') + '" data-status="' + esc(n.status || '') + '">' +
             '<span class="marker" aria-hidden="true"></span>' +
             '<div class="body">' +
               '<div class="head">' +
                 '<span class="alias">' + esc(n.alias || '(unnamed)') + '</span>' +
                 (n.is_cursor ? '<span class="cursor-flag">cursor</span>' : '') +
               '</div>' +
               renderNodeSub(n) +
             '</div>' +
             '<div class="timing">' + renderNodeTiming(n) + '</div>' +
           '</div>';
  }

  function renderNodeSub(n) {
    var ntype = (n.type || '').toString().trim();
    var tokens = [];
    if (ntype) tokens.push('<span class="ntype">' + esc(ntype) + '</span>');

    if (ntype === 'agent_call') {
      if (n.executor && n.output) {
        tokens.push(
          '<span class="flow">' +
            '<span class="val">' + esc(n.executor) + '</span>' +
            ' <span class="arr">→</span> ' +
            '<span class="val">' + esc(n.output) + '</span>' +
          '</span>'
        );
      } else if (n.executor) {
        tokens.push('<span class="val">' + esc(n.executor) + '</span>');
      } else if (n.output) {
        tokens.push('<span class="val">' + esc(n.output) + '</span>');
      }
    } else if (ntype === 'sleep') {
      if (n.seconds != null) {
        tokens.push('<span class="val">' + esc(n.seconds) + 's</span>');
      }
    } else if (ntype === 'loop') {
      if (n.max_iterations != null) {
        tokens.push(
          '<span class="kv">max <span class="val">' + esc(n.max_iterations) + '</span></span>'
        );
      }
      if (n.condition) {
        tokens.push(
          '<span class="kv">while <span class="val" title="' + esc(n.condition) + '">' +
            esc(truncate(n.condition, 44)) +
          '</span></span>'
        );
      }
    }

    var sub = '';
    if (tokens.length) {
      sub = '<div class="sub">' +
              tokens.join('<span class="sep">·</span>') +
            '</div>';
    }
    if (n.description) {
      sub += '<div class="desc">' + esc(n.description) + '</div>';
    }
    return sub;
  }

  function renderNodeTiming(n) {
    if (!n.iter_count) return '';
    var parts = [];
    if (n.iter_count > 1) {
      parts.push('<span class="iters">×' + n.iter_count + '</span>');
    }
    if (n.total_duration_ms != null) {
      parts.push('<span class="dur">' + esc(formatDuration(n.total_duration_ms)) + '</span>');
    }
    if (n.last_ts) {
      parts.push(
        '<span class="ts" title="' + esc(n.last_ts) + '">' +
          esc(formatShortTs(n.last_ts)) +
        '</span>'
      );
    }
    return parts.join('');
  }

  function renderTimeline(nodes) {
    if (!nodes || !nodes.length) {
      return '<div class="timeline-empty">no nodes</div>';
    }
    return nodes.map(renderNode).join('\n');
  }

  // ---------- metric blocks --------------------------------------------------

  function metric(label, value, tone) {
    return '<div class="metric">' +
             '<span class="label">' + esc(label) + '</span>' +
             '<span class="value' + (tone ? ' ' + tone : '') + '">' + esc(value) + '</span>' +
           '</div>';
  }

  function renderMetrics(run) {
    var status = run.status || '';
    var runtime = run.runtime_ms != null ? formatDuration(run.runtime_ms) : '—';
    var avg     = run.avg_step_ms != null ? formatDuration(run.avg_step_ms) : '—';

    var cursorStr, cursorTone;
    if (status === 'completed') { cursorStr = 'complete'; cursorTone = 'ok'; }
    else if (status === 'failed')  { cursorStr = 'failed';   cursorTone = 'bad'; }
    else if (status === 'aborted') { cursorStr = 'aborted';  cursorTone = 'dim'; }
    else if (run.cursor_alias)     { cursorStr = run.cursor_alias; cursorTone = 'accent'; }
    else                            { cursorStr = '—';        cursorTone = 'dim'; }

    return [
      metric('Steps run', run.history_count || 0, 'accent'),
      metric('Runtime',   runtime),
      metric('Nodes',     run.node_count_top || 0),
      metric('Cursor',    cursorStr, cursorTone),
      metric('Avg step',  avg),
      metric('Caller',    run.caller || '—')
    ].join('');
  }

  // ---------- event row ------------------------------------------------------

  function renderEvent(e) {
    var etype = e.type || '?';
    var hasErrorCode = Object.prototype.hasOwnProperty.call(e, 'error_code');
    var endsWithFailed = (etype.length >= 4 &&
                          etype.slice(-4) === '_end' &&
                          e.status === 'failed');
    var cls = '';
    if (etype === 'error' || hasErrorCode || endsWithFailed) cls = 'error';
    else if (etype === 'run_end' && e.status === 'completed') cls = 'success';

    var fields = [];
    Object.keys(e).forEach(function (k) {
      if (k === 'ts' || k === 'type') return;
      var v = e[k];
      var val = (v != null && typeof v === 'object') ? JSON.stringify(v)
                                                     : (v == null ? '' : String(v));
      fields.push(
        '<span class="k">' + esc(k) + '</span>' +
        '<span class="eq">=</span>' +
        '<code>' + esc(val) + '</code>'
      );
    });

    return '<div class="evt' + (cls ? ' ' + cls : '') + '">' +
             '<span class="ts">' + esc(e.ts || '') + '</span>' +
             '<span class="type">' + esc(etype) + '</span>' +
             '<span class="fields">' + fields.join(' ') + '</span>' +
           '</div>';
  }

  function renderEvents(events) {
    if (!events || !events.length) {
      return '<div class="evt"><span class="ts">—</span>' +
             '<span class="type">empty</span>' +
             '<span class="fields">no events recorded yet</span></div>';
    }
    return events.map(renderEvent).join('\n');
  }

  // ---------- payload / error / vars -----------------------------------------

  function renderPanel(title, meta, pre) {
    return '<div class="panel">' +
             '<div class="panel-head">' +
               '<span>' + esc(title) + '</span>' +
               '<span class="panel-meta">' + esc(meta) + '</span>' +
             '</div>' +
             '<div class="panel-body no-pad"><pre>' + esc(pre) + '</pre></div>' +
           '</div>';
  }

  function renderLastPayload(payload) {
    if (payload == null) return '';
    var pretty = JSON.stringify(payload, null, 2);
    return renderPanel('Last payload', 'caller handoff', pretty);
  }

  function renderErrorBlock(error) {
    if (error == null) return '';
    var code = (error && error.code) || 'ERROR';
    var pretty = JSON.stringify(error, null, 2);
    return '<div class="raw-block error-block panel" style="margin-bottom:24px;">' +
             '<div class="panel-head">' +
               '<span>Error · ' + esc(code) + '</span>' +
               '<span class="panel-meta">last failure</span>' +
             '</div>' +
             '<div class="panel-body no-pad"><pre>' + esc(pretty) + '</pre></div>' +
           '</div>';
  }

  // ---------- main routing ---------------------------------------------------

  function findRun(rid) {
    if (!rid) return null;
    for (var i = 0; i < RUNS.length; i++) {
      if (RUNS[i].run_id === rid) return RUNS[i];
    }
    return null;
  }

  function getRunId() {
    var raw = (location.hash || '').replace(/^#/, '');
    try { raw = decodeURIComponent(raw); } catch (e) {}
    return raw.trim();
  }

  function renderNotFound(rid) {
    document.title = 'agent-workflow · run not found';
    setText('workflow-name', '(unknown)');
    setText('run-id', rid || '—');
    setText('caller', '—');
    setText('created-at', '—');
    setText('updated-at', '—');
    setText('node-count', 0);
    setText('history-count', 0);
    setText('event-count', 0);
    setText('telemetry-meta', 'no data');
    setText('generated-at', DATA.generated_at || '—');
    setHtml('status-pill',
      '<span class="pill pill-dim">not found</span>');
    setHtml('timeline',
      '<div class="timeline-empty">' +
      'no data for run <code>' + esc(rid || '∅') + '</code>. ' +
      're-run <code>view</code> to refresh.' +
      '</div>');
    setHtml('metric-blocks', '');
    setHtml('events',
      '<div class="evt"><span class="ts">—</span>' +
      '<span class="type">empty</span>' +
      '<span class="fields">no events</span></div>');
    setHtml('last-payload', '');
    setHtml('error-block', '');
    var pre = $('[data-slot="vars-pretty"]');
    if (pre) pre.textContent = '{}';
  }

  function renderRun(run) {
    document.title = 'agent-workflow · ' + (run.workflow_name || 'run') + ' · ' + run.run_id;

    setText('workflow-name', run.workflow_name || 'workflow');
    setText('run-id',        run.run_id || '—');
    setText('caller',        run.caller || '—');
    setText('created-at',    run.created_at || '—');
    setText('updated-at',    run.updated_at || '—');
    setText('node-count',    run.node_count_top || 0);
    setText('history-count', run.history_count || 0);
    setText('event-count',   run.event_count || 0);
    setText('telemetry-meta', run.status || 'snapshot');
    setText('generated-at',  DATA.generated_at || '—');

    setHtml('status-pill',   statusPill(run.status));
    setHtml('error-block',   renderErrorBlock(run.error));
    setHtml('timeline',      renderTimeline(run.nodes));
    setHtml('metric-blocks', renderMetrics(run));
    setHtml('events',        renderEvents(run.events));
    setHtml('last-payload',  renderLastPayload(run.last_payload));

    var pre = $('[data-slot="vars-pretty"]');
    if (pre) {
      pre.textContent = run.vars
        ? JSON.stringify(run.vars, null, 2)
        : '{}';
    }
  }

  function route() {
    var rid = getRunId();
    var run = findRun(rid);
    if (run) renderRun(run);
    else     renderNotFound(rid);
  }

  function init() {
    route();
    window.addEventListener('hashchange', route);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
