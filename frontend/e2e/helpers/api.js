const BASE_URL = 'http://127.0.0.1:8000';

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const { headers: optHeaders, ...rest } = options;
  const fetchOptions = {
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...optHeaders,
    },
  };
  const res = await fetch(url, fetchOptions);
  const json = await res.json();
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${json.error?.message || JSON.stringify(json)} | detail: ${JSON.stringify(json.detail || json.error?.detail)}`);
  }
  return json.data;
}

function authHeaders(token) {
  return { Authorization: `Bearer ${token}` };
}

const api = {
  // Auth
  async login(username, password) {
    const res = await fetch(`${BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const json = await res.json();
    if (!res.ok) {
      throw new Error(`Login failed ${res.status}: ${json.error?.message || JSON.stringify(json)}`);
    }
    return json.data;
  },

  // Properties
  async createProperty(token, data) {
    return request('/api/properties', {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(data),
    });
  },

  async getProperty(token, id) {
    return request(`/api/properties/${id}`, {
      headers: authHeaders(token),
    });
  },

  async deleteProperty(token, id) {
    return request(`/api/properties/${id}`, {
      method: 'DELETE',
      headers: authHeaders(token),
    });
  },

  // Permissions
  async createPermission(token, data) {
    return request('/api/permissions', {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(data),
    });
  },

  async getPermission(token, id) {
    return request(`/api/permissions/${id}`, {
      headers: authHeaders(token),
    });
  },

  async changePermissionStatus(token, id, body) {
    return request(`/api/permissions/${id}/status`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(body),
    });
  },

  async startPermissionRenewal(token, id) {
    return request(`/api/permissions/${id}/renewal`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify({}),
    });
  },

  // Leases
  async createLease(token, data) {
    return request('/api/leases', {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(data),
    });
  },

  async getLease(token, id) {
    return request(`/api/leases/${id}`, {
      headers: authHeaders(token),
    });
  },

  async changeLeaseStatus(token, id, body) {
    return request(`/api/leases/${id}/status`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(body),
    });
  },

  async startLeaseRenewal(token, id) {
    return request(`/api/leases/${id}/renewal`, {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify({}),
    });
  },

  // Fees
  async calculateFee(token, data) {
    return request('/api/fees/calculate', {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(data),
    });
  },

  async getFeeDetails(token, caseType, caseId) {
    return request(`/api/fees/${caseType}/${caseId}`, {
      headers: authHeaders(token),
    });
  },

  // Unit Prices
  async getUnitPrices(token) {
    return request('/api/unit-prices', {
      headers: authHeaders(token),
    });
  },

  async createUnitPrice(token, data) {
    return request('/api/unit-prices', {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(data),
    });
  },

  async updateUnitPrice(token, id, data) {
    return request(`/api/unit-prices/${id}`, {
      method: 'PUT',
      headers: authHeaders(token),
      body: JSON.stringify(data),
    });
  },

  // PDF
  async generatePermissionPdf(token, id) {
    return request(`/api/pdf/permission/${id}`, {
      method: 'POST',
      headers: authHeaders(token),
    });
  },

  async generateLandLeasePdf(token, id) {
    return request(`/api/pdf/lease-land/${id}`, {
      method: 'POST',
      headers: authHeaders(token),
    });
  },

  async generateBuildingLeasePdf(token, id) {
    return request(`/api/pdf/lease-building/${id}`, {
      method: 'POST',
      headers: authHeaders(token),
    });
  },

  async generateRenewalPdf(token, caseType, caseId) {
    return request(`/api/pdf/renewal/${caseType}/${caseId}`, {
      method: 'POST',
      headers: authHeaders(token),
    });
  },

  async downloadPdf(token, documentId) {
    const res = await fetch(`${BASE_URL}/api/pdf/download/${documentId}`, {
      headers: authHeaders(token),
    });
    if (!res.ok) {
      const json = await res.json().catch(() => ({}));
      throw new Error(`PDF download failed ${res.status}: ${json.error?.message || 'Unknown error'}`);
    }
    return res;
  },

  // Files
  async uploadFile(token, filePath, relatedType, relatedId) {
    const fsPromises = await import('fs/promises');
    const fileBuffer = await fsPromises.readFile(filePath);

    const formData = new FormData();
    formData.append('file', new Blob([fileBuffer]), filePath.split('/').pop());
    formData.append('related_type', relatedType);
    formData.append('related_id', String(relatedId));
    formData.append('file_type', 'other');

    const res = await fetch(`${BASE_URL}/api/files/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });
    const json = await res.json();
    if (!res.ok) {
      throw new Error(`File upload failed ${res.status}: ${json.error?.message || JSON.stringify(json)}`);
    }
    return json.data;
  },

  async getFiles(token, relatedType, relatedId) {
    return request(`/api/files?related_type=${relatedType}&related_id=${relatedId}`, {
      headers: authHeaders(token),
    });
  },

  async deleteFile(token, fileId) {
    return request(`/api/files/${fileId}`, {
      method: 'DELETE',
      headers: authHeaders(token),
    });
  },

  // Users (admin)
  async getUsers(token) {
    return request('/api/auth/users', {
      headers: authHeaders(token),
    });
  },

  async createUser(token, data) {
    return request('/api/auth/users', {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify(data),
    });
  },

  async unlockUser(token, userId) {
    return request(`/api/auth/users/${userId}/unlock`, {
      method: 'POST',
      headers: authHeaders(token),
    });
  },
};

export { api };
