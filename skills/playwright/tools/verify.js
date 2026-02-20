'use strict';

const { escapeWithQuotes } = require('playwright-core/lib/utils');

async function verifyElement(context, params, response) {
  const tab = context.currentTabOrDie();
  const locator = tab.page.getByRole(params.role, { name: params.accessibleName });
  if (await locator.count() === 0) {
    response.addError(`Element with role "${params.role}" and accessible name "${params.accessibleName}" not found`);
    return;
  }
  response.addCode(`await expect(page.getByRole(${escapeWithQuotes(params.role, "'")}, { name: ${escapeWithQuotes(params.accessibleName, "'")} })).toBeVisible();`);
  response.addTextResult('Done');
}

async function verifyText(context, params, response) {
  const tab = context.currentTabOrDie();
  const locator = tab.page.getByText(params.text).first();
  if (await locator.count() === 0) {
    response.addError('Text not found');
    return;
  }
  response.addCode(`await expect(page.getByText(${escapeWithQuotes(params.text, "'")})).toBeVisible();`);
  response.addTextResult('Done');
}

async function verifyList(context, params, response) {
  const tab = context.currentTabOrDie();
  const { locator } = await tab.refLocator({ ref: params.ref, element: params.element });
  for (const item of params.items) {
    const itemLocator = locator.getByText(item);
    if (await itemLocator.count() === 0) {
      response.addError(`Item "${item}" not found`);
      return;
    }
  }
  response.addTextResult('Done');
}

async function verifyValue(context, params, response) {
  const tab = context.currentTabOrDie();
  const { locator, resolved } = await tab.refLocator({ ref: params.ref, element: params.element });
  if (params.type === 'textbox' || params.type === 'slider' || params.type === 'combobox') {
    const value = await locator.inputValue();
    if (value !== params.value) {
      response.addError(`Expected value "${params.value}", but got "${value}"`);
      return;
    }
    response.addCode(`await expect(page.${resolved}).toHaveValue(${escapeWithQuotes(params.value, "'")});`);
  } else if (params.type === 'checkbox' || params.type === 'radio') {
    const value = await locator.isChecked();
    if (value !== (params.value === 'true')) {
      response.addError(`Expected value "${params.value}", but got "${value}"`);
      return;
    }
    response.addCode(`await expect(page.${resolved}).${value ? 'toBeChecked' : 'not.toBeChecked'}();`);
  }
  response.addTextResult('Done');
}

async function generateLocator(context, params, response) {
  const tab = context.currentTabOrDie();
  const { resolved } = await tab.refLocator(params);
  response.addTextResult(resolved);
}

module.exports = { verifyElement, verifyText, verifyList, verifyValue, generateLocator };
