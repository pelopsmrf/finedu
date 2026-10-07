declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData?: string;
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

export {};
