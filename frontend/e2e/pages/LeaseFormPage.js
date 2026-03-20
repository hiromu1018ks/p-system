import BasePage from './BasePage.js';

class LeaseFormPage extends BasePage {
  constructor(page) {
    super(page);
  }

  async goto() {
    await this.navigate('/leases/new');
  }

  async gotoEdit(id) {
    await this.navigate(`/leases/${id}/edit`);
  }

  async fillForm(data) {
    if (data.property_id !== undefined) {
      await this.page.getByLabel('対象財産').selectOption({ value: String(data.property_id) });
    }
    if (data.property_sub_type) await this.page.getByLabel('財産種別').selectOption({ label: data.property_sub_type });
    if (data.lessee_name) await this.page.getByLabel('借受者氏名・法人名').fill(data.lessee_name);
    if (data.lessee_address) await this.page.getByLabel('借受者住所').fill(data.lessee_address);
    if (data.lessee_contact) await this.page.getByLabel('連絡先').fill(data.lessee_contact);
    if (data.purpose) await this.page.getByLabel('貸付目的').fill(data.purpose);
    if (data.start_date) await this.page.getByLabel('開始日').fill(data.start_date);
    if (data.end_date) await this.page.getByLabel('終了日').fill(data.end_date);
    if (data.leased_area !== undefined) await this.page.getByLabel('貸付面積・部屋番号').fill(String(data.leased_area));
    if (data.payment_method) await this.page.getByLabel('支払方法').selectOption({ label: data.payment_method });
  }

  async submit() {
    const submitBtn = this.page.getByRole('button', { name: /^(登録|更新)$/ });
    await submitBtn.click();
    await this.waitForLoad();
  }

  async cancel() {
    await this.page.getByRole('button', { name: 'キャンセル' }).click();
    await this.waitForLoad();
  }
}

export default LeaseFormPage;
