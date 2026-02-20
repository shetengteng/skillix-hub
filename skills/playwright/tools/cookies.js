'use strict';

async function cookieList(context, params, response) {
  const bc = await context.ensureBrowserContext();
  let cookies = await bc.cookies();
  if (params.domain) cookies = cookies.filter(c => c.domain.includes(params.domain));
  if (params.path) cookies = cookies.filter(c => c.path.startsWith(params.path));
  if (cookies.length === 0)
    response.addTextResult('No cookies found');
  else
    response.addTextResult(cookies.map(c => `${c.name}=${c.value} (domain: ${c.domain}, path: ${c.path})`).join('\n'));
}

async function cookieGet(context, params, response) {
  const bc = await context.ensureBrowserContext();
  const cookies = await bc.cookies();
  const cookie = cookies.find(c => c.name === params.name);
  if (!cookie)
    response.addTextResult(`Cookie '${params.name}' not found`);
  else
    response.addTextResult(`${cookie.name}=${cookie.value} (domain: ${cookie.domain}, path: ${cookie.path}, httpOnly: ${cookie.httpOnly}, secure: ${cookie.secure}, sameSite: ${cookie.sameSite})`);
}

async function cookieSet(context, params, response) {
  const bc = await context.ensureBrowserContext();
  const tab = await context.ensureTab();
  const url = new URL(tab.page.url());
  const cookie = {
    name: params.name,
    value: params.value,
    domain: params.domain || url.hostname,
    path: params.path || '/',
  };
  if (params.expires !== undefined) cookie.expires = params.expires;
  if (params.httpOnly !== undefined) cookie.httpOnly = params.httpOnly;
  if (params.secure !== undefined) cookie.secure = params.secure;
  if (params.sameSite !== undefined) cookie.sameSite = params.sameSite;
  await bc.addCookies([cookie]);
  response.addTextResult(`Cookie '${params.name}' set.`);
}

async function cookieDelete(context, params, response) {
  const bc = await context.ensureBrowserContext();
  await bc.clearCookies({ name: params.name });
  response.addTextResult(`Cookie '${params.name}' deleted.`);
}

async function cookieClear(context, params, response) {
  const bc = await context.ensureBrowserContext();
  await bc.clearCookies();
  response.addTextResult('All cookies cleared.');
}

module.exports = { cookieList, cookieGet, cookieSet, cookieDelete, cookieClear };
