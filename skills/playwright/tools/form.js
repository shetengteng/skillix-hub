'use strict';

async function fillForm(context, params, response) {
  const tab = context.currentTabOrDie();
  for (const field of params.fields) {
    const { locator, resolved } = await tab.refLocator({ element: field.name, ref: field.ref });
    const src = `await page.${resolved}`;
    if (field.type === 'textbox' || field.type === 'slider') {
      await locator.fill(field.value);
      response.addCode(`${src}.fill('${field.value}');`);
    } else if (field.type === 'checkbox' || field.type === 'radio') {
      await locator.setChecked(field.value === 'true');
      response.addCode(`${src}.setChecked(${field.value});`);
    } else if (field.type === 'combobox') {
      await locator.selectOption({ label: field.value });
      response.addCode(`${src}.selectOption('${field.value}');`);
    }
  }
}

module.exports = { fillForm };
