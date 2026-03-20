import BasePage from './BasePage.js';

class BulkFeeUpdatePage extends BasePage {
  constructor(page) {
    super(page);
  }

  async goto() {
    await this.navigate('/bulk-fee-update');
  }

  isAccessDenied() {
    return this.page.getByText('管理者のみアクセス可能です。').isVisible();
  }

  // Step 1: Select leases
  async selectAllLeases() {
    await this.page.locator('thead input[type="checkbox"]').check();
  }

  async selectLease(index) {
    await this.page.locator('table tbody tr').nth(index).locator('input[type="checkbox"]').check();
  }

  async goToStep2() {
    await this.page.getByRole('button', { name: '次へ' }).click();
    await this.waitForLoad();
  }

  // Step 2: Set parameters
  async setParams(data) {
    if (data.new_unit_price !== undefined) await this.page.getByPlaceholder('0').first().fill(String(data.new_unit_price));
    if (data.discount_rate !== undefined) await this.page.getByPlaceholder('0').nth(1).fill(String(data.discount_rate));
    if (data.tax_rate !== undefined) await this.page.getByPlaceholder('0.10').fill(String(data.tax_rate));
    if (data.discount_reason) await this.page.getByPlaceholder('減免事由を入力').fill(data.discount_reason);
  }

  async preview() {
    await this.page.getByRole('button', { name: 'プレビュー' }).click();
    await this.waitForLoad();
  }

  async goBack() {
    await this.page.getByRole('button', { name: '戻る' }).click();
    await this.waitForLoad();
  }

  // Step 3: Confirm
  async confirm() {
    this.page.once('dialog', async dialog => {
      await dialog.accept();
    });
    await this.page.getByRole('button', { name: '実行' }).click();
    await this.waitForLoad();
  }

  async getPreviewCount() {
    const text = await this.page.getByText(/合計：\d+件/).textContent();
    const match = text.match(/合計：(\d+)件/);
    return match ? parseInt(match[1], 10) : 0;
  }

  isSuccess() {
    return this.page.getByText('一括賃料改定が完了しました').isVisible();
  }

  async startNew() {
    await this.page.getByRole('button', { name: '新しく実行する' }).click();
    await this.waitForLoad();
  }

  getSelectedCount() {
    return this.page.getByText(/\d+件選択中/).textContent()
      .then(text => { const m = text.match(/(\d+)件/); return m ? parseInt(m[1], 10) : 0; });
  }
}

export default BulkFeeUpdatePage;
