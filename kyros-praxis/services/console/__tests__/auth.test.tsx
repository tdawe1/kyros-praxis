import { render, screen, fireEvent } from '@testing-library/react';
import { SessionProvider } from 'next-auth/react';
import AuthPage from '../app/auth/page';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    replace: jest.fn(),
  }),
}));

// Mock next-auth/react
jest.mock('next-auth/react', () => ({
  signIn: jest.fn(),
  getSession: jest.fn(),
  SessionProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe('AuthPage', () => {
  it('renders OAuth login buttons', () => {
    render(
      <SessionProvider session={null}>
        <AuthPage />
      </SessionProvider>
    );

    expect(screen.getByText('Continue with Google')).toBeInTheDocument();
    expect(screen.getByText('Continue with GitHub')).toBeInTheDocument();
    expect(screen.getByText('Or continue with email')).toBeInTheDocument();
  });

  it('renders email and password form', () => {
    render(
      <SessionProvider session={null}>
        <AuthPage />
      </SessionProvider>
    );

    expect(screen.getByLabelText('Email')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign in/i })).toBeInTheDocument();
  });

  it('allows typing in email and password fields', () => {
    render(
      <SessionProvider session={null}>
        <AuthPage />
      </SessionProvider>
    );

    const emailInput = screen.getByLabelText('Email') as HTMLInputElement;
    const passwordInput = screen.getByLabelText('Password') as HTMLInputElement;

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });

    expect(emailInput.value).toBe('test@example.com');
    expect(passwordInput.value).toBe('password123');
  });
});