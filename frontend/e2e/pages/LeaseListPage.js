import BasePage from './BasePage.js';

class LeaseListPage extends BasePage {
  constructor(page) {
    super(page);
    this.searchInput = page.getByPlaceholder('借受者・目的で検索');
    this.statusFilter = page.locator('select').first();
    this.searchButton = page.getByRole('button', { name: '検索' });
    this.exportButton = page.getByRole('button', { name: 'CSVエクスポート' });
    this.newButton = page.getByRole('button', { name: '新規登録' });
  }

  async goto() {
    await this.navigate('/leases');
  }

  async search(query) {
    await this.searchInput.fill(query);
    await this.searchButton.click();
    await this.waitForLoad();
  }

  async filterByStatus(status) {
    await this.statusFilter.selectOption({ label: status });
    await this.waitForLoad();
  }

  async clickLease(index = 0) {
    await this.page.locator('table tbody tr').nth(index).click();
    await this.waitForLoad();
  }

  async clickNew() {
    await this.newButton.click();
    await this.waitForLoad();
  }

  async exportCsv() {
    const [download] = await Promise.all([
      this.page.waitForEvent('download', { timeout: 30000 }),
      this.exportButton.click(),
    ]);
    return download;
  }

  async getRowCount() {
    return this.page.locator('table tbody tr').count();
  }

  async getTotal() {
    const text = await this.page.getByText(/ページ（全 \d+ 件）/).textContent();
    const match = text.match(/全 (\d+) 件/);
    return match ? parseInt(match[1], 10) : 0;
  }

  isEmpty() {
    return this.page.getByText('案件データがありません').isVisible();
  }
}

export default LeaseListPage;
