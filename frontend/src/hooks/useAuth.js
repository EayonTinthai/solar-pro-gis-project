import { useEffect, useMemo, useState } from 'react';
import { useClerk, useUser } from '@clerk/react';
import { useDemoLifecycle } from '@/contexts/DemoLifecycleContext';

/** Pro access is bypassed – all signed-in users get Pro features. */
const DEFAULT_FRONTEND_TRIAL_DAYS = 7;

function parseTrialDays(value) {
  const parsed = Number(value);
  if (Number.isFinite(parsed) && parsed > 0) {
    return Math.floor(parsed);
  }
  return DEFAULT_FRONTEND_TRIAL_DAYS;
}

function readStorage(key) {
  if (typeof window === 'undefined') return null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key, value) {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // ignore storage write failures
  }
}

export function useAuth() {
  const { isLoaded, isSignedIn, user } = useUser();
  const { openSignIn, openSignUp, signOut } = useClerk();
  const {
    accountType: lifecycleAccountType,
    demoAccessStatus,
    demoExpiresAt,
    demoExpiredAt,
    tourCompletedAt,
    lifecycleIsPro,
    demoAccess,
  } = useDemoLifecycle();
  const trialDays = parseTrialDays(import.meta.env.VITE_FRONTEND_AUTO_TRIAL_DAYS);
  const [trialState, setTrialState] = useState({
    trialStartedAt: null,
    trialExpiresAt: null,
  });

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !user?.id) {
      setTrialState({ trialStartedAt: null, trialExpiresAt: null });
      return;
    }

    const startedKey = `frontend-trial:${user.id}:started_at`;
    const expiresKey = `frontend-trial:${user.id}:expires_at`;
    const now = Date.now();

    let startedAt = readStorage(startedKey);
    let expiresAt = readStorage(expiresKey);

    const startedMs = typeof startedAt === 'string' ? Date.parse(startedAt) : NaN;
    const expiresMs = typeof expiresAt === 'string' ? Date.parse(expiresAt) : NaN;
    const hasValidStarted = Number.isFinite(startedMs);
    const hasValidExpires = Number.isFinite(expiresMs);

    let shouldPersist = false;

    if (!hasValidStarted) {
      startedAt = new Date(now).toISOString();
      shouldPersist = true;
    }

    const nextStartedMs = Number.isFinite(Date.parse(startedAt)) ? Date.parse(startedAt) : now;
    const computedExpires = new Date(nextStartedMs + trialDays * 24 * 60 * 60 * 1000).toISOString();

    if (!hasValidExpires || Date.parse(expiresAt) <= nextStartedMs) {
      expiresAt = computedExpires;
      shouldPersist = true;
    }

    if (shouldPersist) {
      writeStorage(startedKey, startedAt);
      writeStorage(expiresKey, expiresAt);
    }

    setTrialState({
      trialStartedAt: startedAt,
      trialExpiresAt: expiresAt,
    });
  }, [isLoaded, isSignedIn, trialDays, user?.id]);

  const primary = user?.primaryEmailAddress?.emailAddress?.trim().toLowerCase() ?? '';
  const publicPlanPro = user?.publicMetadata?.plan === 'pro';
  const isPaidPro = true; // Pro access bypassed – all users get Pro
  const nowMs = Date.now();
  const demoExpiryMs = typeof demoExpiresAt === 'string' ? Date.parse(demoExpiresAt) : NaN;
  const hasValidDemoExpiry = Number.isFinite(demoExpiryMs);
  const isServerDemoActive = Boolean(
    isSignedIn &&
    demoAccessStatus === 'granted' &&
    (!hasValidDemoExpiry || demoExpiryMs > nowMs)
  );

  const trialExpiryMs =
    typeof trialState.trialExpiresAt === 'string' ? Date.parse(trialState.trialExpiresAt) : NaN;
  const isFrontendTrialActive = Boolean(
    isSignedIn &&
    !isPaidPro &&
    !isServerDemoActive &&
    Number.isFinite(trialExpiryMs) &&
    trialExpiryMs > nowMs
  );

  const accountType = useMemo(() => {
    if (!isSignedIn) return 'free';
    if (isPaidPro) return 'pro';
    if (isServerDemoActive) return 'demo';
    if (isFrontendTrialActive) return 'trial';
    return 'free';
  }, [isFrontendTrialActive, isPaidPro, isServerDemoActive, isSignedIn]);

  const isPro = accountType === 'pro';
  const isDemo = accountType === 'demo';
  const isDemoActive = isServerDemoActive || isFrontendTrialActive;
  const hasFeatureAccess = isPro || isDemoActive;

  return {
    isLoaded,
    isSignedIn: Boolean(isSignedIn),
    isPro,
    isDemo,
    isDemoActive,
    isFrontendTrialActive,
    hasFeatureAccess,
    accountType,
    demoAccessStatus,
    demoExpiresAt,
    demoExpiredAt,
    trialStartedAt: trialState.trialStartedAt,
    trialExpiresAt: trialState.trialExpiresAt,
    tourCompletedAt,
    demoAccess,
    user,
    signIn: () => openSignIn({ afterSignInUrl: window.location.href }),
    signUp: () => openSignUp({ afterSignUpUrl: window.location.href }),
    signOut: () => signOut(),
  };
}
