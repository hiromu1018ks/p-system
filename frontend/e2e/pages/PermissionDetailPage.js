import BasePage from './BasePage.js';

class PermissionDetailPage extends BasePage {
  constructor(page) {
    super(page);
  }

  async goto(id) {
    await this.navigate(`/permissions/${id}`);
  }

  async getStatus() {
    // StatusBadge renders a span with status label
    const badge = this.page.locator('span').filter({ hasText: /^(下書き|申請受付済み|審査中|決裁待ち|決裁完了|交付済み|差戻し|期間終了|取消)$/ }).first();
    return badge.textContent().catch(() => '');
  }

  async transitionTo(targetStatus) {
    const transitionMap = {
      'submitted': '受付登録',
      'under_review': '審査開始',
      'rejected': '差戻し',
      'pending_approval': '決裁上申',
      'approved': '決裁完了',
      'issued': '交付済み',
    };

    const buttonLabel = transitionMap[targetStatus];
    if (!buttonLabel) throw new Error(`Unknown target status: ${targetStatus}`);

    if (targetStatus === 'rejected') {
      // Opens modal - fill reason and confirm
      await this.page.getByRole('button', { name: '差戻し' }).click();
      await this.page.locator('textarea').fill('テスト理由');
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
    // Switch to fee tab first
    await this.switchTab('料金計算');
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
    // Get the total from the fee result display
    const totalText = await this.page.getByText('税込合計').locator('..').textContent().catch(() => '');
    return totalText;
  }

  async generatePermissionPdf() {
    // Handle dialog for window.alert
    this.page.once('dialog', async dialog => {
      await dialog.accept();
    });
    await this.page.getByRole('button', { name: '使用許可証を生成' }).click();
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
export default PermissionDetailPage;
