'use strict';

async function fillForm(context, params, response) {
  const tab = context.currentTabOrDie();
  for (const field of params.fields) {
    const { locator, resolved } = await tab.refLocator({ element: field.name, ref: field.ref });
    const src = `await page.${resolved}`;
    if (field.type === 'textbox' || field.type === 'slider') {
      try {
        await locator.fill(field.value);
        response.addCode(`${src}.fill('${field.value}');`);
      } catch {
        try {
          await locator.locator('input, textarea').first().fill(field.value);
          response.addCode(`${src}.locator('input, textarea').first().fill('${field.value}');`);
        } catch {
          await locator.click();
          await locator.pressSequentially(field.value);
          response.addCode(`${src}.click();\n${src}.pressSequentially('${field.value}');`);
        }
      }
    } else if (field.type === 'checkbox' || field.type === 'radio') {
      await locator.setChecked(field.value === 'true');
      response.addCode(`${src}.setChecked(${field.value});`);
    } else if (field.type === 'combobox') {
      try {
        await locator.selectOption({ label: field.value });
        response.addCode(`${src}.selectOption('${field.value}');`);
      } catch {
        await locator.click();
        response.addCode(`${src}.click();`);
        const option = tab.page.getByRole('option', { name: field.value }).first();
        await option.waitFor({ state: 'visible', timeout: context.config.timeouts.action });
        await option.click();
        response.addCode(`await page.getByRole('option', { name: '${field.value}' }).first().click();`);
      }
    }
  }
}

module.exports = { fillForm };
