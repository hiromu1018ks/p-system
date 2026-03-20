import { test, expect } from '../fixtures/auth.js';
import { api } from '../helpers/api.js';

test.describe('PDF生成', () => {
  let token, propertyId;

  test.beforeAll(async () => {
    const loginData = await api.login('admin', 'Admin123');
    token = loginData.access_token;
    const prop = await api.createProperty(token, { name: 'PDFテスト財産', property_type: 'administrative' });
    propertyId = prop.id;
  });

  test.setTimeout(60_000);

  test('使用許可許可書PDF生成 (API)', async () => {
    // Create permission and advance to approved
    const perm = await api.createPermission(token, {
      property_id: propertyId, applicant_name: 'PDF申請者', applicant_address: 'テスト',
      purpose: 'PDFテスト', start_date: '2025-04-01', end_date: '2026-03-31',
    });
    let updated = perm;
    for (const status of ['submitted', 'under_review', 'pending_approval', 'approved']) {
      updated = await api.changePermissionStatus(token, perm.id, {
        new_status: status, reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
      });
    }

    const pdf = await api.generatePermissionPdf(token, updated.id);
    expect(pdf.document_type).toBe('permission_certificate');
    expect(pdf.filename).toContain('.pdf');
  });

  test('土地賃貸借契約書PDF生成 (API)', async () => {
    const lease = await api.createLease(token, {
      property_id: propertyId, property_sub_type: 'land', lessee_name: 'PDF借受者',
      lessee_address: 'テスト', purpose: 'PDFテスト', start_date: '2025-04-01', end_date: '2026-03-31',
    });
    let updated = lease;
    for (const status of ['negotiating', 'pending_approval', 'active']) {
      updated = await api.changeLeaseStatus(token, lease.id, {
        new_status: status, reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
      });
    }

    const pdf = await api.generateLandLeasePdf(token, updated.id);
    expect(pdf.document_type).toBe('land_lease_contract');
    expect(pdf.filename).toContain('.pdf');
  });

  test('建物賃貸借契約書PDF生成 (API)', async () => {
    const lease = await api.createLease(token, {
      property_id: propertyId, property_sub_type: 'building', lessee_name: 'PDF建物借受者',
      lessee_address: 'テスト', purpose: 'PDFテスト', start_date: '2025-04-01', end_date: '2026-03-31',
    });
    let updated = lease;
    for (const status of ['negotiating', 'pending_approval', 'active']) {
      updated = await api.changeLeaseStatus(token, lease.id, {
        new_status: status, reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
      });
    }

    const pdf = await api.generateBuildingLeasePdf(token, updated.id);
    expect(pdf.document_type).toBe('building_lease_contract');
  });

  test('PDFダウンロード (API)', async () => {
    // Generate a PDF first, then download it
    const perm = await api.createPermission(token, {
      property_id: propertyId, applicant_name: 'DL申請者', applicant_address: 'テスト',
      purpose: 'DLテスト', start_date: '2025-04-01', end_date: '2026-03-31',
    });
    let updated = perm;
    for (const status of ['submitted', 'under_review', 'pending_approval', 'approved']) {
      updated = await api.changePermissionStatus(token, perm.id, {
        new_status: status, reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
      });
    }

    const pdf = await api.generatePermissionPdf(token, updated.id);
    const response = await api.downloadPdf(token, pdf.id);
    expect(response.status).toBe(200);
  });

  test('使用許可証を生成 (UI)', async ({ adminPage }) => {
    const perm = await api.createPermission(token, {
      property_id: propertyId, applicant_name: 'UI申請者', applicant_address: 'テスト',
      purpose: 'UIテスト', start_date: '2025-04-01', end_date: '2026-03-31',
    });
    let updated = perm;
    for (const status of ['submitted', 'under_review', 'pending_approval', 'approved']) {
      updated = await api.changePermissionStatus(token, perm.id, {
        new_status: status, reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
      });
    }

    await adminPage.goto(`/permissions/${updated.id}`);
    await adminPage.waitForLoadState('networkidle');

    await adminPage.getByRole('button', { name: '使用許可証を生成' }).click();
    await adminPage.waitForLoadState('networkidle');
  });
});
