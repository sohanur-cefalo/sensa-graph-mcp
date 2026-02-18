export interface Employee {
  name: string;
  displayName?: string;
  userId: number;
  designation?: string;
  department?: string;
  email?: string;
  slackDisplayName?: string;
}

export interface EmployeeSearchResponse {
  employees: Employee[];
  total: number;
}

// Get API base URL - use relative URL for proxy (ngrok) or absolute for direct connection
const getApiBaseUrl = (): string => {
  // @ts-ignore - import.meta is replaced by Vite at build-time
  const runtimeEnv = (import.meta as any).env;
  const apiBase = runtimeEnv?.VITE_API_BASE_URL || runtimeEnv?.VITE_API_URL;
  // If API base is set and not localhost, use it (for production)
  if (apiBase && !apiBase.includes('localhost') && !apiBase.includes('127.0.0.1')) {
    return apiBase;
  }
  // Otherwise use relative URL (works with Vite proxy for ngrok)
  return '';
};

export async function searchEmployees(query: string, limit: number = 10): Promise<Employee[]> {
  if (!query || query.trim().length === 0) {
    return [];
  }

  try {
    const baseUrl = getApiBaseUrl();
    const url = new URL(`${baseUrl}/employees/search`);
    url.searchParams.set('q', query.trim());
    url.searchParams.set('limit', limit.toString());

    const res = await fetch(url.toString(), {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) {
      throw new Error(`HTTP ${res.status} - Failed to search employees`);
    }

    const result: EmployeeSearchResponse = await res.json();
    return result.employees;
  } catch (err: any) {
    console.error('Error searching employees:', err);
    return [];
  }
}

