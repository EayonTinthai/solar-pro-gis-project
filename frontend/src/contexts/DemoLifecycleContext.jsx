import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useClerk, useUser } from '@clerk/react';
import { toast } from 'sonner';

const DemoLifecycleContext = createContext(null);

const PRODUCT_ID = 'solar-panel-detection';
const DEFAULT_DEMO_DURATION_DAYS = 14;

const DEMO_EVENT_PENDING_USER = 'demo_access_pending_user';
const DEMO_EVENT_PENDING_TEAM = 'demo_access_pending_team';
const DEMO_EVENT_GRANTED = 'demo_access_granted';
const DEMO_EVENT_EXPIRED = 'demo_access_expired';

function asObject(value) {
  return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
}

function toIsoOrNull(value) {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = Date.parse(trimmed);
  return Number.isFinite(parsed) ? new Date(parsed).toISOString() : null;
}

function toStringOrNull(value) {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function normalizePlan(value) {
  return value === 'pro' ? 'pro' : 'free';
}

function normalizeAccountType(value, { plan, demoStatus } = {}) {
  if (value === 'pro' || value === 'demo' || value === 'free') return value;
  if (demoStatus === 'granted') return 'demo';
  return plan === 'pro' ? 'pro' : 'free';
}

function normalizeDemoStatus(value) {
  if (value === 'pending' || value === 'granted' || value === 'expired') return value;
  return 'none';
}

function parseDemoDurationDays(raw) {
  const n = Number(raw);
  if (Number.isFinite(n) && n > 0) return Math.max(1, Math.floor(n));
  return DEFAULT_DEMO_DURATION_DAYS;
}

function parseIsoMs(iso) {
  if (!iso) return null;
  const ms = Date.parse(iso);
  return Number.isFinite(ms) ? ms : null;
}

function addDaysIso(iso, days) {
  const base = parseIsoMs(iso);
  if (base == null) return null;
  return new Date(base + days * 24 * 60 * 60 * 1000).toISOString();
}

function nowIso() {
  return new Date().toISOString();
}

function formatDate(iso) {
  const ms = parseIsoMs(iso);
  if (ms == null) return null;
  return new Date(ms).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function normalizeLifecycleMetadata(rawUnsafe) {
  const unsafe = asObject(rawUnsafe);
  const demo = asObject(unsafe.demo_access);
  const onboarding = asObject(unsafe.onboarding);
  const normalizedPlan = normalizePlan(unsafe.plan);
  const normalizedDemoStatus = normalizeDemoStatus(demo.status);

  return {
    plan: normalizedPlan,
    account_type: normalizeAccountType(unsafe.account_type, {
      plan: normalizedPlan,
      demoStatus: normalizedDemoStatus,
    }),
    demo_access: {
      status: normalizedDemoStatus,
      requested_at: toIsoOrNull(demo.requested_at),
      requested_source: toStringOrNull(demo.requested_source),
      company: toStringOrNull(demo.company),
      note: toStringOrNull(demo.note),
      granted_at: toIsoOrNull(demo.granted_at),
      expires_at: toIsoOrNull(demo.expires_at),
      expired_at: toIsoOrNull(demo.expired_at),
      pending_email_sent_at: toIsoOrNull(demo.pending_email_sent_at),
      team_notified_at: toIsoOrNull(demo.team_notified_at),
      granted_email_sent_at: toIsoOrNull(demo.granted_email_sent_at),
      expired_email_sent_at: toIsoOrNull(demo.expired_email_sent_at),
    },
    onboarding: {
      tour_completed_at: toIsoOrNull(onboarding.tour_completed_at),
    },
  };
}

function buildUnsafeMetadata(rawUnsafe, { plan, accountType, demoAccess, onboarding }) {
  const unsafe = asObject(rawUnsafe);
  const next = { ...unsafe };
  if (plan) next.plan = normalizePlan(plan);
  if (accountType) {
    next.account_type = normalizeAccountType(accountType, {
      plan: next.plan,
      demoStatus: demoAccess?.status,
    });
  }
  if (demoAccess) next.demo_access = { ...demoAccess };
  if (onboarding) next.onboarding = { ...onboarding };
  return next;
}

function getPrimaryEmail(user) {
  return user?.primaryEmailAddress?.emailAddress?.trim() || '';
}

function getDisplayName(user) {
  return user?.fullName?.trim() || user?.username?.trim() || 'Unknown';
}

function getEffectiveExpiresAt(demoAccess, durationDays) {
  if (demoAccess.expires_at) return demoAccess.expires_at;
  if (demoAccess.granted_at) return addDaysIso(demoAccess.granted_at, durationDays);
  return null;
}

function makeStorageKey(userId, category, eventType, timestamp) {
  return `demo-lifecycle:${userId}:${category}:${eventType}:${timestamp}`;
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

function makeIdempotencyKey({ userId, event, timestamp }) {
  return `${PRODUCT_ID}:${userId}:${event}:${timestamp || 'none'}`;
}

function trimOrNull(value) {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function noticeTimestampFor(type, demoAccess, effectiveExpiresAt) {
  if (type === 'granted') {
    return demoAccess.granted_at || effectiveExpiresAt || null;
  }
  if (type === 'expired') {
    return demoAccess.expired_at || effectiveExpiresAt || demoAccess.granted_at || null;
  }
  return null;
}

const lifecycleWebhookUrl = import.meta.env.VITE_DEMO_LIFECYCLE_WEBHOOK_URL?.trim() || '';
const lifecycleWebhookBearer = import.meta.env.VITE_DEMO_LIFECYCLE_WEBHOOK_BEARER?.trim() || '';
const demoDurationDays = parseDemoDurationDays(import.meta.env.VITE_DEMO_DURATION_DAYS);

/**
 * @param {{ children: import('react').ReactNode }} props
 */
export function DemoLifecycleProvider({ children }) {
  const { isLoaded, isSignedIn, user } = useUser();
  const { openSignIn } = useClerk();
  const [storageTick, setStorageTick] = useState(0);
  const reconcileLockRef = useRef(false);
  const requestLockRef = useRef(false);
  const completeTourLockRef = useRef(false);
  const reconciledUserIdRef = useRef(null);

  const normalized = useMemo(
    () => normalizeLifecycleMetadata(user?.unsafeMetadata),
    [user?.unsafeMetadata]
  );
  const effectiveExpiresAt = useMemo(
    () => getEffectiveExpiresAt(normalized.demo_access, demoDurationDays),
    [normalized.demo_access]
  );
  const effectiveExpiresAtMs = useMemo(() => parseIsoMs(effectiveExpiresAt), [effectiveExpiresAt]);

  const demoAccessStatus = useMemo(() => {
    if (normalized.demo_access.status !== 'granted') return normalized.demo_access.status;
    if (effectiveExpiresAtMs != null && effectiveExpiresAtMs <= Date.now()) return 'expired';
    return 'granted';
  }, [normalized.demo_access.status, effectiveExpiresAtMs]);

  const lifecycleIsPro = Boolean(isSignedIn && normalized.account_type === 'pro');

  const activeNotice = useMemo(() => {
    if (!isSignedIn || !user?.id) return null;

    if (demoAccessStatus === 'granted') {
      const timestamp = noticeTimestampFor('granted', normalized.demo_access, effectiveExpiresAt);
      if (!timestamp) return null;
      const dismissKey = makeStorageKey(user.id, 'banner-dismissed', 'granted', timestamp);
      if (readStorage(dismissKey)) return null;
      return {
        type: 'granted',
        timestamp,
        expiresAt: effectiveExpiresAt,
      };
    }

    if (demoAccessStatus === 'expired') {
      const timestamp = noticeTimestampFor('expired', normalized.demo_access, effectiveExpiresAt);
      if (!timestamp) return null;
      const dismissKey = makeStorageKey(user.id, 'banner-dismissed', 'expired', timestamp);
      if (readStorage(dismissKey)) return null;
      return {
        type: 'expired',
        timestamp,
        expiredAt: normalized.demo_access.expired_at || timestamp,
      };
    }

    return null;
  }, [
    demoAccessStatus,
    effectiveExpiresAt,
    isSignedIn,
    normalized.demo_access,
    storageTick,
    user?.id,
  ]);

  const updateLifecycleUser = useCallback(async (targetUser, { plan, accountType, demoAccess, onboarding }) => {
    if (!targetUser) return null;
    const unsafeMetadata = buildUnsafeMetadata(targetUser.unsafeMetadata, {
      plan,
      accountType,
      demoAccess,
      onboarding,
    });
    const updatedUser = await targetUser.update({ unsafeMetadata });
    return updatedUser || targetUser;
  }, []);

  const sendLifecycleWebhook = useCallback(
    async ({ event, demoAccess, eventTimestamp }) => {
      if (!user?.id) return { ok: false, skipped: true, reason: 'missing_user' };
      if (!lifecycleWebhookUrl) {
        return { ok: false, skipped: true, reason: 'missing_webhook_url' };
      }

      const headers = {
        'Content-Type': 'application/json',
      };
      if (lifecycleWebhookBearer) {
        headers.Authorization = `Bearer ${lifecycleWebhookBearer}`;
      }

      const occurredAt = nowIso();
      const payload = {
        event,
        idempotency_key: makeIdempotencyKey({
          userId: user.id,
          event,
          timestamp: eventTimestamp || occurredAt,
        }),
        occurred_at: occurredAt,
        product: PRODUCT_ID,
        user: {
          id: user.id,
          email: getPrimaryEmail(user),
          name: getDisplayName(user),
        },
        demo_access: {
          ...demoAccess,
          status: normalizeDemoStatus(demoAccess.status),
        },
      };

      try {
        const response = await fetch(lifecycleWebhookUrl, {
          method: 'POST',
          headers,
          mode: 'cors',
          body: JSON.stringify(payload),
        });
        if (!response.ok) {
          throw new Error(`Webhook request failed (${response.status})`);
        }
        return { ok: true };
      } catch (error) {
        console.error(`[demo-lifecycle] webhook ${event} failed`, error);
        return { ok: false, error };
      }
    },
    [user]
  );

  const reconcileLifecycle = useCallback(async () => {
    if (!isLoaded || !isSignedIn || !user) return;
    if (reconcileLockRef.current) return;

    reconcileLockRef.current = true;
    try {
      let workingUser = user;
      await workingUser.reload();
      let lifecycle = normalizeLifecycleMetadata(workingUser.unsafeMetadata);
      let nextDemoAccess = { ...lifecycle.demo_access };
      let nextPlan = lifecycle.plan;
      let nextAccountType = lifecycle.account_type;
      let shouldPersist = false;
      const now = nowIso();

      if (nextDemoAccess.status === 'granted') {
        if (!nextDemoAccess.granted_at) {
          nextDemoAccess.granted_at = now;
          shouldPersist = true;
        }
        if (!nextDemoAccess.expires_at) {
          const derivedExpires = addDaysIso(nextDemoAccess.granted_at || now, demoDurationDays);
          if (derivedExpires) {
            nextDemoAccess.expires_at = derivedExpires;
            shouldPersist = true;
          }
        }

        const expiryMs = parseIsoMs(nextDemoAccess.expires_at);
        if (expiryMs != null && expiryMs <= Date.now()) {
          nextDemoAccess.status = 'expired';
          if (!nextDemoAccess.expired_at) {
            nextDemoAccess.expired_at = now;
          }
          nextPlan = 'free';
          nextAccountType = 'free';
          shouldPersist = true;
        } else {
          if (nextPlan !== 'free') {
            nextPlan = 'free';
            shouldPersist = true;
          }
          if (nextAccountType !== 'demo') {
            nextAccountType = 'demo';
            shouldPersist = true;
          }
        }
      } else if (nextDemoAccess.status === 'pending') {
        if (nextPlan !== 'free') {
          nextPlan = 'free';
          shouldPersist = true;
        }
        if (nextAccountType !== 'free') {
          nextAccountType = 'free';
          shouldPersist = true;
        }
      } else if (nextDemoAccess.status === 'expired') {
        if (!nextDemoAccess.expired_at) {
          nextDemoAccess.expired_at = now;
          shouldPersist = true;
        }
        if (nextPlan !== 'free') {
          nextPlan = 'free';
          shouldPersist = true;
        }
        if (nextAccountType !== 'free') {
          nextAccountType = 'free';
          shouldPersist = true;
        }
      }

      if (shouldPersist) {
        workingUser = await updateLifecycleUser(workingUser, {
          plan: nextPlan,
          accountType: nextAccountType,
          demoAccess: nextDemoAccess,
        });
        lifecycle = normalizeLifecycleMetadata(workingUser.unsafeMetadata);
        nextDemoAccess = { ...lifecycle.demo_access };
      }

      const sentAtPatch = {};
      if (nextDemoAccess.status === 'pending' && !nextDemoAccess.pending_email_sent_at) {
        const pendingUserResult = await sendLifecycleWebhook({
          event: DEMO_EVENT_PENDING_USER,
          demoAccess: nextDemoAccess,
          eventTimestamp: nextDemoAccess.requested_at || now,
        });
        if (pendingUserResult.ok) {
          sentAtPatch.pending_email_sent_at = nowIso();
        } else {
          toast.error('Demo request acknowledgment email is delayed and will retry.', {
            id: 'demo-pending-user-email-delayed',
          });
        }
      }

      if (nextDemoAccess.status === 'pending' && !nextDemoAccess.team_notified_at) {
        const pendingTeamResult = await sendLifecycleWebhook({
          event: DEMO_EVENT_PENDING_TEAM,
          demoAccess: nextDemoAccess,
          eventTimestamp: nextDemoAccess.requested_at || now,
        });
        if (pendingTeamResult.ok) {
          sentAtPatch.team_notified_at = nowIso();
        } else {
          toast.error('Internal demo notification is delayed and will retry.', {
            id: 'demo-pending-team-email-delayed',
          });
        }
      }

      if (nextDemoAccess.status === 'granted' && !nextDemoAccess.granted_email_sent_at) {
        const grantedResult = await sendLifecycleWebhook({
          event: DEMO_EVENT_GRANTED,
          demoAccess: nextDemoAccess,
          eventTimestamp: nextDemoAccess.granted_at || now,
        });
        if (grantedResult.ok) {
          sentAtPatch.granted_email_sent_at = nowIso();
        } else {
          toast.error('Demo granted email is delayed and will retry on next refresh.', {
            id: 'demo-granted-email-delayed',
          });
        }
      }

      if (nextDemoAccess.status === 'expired' && !nextDemoAccess.expired_email_sent_at) {
        const expiredResult = await sendLifecycleWebhook({
          event: DEMO_EVENT_EXPIRED,
          demoAccess: nextDemoAccess,
          eventTimestamp: nextDemoAccess.expired_at || nextDemoAccess.expires_at || now,
        });
        if (expiredResult.ok) {
          sentAtPatch.expired_email_sent_at = nowIso();
        } else {
          toast.error('Demo expired email is delayed and will retry on next refresh.', {
            id: 'demo-expired-email-delayed',
          });
        }
      }

        if (Object.keys(sentAtPatch).length) {
          workingUser = await updateLifecycleUser(workingUser, {
            demoAccess: { ...nextDemoAccess, ...sentAtPatch },
          });
        }

      await workingUser.reload();
    } catch (error) {
      console.error('[demo-lifecycle] reconcile failed', error);
    } finally {
      reconcileLockRef.current = false;
    }
  }, [isLoaded, isSignedIn, sendLifecycleWebhook, updateLifecycleUser, user]);

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn || !user?.id) {
      reconciledUserIdRef.current = null;
      return;
    }
    if (reconciledUserIdRef.current === user.id) return;
    reconciledUserIdRef.current = user.id;
    void reconcileLifecycle();
  }, [isLoaded, isSignedIn, reconcileLifecycle, user?.id]);

  useEffect(() => {
    if (!activeNotice || !user?.id) return;
    const toastKey = makeStorageKey(user.id, 'toast-shown', activeNotice.type, activeNotice.timestamp);
    if (readStorage(toastKey)) return;

    if (activeNotice.type === 'granted') {
      const label = formatDate(activeNotice.expiresAt);
      toast.success(
        label
          ? `Demo access granted. Pro is active until ${label}.`
          : 'Demo access granted. Pro features are now active.'
      );
    } else if (activeNotice.type === 'expired') {
      const label = formatDate(activeNotice.expiredAt);
      toast.error(
        label
          ? `Demo access expired on ${label}.`
          : 'Demo access expired. Your account is back on the Free plan.'
      );
    }

    writeStorage(toastKey, '1');
  }, [activeNotice, user?.id]);

  const dismissNotice = useCallback(
    (noticeType) => {
      if (!activeNotice || !user?.id) return;
      if (noticeType && activeNotice.type !== noticeType) return;
      const dismissKey = makeStorageKey(
        user.id,
        'banner-dismissed',
        activeNotice.type,
        activeNotice.timestamp
      );
      writeStorage(dismissKey, nowIso());
      setStorageTick((n) => n + 1);
    },
    [activeNotice, user?.id]
  );

  const requestDemoAccess = useCallback(
    async ({ source = 'Locked Pro feature', company = null, note = null } = {}) => {
      if (!isLoaded) {
        return { ok: false, code: 'not_loaded' };
      }
      if (!isSignedIn || !user) {
        openSignIn({ afterSignInUrl: window.location.href });
        return { ok: false, code: 'signin_required' };
      }
      if (requestLockRef.current) {
        return { ok: false, code: 'busy' };
      }

      requestLockRef.current = true;
      try {
        let workingUser = user;
        await workingUser.reload();
        let lifecycle = normalizeLifecycleMetadata(workingUser.unsafeMetadata);
        const demo = lifecycle.demo_access;
        const expiresAt = getEffectiveExpiresAt(demo, demoDurationDays);
        const expiresMs = parseIsoMs(expiresAt);

        if (demo.status === 'pending') {
          return { ok: true, code: 'already_pending' };
        }
        if (demo.status === 'granted') {
          if (expiresMs == null || expiresMs > Date.now()) {
            return { ok: true, code: 'already_granted', expiresAt };
          }
        }

        const requestedAt = nowIso();
        const nextDemoAccess = {
          ...demo,
          status: 'pending',
          requested_at: requestedAt,
          requested_source: trimOrNull(source) || 'Locked Pro feature',
          company: trimOrNull(company),
          note: trimOrNull(note),
          granted_at: null,
          expires_at: null,
          expired_at: null,
          pending_email_sent_at: null,
          team_notified_at: null,
          granted_email_sent_at: null,
          expired_email_sent_at: null,
        };

        workingUser = await updateLifecycleUser(workingUser, {
          plan: 'free',
          accountType: 'free',
          demoAccess: nextDemoAccess,
        });

        lifecycle = normalizeLifecycleMetadata(workingUser.unsafeMetadata);
        const latestDemoAccess = { ...lifecycle.demo_access };
        const failures = [];
        const sentAtPatch = {};

        if (!latestDemoAccess.pending_email_sent_at) {
          const userAckResult = await sendLifecycleWebhook({
            event: DEMO_EVENT_PENDING_USER,
            demoAccess: latestDemoAccess,
            eventTimestamp: latestDemoAccess.requested_at || requestedAt,
          });
          if (userAckResult.ok) {
            sentAtPatch.pending_email_sent_at = nowIso();
          } else {
            failures.push(DEMO_EVENT_PENDING_USER);
          }
        }

        if (!latestDemoAccess.team_notified_at) {
          const teamAckResult = await sendLifecycleWebhook({
            event: DEMO_EVENT_PENDING_TEAM,
            demoAccess: latestDemoAccess,
            eventTimestamp: latestDemoAccess.requested_at || requestedAt,
          });
          if (teamAckResult.ok) {
            sentAtPatch.team_notified_at = nowIso();
          } else {
            failures.push(DEMO_EVENT_PENDING_TEAM);
          }
        }

        if (Object.keys(sentAtPatch).length) {
          workingUser = await updateLifecycleUser(workingUser, {
            demoAccess: { ...latestDemoAccess, ...sentAtPatch },
          });
        }

        await workingUser.reload();
        return {
          ok: true,
          code: 'requested',
          webhookFailures: failures,
        };
      } catch (error) {
        console.error('[demo-lifecycle] request failed', error);
        return { ok: false, code: 'request_failed', error };
      } finally {
        requestLockRef.current = false;
      }
    },
    [isLoaded, isSignedIn, openSignIn, sendLifecycleWebhook, updateLifecycleUser, user]
  );

  const completeTour = useCallback(async () => {
    if (!isLoaded || !isSignedIn || !user) return { ok: false, code: 'signin_required' };
    if (completeTourLockRef.current) return { ok: false, code: 'busy' };

    const localKey = `demo-lifecycle:${user.id}:tour-local-complete`;
    writeStorage(localKey, nowIso());
    completeTourLockRef.current = true;

    try {
      const workingUser = user;
      await workingUser.reload();
      const lifecycle = normalizeLifecycleMetadata(workingUser.unsafeMetadata);
      if (lifecycle.onboarding.tour_completed_at) {
        return { ok: true, code: 'already_completed' };
      }

      const nextOnboarding = {
        ...lifecycle.onboarding,
        tour_completed_at: nowIso(),
      };
      const updatedUser = await updateLifecycleUser(workingUser, {
        onboarding: nextOnboarding,
      });
      await updatedUser.reload();
      return { ok: true, code: 'completed' };
    } catch (error) {
      console.error('[demo-lifecycle] complete tour failed', error);
      return { ok: false, code: 'failed', error };
    } finally {
      completeTourLockRef.current = false;
    }
  }, [isLoaded, isSignedIn, updateLifecycleUser, user]);

  const value = useMemo(
    () => ({
      isLoaded,
      isSignedIn: Boolean(isSignedIn),
      userId: user?.id || null,
      plan: normalized.plan,
      accountType: normalized.account_type,
      demoAccess: {
        ...normalized.demo_access,
        status: demoAccessStatus,
        expires_at: effectiveExpiresAt,
      },
      onboarding: normalized.onboarding,
      demoAccessStatus,
      demoExpiresAt: effectiveExpiresAt,
      demoExpiredAt: normalized.demo_access.expired_at,
      tourCompletedAt: normalized.onboarding.tour_completed_at,
      lifecycleIsPro,
      activeNotice,
      requestDemoAccess,
      completeTour,
      dismissNotice,
      refreshLifecycle: reconcileLifecycle,
    }),
    [
      activeNotice,
      completeTour,
      demoAccessStatus,
      dismissNotice,
      effectiveExpiresAt,
      isLoaded,
      isSignedIn,
      lifecycleIsPro,
      normalized.demo_access,
      normalized.onboarding,
      normalized.account_type,
      normalized.plan,
      reconcileLifecycle,
      requestDemoAccess,
      user?.id,
    ]
  );

  return <DemoLifecycleContext.Provider value={value}>{children}</DemoLifecycleContext.Provider>;
}

export function useDemoLifecycle() {
  const ctx = useContext(DemoLifecycleContext);
  if (ctx) return ctx;
  return {
    isLoaded: false,
    isSignedIn: false,
    userId: null,
    plan: 'free',
    accountType: 'free',
    demoAccess: {
      status: 'none',
      requested_at: null,
      requested_source: null,
      company: null,
      note: null,
      granted_at: null,
      expires_at: null,
      expired_at: null,
      pending_email_sent_at: null,
      team_notified_at: null,
      granted_email_sent_at: null,
      expired_email_sent_at: null,
    },
    onboarding: { tour_completed_at: null },
    demoAccessStatus: 'none',
    demoExpiresAt: null,
    demoExpiredAt: null,
    tourCompletedAt: null,
    lifecycleIsPro: false,
    activeNotice: null,
    requestDemoAccess: async () => ({ ok: false, code: 'unavailable' }),
    completeTour: async () => ({ ok: false, code: 'unavailable' }),
    dismissNotice: () => {},
    refreshLifecycle: async () => {},
  };
}
