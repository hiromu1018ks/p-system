import BasePage from './BasePage.js';

class PropertyFormPage extends BasePage {
  constructor(page) {
    super(page);
  }

  async goto() {
    await this.navigate('/properties/new');
  }

  async gotoEdit(id) {
    await this.navigate(`/properties/${id}/edit`);
  }

  async fillForm(data) {
    if (data.name !== undefined) await this.page.getByLabel('財産名称').fill(data.name);
    if (data.property_type) await this.page.getByLabel('財産区分').selectOption({ label: data.property_type });
    if (data.address !== undefined) await this.page.getByLabel('所在地').fill(data.address);
    if (data.lot_number !== undefined) await this.page.getByLabel('地番').fill(data.lot_number);
    if (data.land_category) await this.page.getByLabel('地目').selectOption({ label: data.land_category });
    if (data.area_sqm !== undefined) await this.page.getByLabel('面積（㎡）').fill(String(data.area_sqm));
    if (data.acquisition_date) await this.page.getByLabel('取得年月日').fill(data.acquisition_date);
    if (data.remarks !== undefined) await this.page.getByLabel('備考').fill(data.remarks);
  }

  async submit() {
    // Wait for the submit button (登録 or 更新)
    const submitBtn = this.page.getByRole('button', { name: /^(登録|更新)$/ });
    await submitBtn.click();
    await this.waitForLoad();
  }

  async cancel() {
    await this.page.getByRole('button', { name: 'キャンセル' }).click();
    await this.waitForLoad();
  }
}

export default PropertyFormPage;
