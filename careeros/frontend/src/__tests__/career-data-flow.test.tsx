import { screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { render } from '@testing-library/react';

describe('Career data page', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('careeros_access_token', 'mock-token');
    vi.stubGlobal('fetch', vi.fn());
  });

  it('should display the career data page with skills section', async () => {
    const mockFetch = window.fetch as unknown as ReturnType<typeof vi.fn>;
    mockFetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [],
    });

    window.history.pushState({}, '', '/career-data');

    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    const skillsHeading = await screen.findByRole('heading', { name: /skills/i }, { timeout: 5000 });
    expect(skillsHeading).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /add skill/i })).toBeInTheDocument();
  });
});