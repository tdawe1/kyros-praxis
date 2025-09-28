import { render, screen, fireEvent } from '@testing-library/react';
import { useSession } from 'next-auth/react';
import LogoutButton from '../app/components/LogoutButton';

// Mock next-auth/react
jest.mock('next-auth/react', () => ({
  useSession: jest.fn(),
  signOut: jest.fn(),
}));

const mockUseSession = useSession as jest.MockedFunction<typeof useSession>;

describe('LogoutButton', () => {
  it('renders nothing when not authenticated', () => {
    mockUseSession.mockReturnValue({ data: null, status: 'unauthenticated' });
    
    render(<LogoutButton />);
    
    expect(screen.queryByText('Sign out')).not.toBeInTheDocument();
  });

  it('renders logout button when authenticated', () => {
    mockUseSession.mockReturnValue({
      data: { user: { email: 'test@example.com' } },
      status: 'authenticated',
    });
    
    render(<LogoutButton />);
    
    expect(screen.getByText('Sign out')).toBeInTheDocument();
  });

  it('can be customized with children and className', () => {
    mockUseSession.mockReturnValue({
      data: { user: { email: 'test@example.com' } },
      status: 'authenticated',
    });
    
    render(
      <LogoutButton className="custom-class">
        Custom Logout Text
      </LogoutButton>
    );
    
    const button = screen.getByText('Custom Logout Text');
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('custom-class');
  });
});