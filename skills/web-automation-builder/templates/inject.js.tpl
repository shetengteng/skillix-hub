(function() {
  if (window.__WAB_INJECTED__) return;
  window.__WAB_INJECTED__ = true;
  window.__WAB_EVENTS__ = [];

  function cssSelector(el) {
    if (el.id) return '#' + CSS.escape(el.id);
    if (el.getAttribute('data-testid')) return '[data-testid="' + el.getAttribute('data-testid') + '"]';
    if (el.getAttribute('name')) return el.tagName.toLowerCase() + '[name="' + el.getAttribute('name') + '"]';

    var parts = [];
    var cur = el;
    while (cur && cur !== document.body && cur !== document.documentElement) {
      var tag = cur.tagName.toLowerCase();
      if (cur.id) { parts.unshift('#' + CSS.escape(cur.id)); break; }
      var parent = cur.parentElement;
      if (parent) {
        var siblings = Array.from(parent.children).filter(function(c) { return c.tagName === cur.tagName; });
        if (siblings.length > 1) {
          var idx = siblings.indexOf(cur) + 1;
          tag += ':nth-of-type(' + idx + ')';
        }
      }
      parts.unshift(tag);
      cur = parent;
    }
    return parts.join(' > ');
  }

  function locators(el) {
    return {
      css: cssSelector(el),
      text: (el.textContent || '').trim().substring(0, 100) || null,
      role: el.getAttribute('role') || el.tagName.toLowerCase(),
      ariaLabel: el.getAttribute('aria-label') || null,
      placeholder: el.getAttribute('placeholder') || null,
      testId: el.getAttribute('data-testid') || null,
      name: el.getAttribute('name') || null,
      id: el.id || null,
      tagName: el.tagName.toLowerCase(),
      type: el.getAttribute('type') || null
    };
  }

  function push(evt) {
    evt.timestamp = new Date().toISOString();
    evt.url = location.href;
    window.__WAB_EVENTS__.push(evt);
  }

  document.addEventListener('click', function(e) {
    var el = e.target;
    if (!el || !el.tagName) return;
    push({ type: 'click', locators: locators(el) });
  }, true);

  var inputTimers = {};
  document.addEventListener('input', function(e) {
    var el = e.target;
    if (!el || !el.tagName) return;
    var key = cssSelector(el);
    clearTimeout(inputTimers[key]);
    inputTimers[key] = setTimeout(function() {
      push({
        type: 'input',
        locators: locators(el),
        value: el.value || ''
      });
      delete inputTimers[key];
    }, 300);
  }, true);

  document.addEventListener('change', function(e) {
    var el = e.target;
    if (!el || !el.tagName) return;
    var tag = el.tagName.toLowerCase();
    if (tag === 'select') {
      push({
        type: 'select',
        locators: locators(el),
        value: el.value,
        selectedText: el.options[el.selectedIndex] ? el.options[el.selectedIndex].text : ''
      });
    } else if (el.type === 'checkbox' || el.type === 'radio') {
      push({
        type: el.type === 'checkbox' ? 'check' : 'radio',
        locators: locators(el),
        checked: el.checked
      });
    }
  }, true);

  document.addEventListener('submit', function(e) {
    var form = e.target;
    if (!form || form.tagName.toLowerCase() !== 'form') return;
    push({ type: 'submit', locators: locators(form) });
  }, true);

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' || e.key === 'Tab' || e.key === 'Escape') {
      push({
        type: 'keydown',
        key: e.key,
        locators: locators(e.target),
        modifiers: {
          ctrl: e.ctrlKey,
          shift: e.shiftKey,
          alt: e.altKey,
          meta: e.metaKey
        }
      });
    }
  }, true);

  var lastUrl = location.href;
  var observer = new MutationObserver(function() {
    if (location.href !== lastUrl) {
      push({ type: 'navigation', fromUrl: lastUrl, toUrl: location.href });
      lastUrl = location.href;
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });

  window.addEventListener('popstate', function() {
    if (location.href !== lastUrl) {
      push({ type: 'navigation', fromUrl: lastUrl, toUrl: location.href });
      lastUrl = location.href;
    }
  });

  window.addEventListener('hashchange', function(e) {
    push({ type: 'navigation', fromUrl: e.oldURL, toUrl: e.newURL });
    lastUrl = location.href;
  });
})();
