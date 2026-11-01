import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';

describe('CareerOS app routing', () => {
  beforeEach(() => {
    localStorage.clear();
    window.history.pushState({}, '', '/career-brain');

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          id: 'user-1',
          email: 'user@example.com',
          full_name: 'Test User',
          is_active: true,
        }),
      })
    );

    localStorage.setItem('careeros_access_token', 'token-123');
  });

  it('renders the career brain page for authenticated users', async () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByRole('heading', { name: /career brain/i }).length).toBeGreaterThan(0);
    });
  });
});
