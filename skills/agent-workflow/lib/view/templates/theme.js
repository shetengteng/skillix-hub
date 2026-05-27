// dark/light theme toggle — shadcn pattern
(function () {
  var key = 'agent-workflow-theme';
  var root = document.documentElement;

  function apply(theme) {
    if (theme === 'dark') root.setAttribute('data-theme', 'dark');
    else root.removeAttribute('data-theme');
  }

  function preferred() {
    try {
      var saved = localStorage.getItem(key);
      if (saved === 'dark' || saved === 'light') return saved;
    } catch (e) {}
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
    return 'light';
  }

  var current = preferred();
  apply(current);

  function bind() {
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;
    btn.addEventListener('click', function () {
      current = (root.getAttribute('data-theme') === 'dark') ? 'light' : 'dark';
      apply(current);
      try { localStorage.setItem(key, current); } catch (e) {}
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bind);
  } else {
    bind();
  }
})();
