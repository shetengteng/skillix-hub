// overview — client-side search & filter
(function () {
  var input = document.getElementById('q');
  var statusSel = document.getElementById('status-filter');
  var rows = Array.prototype.slice.call(document.querySelectorAll('tbody tr[data-row]'));
  var matchCount = document.getElementById('match-count');

  function applyFilter() {
    var q = (input.value || '').toLowerCase();
    var st = statusSel.value;
    var visible = 0;
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var text = row.getAttribute('data-search') || '';
      var status = row.getAttribute('data-status') || '';
      var matchQ = !q || text.toLowerCase().indexOf(q) !== -1;
      var matchS = !st || status === st;
      var show = matchQ && matchS;
      row.style.display = show ? '' : 'none';
      if (show) visible++;
    }
    if (matchCount) matchCount.textContent = visible + ' / ' + rows.length;
  }

  input.addEventListener('input', applyFilter);
  statusSel.addEventListener('change', applyFilter);
  applyFilter();

  // 整行可点击 — 点击 row 跳转
  rows.forEach(function (row) {
    var link = row.querySelector('a[data-row-link]');
    if (!link) return;
    row.style.cursor = 'pointer';
    row.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') return;
      window.location.href = link.getAttribute('href');
    });
  });
})();
