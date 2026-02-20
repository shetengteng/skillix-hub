'use strict';

const { Tab } = require('./tab');

class Context {
  constructor(config, browserContext) {
    this.config = config;
    this._browserContext = browserContext;
    this._tabs = [];
    this._currentTab = undefined;
    this._routes = [];

    for (const page of browserContext.pages())
      this._onPageCreated(page);
    browserContext.on('page', page => this._onPageCreated(page));
  }

  _onPageCreated(page) {
    const tab = new Tab(this, page, t => this._onPageClosed(t));
    this._tabs.push(tab);
    if (!this._currentTab)
      this._currentTab = tab;
  }

  _onPageClosed(tab) {
    const index = this._tabs.indexOf(tab);
    if (index === -1) return;
    this._tabs.splice(index, 1);
    if (this._currentTab === tab)
      this._currentTab = this._tabs[Math.min(index, this._tabs.length - 1)];
  }

  tabs() {
    return this._tabs;
  }

  currentTab() {
    return this._currentTab;
  }

  currentTabOrDie() {
    if (!this._currentTab)
      throw new Error('No open pages available.');
    return this._currentTab;
  }

  async newTab() {
    const page = await this._browserContext.newPage();
    this._currentTab = this._tabs.find(t => t.page === page);
    return this._currentTab;
  }

  async selectTab(index) {
    const tab = this._tabs[index];
    if (!tab) throw new Error(`Tab ${index} not found`);
    await tab.page.bringToFront();
    this._currentTab = tab;
    return tab;
  }

  async ensureTab() {
    if (!this._currentTab)
      await this._browserContext.newPage();
    return this._currentTab;
  }

  async closeTab(index) {
    const tab = index === undefined ? this._currentTab : this._tabs[index];
    if (!tab) throw new Error(`Tab ${index} not found`);
    const url = tab.page.url();
    await tab.page.close();
    return url;
  }

  async ensureBrowserContext() {
    return this._browserContext;
  }

  routes() {
    return this._routes;
  }

  async addRoute(entry) {
    await this._browserContext.route(entry.pattern, entry.handler);
    this._routes.push(entry);
  }

  async removeRoute(pattern) {
    if (!pattern) {
      for (const route of this._routes)
        await this._browserContext.unroute(route.pattern, route.handler);
      const count = this._routes.length;
      this._routes = [];
      return count;
    }
    const toRemove = this._routes.filter(r => r.pattern === pattern);
    for (const route of toRemove)
      await this._browserContext.unroute(route.pattern, route.handler);
    this._routes = this._routes.filter(r => r.pattern !== pattern);
    return toRemove.length;
  }

  async closeBrowserContext() {
    await this._browserContext.close().catch(() => {});
  }
}

module.exports = { Context };
