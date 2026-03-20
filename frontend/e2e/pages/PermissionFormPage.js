import BasePage from './BasePage.js';

class PermissionFormPage extends BasePage {
  constructor(page) {
    super(page);
  }

  async goto() {
    await this.navigate('/permissions/new');
  }

  async gotoEdit(id) {
    await this.navigate(`/permissions/${id}/edit`);
  }

  async fillForm(data) {
    if (data.property_id !== undefined) {
      await this.page.getByLabel('対象財産').selectOption({ value: String(data.property_id) });
    }
    if (data.applicant_name) await this.page.getByLabel('申請者氏名').fill(data.applicant_name);
    if (data.applicant_address) await this.page.getByLabel('申請者住所').fill(data.applicant_address);
    if (data.purpose) await this.page.getByLabel('使用目的').fill(data.purpose);
    if (data.start_date) await this.page.getByLabel('開始日').fill(data.start_date);
    if (data.end_date) await this.page.getByLabel('終了日').fill(data.end_date);
    if (data.usage_area_sqm !== undefined) await this.page.getByLabel('使用面積（㎡）').fill(String(data.usage_area_sqm));
    if (data.conditions) await this.page.getByLabel('許可条件・特記事項').fill(data.conditions);
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
export default PermissionFormPage;
