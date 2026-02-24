() => {
  window.scrollTo(0, document.body.scrollHeight);

  const sections = [];
  const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
  if (headings.length === 0) {
    const body = document.body.innerText.trim();
    sections.push({ heading: '', level: 1, content: body, codeBlocks: [], tables: [], links: [] });
  } else {
    for (let i = 0; i < headings.length; i++) {
      const h = headings[i];
      const level = parseInt(h.tagName[1]);
      const heading = h.innerText.trim();
      let content = '';
      let sibling = h.nextElementSibling;
      const codeBlocks = [];
      const tables = [];
      while (sibling && !sibling.matches('h1, h2, h3, h4, h5, h6')) {
        if (sibling.matches('pre, code')) {
          const lang = sibling.className.match(/language-(\\w+)/);
          codeBlocks.push({ language: lang ? lang[1] : '', code: sibling.innerText.trim() });
        } else if (sibling.matches('table')) {
          const rows = [];
          sibling.querySelectorAll('tr').forEach(tr => {
            const cells = [];
            tr.querySelectorAll('th, td').forEach(cell => cells.push(cell.innerText.trim()));
            rows.push(cells);
          });
          tables.push(rows);
        } else {
          content += sibling.innerText.trim() + '\\n';
        }
        sibling = sibling.nextElementSibling;
      }
      sections.push({ heading, level, content: content.trim(), codeBlocks, tables, links: [] });
    }
  }

  const links = [];
  document.querySelectorAll('a[href]').forEach(a => {
    const href = a.getAttribute('href');
    const text = a.innerText.trim();
    if (href && text && !href.startsWith('#') && !href.startsWith('javascript:')) {
      links.push({ href, text });
    }
  });

  return { title: document.title, sections, links };
}
