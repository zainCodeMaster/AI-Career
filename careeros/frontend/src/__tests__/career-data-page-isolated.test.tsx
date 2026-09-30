import { screen } from '@testing-library/react';
import { CareerDataPage } from '../pages/CareerDataPage';
import { AuthProvider } from '../contexts/AuthContext';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render } from '@testing-library/react';

describe('CareerDataPage isolated', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('careeros_token', 'mock-token');
    vi.stubGlobal('fetch', vi.fn());
  });

  it('should display the career data page with skills section', async () => {
    const mockFetch = window.fetch as unknown as ReturnType<typeof vi.fn>;
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    });

    render(
      <AuthProvider>
        <CareerDataPage />
      </AuthProvider>
    );

    const skillsHeading = await screen.findByRole('heading', { name: /skills/i }, { timeout: 5000 });
    expect(skillsHeading).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /add skill/i })).toBeInTheDocument();
  });
});