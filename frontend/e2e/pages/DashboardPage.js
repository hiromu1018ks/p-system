import BasePage from './BasePage.js';

class DashboardPage extends BasePage {
  constructor(page) {
    super(page);
  }

  async goto() {
    await this.navigate('/dashboard');
  }

  async getKpiValues() {
    // Returns object with kpi label -> value
    const kpiLabels = ['使用許可案件中', '貸付案件中', '期限切れ間近', '今月新規'];
    const result = {};
    for (const label of kpiLabels) {
      // KPI cards have the label as a div and the value as a large number
      const container = this.page.getByText(label).locator('..');
      const value = await container.locator('div').filter({ hasText: /^\d+$/ }).first().textContent().catch(() => '0');
      result[label] = parseInt(value, 10) || 0;
    }
    return result;
  }

  async getExpiryAlerts() {
    const section = this.page.getByText('有効期限アラート').locator('..');
    const alerts = section.locator('text=あと').count();
    return alerts;
  }

  async getRecentLogs() {
    const section = this.page.getByText('最近の操作履歴').locator('..');
    const rows = section.locator('table tbody tr');
    return rows.count();
  }

  hasStatusChart() {
    return this.page.getByText('ステータス別件数').isVisible();
  }

  hasExpiryAlertsSection() {
    return this.page.getByText('有効期限アラート').isVisible();
  }

  hasRecentLogsSection() {
    return this.page.getByText('最近の操作履歴').isVisible();
  }
}
export default DashboardPage;
