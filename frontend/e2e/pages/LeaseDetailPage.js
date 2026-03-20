import BasePage from './BasePage.js';

class LeaseDetailPage extends BasePage {
  constructor(page) {
    super(page);
  }

  async goto(id) {
    await this.navigate(`/leases/${id}`);
  }

  async getStatus() {
    const badge = this.page.locator('span').filter({ hasText: /^(下書き|協議中|決裁待ち|契約中|期間終了|解約)$/ }).first();
    return badge.textContent().catch(() => '');
  }

  async transitionTo(targetStatus) {
    const transitionMap = {
      'negotiating': '協議開始',
      'pending_approval': '決裁上申',
      'active': '決裁完了',
      'terminated': '解約',
    };

    const buttonLabel = transitionMap[targetStatus];
    if (!buttonLabel) throw new Error(`Unknown target status: ${targetStatus}`);

    if (targetStatus === 'terminated') {
      // Opens modal
      await this.page.getByRole('button', { name: '解約' }).click();
      await this.page.locator('textarea').fill('テスト解約理由');
      await this.page.getByRole('button', { name: '実行' }).click();
    } else {
      await this.page.getByRole('button', { name: buttonLabel }).click();
    }
    await this.waitForLoad();
  }

  async startRenewal() {
    this.page.once('dialog', async dialog => {
      await dialog.accept();
    });
    await this.page.getByRole('button', { name: '更新手続きを開始' }).click();
    await this.waitForLoad();
  }

  async switchTab(tabName) {
    await this.page.getByRole('button', { name: tabName, exact: true }).click();
    await this.waitForLoad();
  }

  async calculateFee(params) {
    await this.switchTab('賃料計算');
    if (params.unit_price) await this.page.getByLabel('単価（円/㎡/月）').fill(String(params.unit_price));
    if (params.area_sqm) await this.page.getByLabel('面積（㎡）').fill(String(params.area_sqm));
    if (params.start_date) await this.page.getByLabel('開始日').fill(params.start_date);
    if (params.end_date) await this.page.getByLabel('終了日').fill(params.end_date);
    if (params.discount_rate !== undefined) await this.page.getByLabel('減額率（%）').fill(String(params.discount_rate));
    if (params.tax_rate) await this.page.getByLabel('課税').selectOption({ label: params.tax_rate });
    await this.page.getByRole('button', { name: '計算' }).click();
    await this.waitForLoad();
  }

  async getFeeResult() {
    const totalText = await this.page.getByText('税込合計').locator('..').textContent().catch(() => '');
    return totalText;
  }

  async generateLandLeasePdf() {
    this.page.once('dialog', async dialog => {
      await dialog.accept();
    });
    await this.page.getByRole('button', { name: '土地貸付契約書を生成' }).click();
    await this.waitForLoad();
  }

  async generateBuildingLeasePdf() {
    this.page.once('dialog', async dialog => {
      await dialog.accept();
    });
    await this.page.getByRole('button', { name: '建物貸付契約書を生成' }).click();
    await this.waitForLoad();
  }

  async generateRenewalPdf() {
    this.page.once('dialog', async dialog => {
      await dialog.accept();
    });
    await this.page.getByRole('button', { name: '更新通知文を生成' }).click();
    await this.waitForLoad();
  }

  async downloadLatestPdf() {
    this.page.once('dialog', async dialog => {
      await dialog.accept();
    });
    const [download] = await Promise.all([
      this.page.waitForEvent('download', { timeout: 60000 }),
      this.page.getByRole('button', { name: '直近のPDFをダウンロード' }).click(),
    ]);
    return download;
  }

  async uploadFile(filePath) {
    const fileInput = this.page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    await this.waitForLoad();
  }

  async getFileCount() {
    return this.page.locator('table tbody tr').count();
  }

  async getHistoryCount() {
    return this.page.locator('table tbody tr').count();
  }

  async clickEdit() {
    await this.page.getByRole('button', { name: '編集' }).click();
    await this.waitForLoad();
  }

  async clickDelete() {
    this.page.once('dialog', async dialog => {
      await dialog.accept();
    });
    await this.page.getByRole('button', { name: '削除' }).click();
    await this.waitForLoad();
  }
}

export default LeaseDetailPage;
