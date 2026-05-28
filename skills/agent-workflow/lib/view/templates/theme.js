// dark/light theme toggle
// CSS contract: :root defines dark (default). [data-theme="light"] overrides to light.
// Therefore: data-theme="light" => light; absence (or any other value) => dark.
(function () {
  var key  = 'agent-workflow-theme';
  var root = document.documentElement;

  function apply(theme) {
    if (theme === 'light') root.setAttribute('data-theme', 'light');
    else                   root.removeAttribute('data-theme');
  }

  function preferred() {
    try {
      var saved = localStorage.getItem(key);
      if (saved === 'dark' || saved === 'light') return saved;
    } catch (e) {}
    if (window.matchMedia &&
        window.matchMedia('(prefers-color-scheme: light)').matches) return 'light';
    return 'dark';
  }

  var current = preferred();
  apply(current);

  function bind() {
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;
    btn.addEventListener('click', function () {
      current = (root.getAttribute('data-theme') === 'light') ? 'dark' : 'light';
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
