import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ApiError } from '../api/auth';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { AuthShell } from '../components/auth/AuthShell';

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error && error.message) return error.message;
  return 'Registration failed';
}

export function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await register({ email, full_name: fullName, password });
      navigate('/jobs', { replace: true });
    } catch (caught) {
      setError(getErrorMessage(caught));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      eyebrow="Start with a clearer path"
      title="Create your account"
      description="Bring your career profile, opportunities, and applications into one focused workspace."
      footer={
        <p className="text-center">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-blue-600 hover:text-blue-700 hover:underline">
            Sign in
          </Link>
        </p>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              id="email"
              label="Email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              autoFocus
            />
            <Input
              id="fullName"
              label="Full Name"
              type="text"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              required
              maxLength={255}
            />
            <Input
              id="password"
              label="Password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              minLength={8}
            />
            {error && (
              <p
                className="rounded-md border border-error-light bg-error-light p-3 text-body-sm text-error-dark"
                role="alert"
              >
                {error}
              </p>
            )}
            <Button type="submit" variant="primary" disabled={loading} className="w-full">
              {loading ? 'Creating account...' : 'Register'}
            </Button>
      </form>
    </AuthShell>
  );
}
