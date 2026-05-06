/**
 * Mock Clerk hooks/components for local development without Clerk keys.
 * All users are treated as signed-in Pro users.
 */
import { createContext, useContext } from 'react';

const mockUser = {
  id: 'local_dev_user',
  primaryEmailAddress: { emailAddress: 'dev@localhost' },
  publicMetadata: { plan: 'pro' },
  unsafeMetadata: {},
  reload: async () => {},
  update: async (data) => ({ ...mockUser, ...data }),
};

export const useUser = () => ({
  isLoaded: true,
  isSignedIn: true,
  user: mockUser,
});

export const useClerk = () => ({
  openSignIn: () => console.log('[mock] openSignIn'),
  openSignUp: () => console.log('[mock] openSignUp'),
  signOut: () => console.log('[mock] signOut'),
});

export const useAuth = () => ({
  isSignedIn: true,
  getToken: async () => null,
  isLoaded: true,
});

export const ClerkProvider = ({ children }) => children;
export const ClerkLoaded = ({ children }) => children;
export const ClerkLoading = () => null;
export const SignInButton = ({ children }) => children || null;
export const UserButton = () => null;
export const Show = ({ children }) => children || null;
