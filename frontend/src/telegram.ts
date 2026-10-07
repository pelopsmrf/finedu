declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData?: string;
        ready?: () => void;
        expand?: () => void;
      };
    };
  }
}

export function isTelegramEnv(): boolean {
  return Boolean(window.Telegram?.WebApp);
}

export function getInitData(): string | null {
  const initData = window.Telegram?.WebApp?.initData;
  return initData ? initData : null;
}

/** Switches the Mini App to full-screen mode inside Telegram. No-op outside Telegram. */
export function initTelegramApp(): void {
  const webApp = window.Telegram?.WebApp;
  if (!webApp) return;
  webApp.ready?.();
  webApp.expand?.();
}

export {};
