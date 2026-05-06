import { useClerk, useUser } from '@clerk/react';

// Check if Clerk is available
const hasClerk = Boolean(import.meta.env.VITE_CLERK_PUBLISHABLE_KEY);

/** Pro access is bypassed – all signed-in users get Pro features. */

export function useAuth() {
  // If no Clerk, return guest mode
  if (!hasClerk) {
    return {
      isLoaded: true,
      isSignedIn: false,
      isPro: false,
      user: null,
      signIn: () => console.log('Clerk not configured'),
      signUp: () => console.log('Clerk not configured'),
      signOut: () => console.log('Clerk not configured'),
    };
  }

  // With Clerk
  const { isLoaded, isSignedIn, user } = useUser();
  const { openSignIn, openSignUp, signOut } = useClerk();

  const primary = user?.primaryEmailAddress?.emailAddress?.trim().toLowerCase() ?? '';
  const planPro = user?.publicMetadata?.plan === 'pro';

  const isPro = Boolean(isSignedIn); // Pro access bypassed

  return {
    isLoaded,
    isSignedIn: Boolean(isSignedIn),
    isPro,
    user,
    signIn: () => openSignIn({ afterSignInUrl: window.location.href }),
    signUp: () => openSignUp({ afterSignUpUrl: window.location.href }),
    signOut: () => signOut(),
  };
}
