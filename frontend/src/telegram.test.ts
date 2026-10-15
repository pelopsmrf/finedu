import { afterEach, describe, expect, test, vi } from "vitest";
import { getInitData, initTelegramApp, isTelegramEnv } from "./telegram";

afterEach(() => {
  delete (window as any).Telegram;
});

describe("telegram environment detection", () => {
  test("returns false/null outside Telegram", () => {
    expect(isTelegramEnv()).toBe(false);
    expect(getInitData()).toBeNull();
  });

  test("returns true/string when Telegram WebApp is present", () => {
    (window as any).Telegram = { WebApp: { initData: "abc" } };
    expect(isTelegramEnv()).toBe(true);
    expect(getInitData()).toBe("abc");
  });

  test("returns null when initData is an empty string", () => {
    (window as any).Telegram = { WebApp: { initData: "" } };
    expect(getInitData()).toBeNull();
  });

  test("plain browser with telegram-web-app.js loaded is not Telegram", () => {
    // The script defines WebApp everywhere; only Telegram fills initData.
    (window as any).Telegram = { WebApp: { initData: "" } };
    expect(isTelegramEnv()).toBe(false);
  });
});

describe("initTelegramApp", () => {
  test("calls ready() and expand() when Telegram WebApp is present", () => {
    const ready = vi.fn();
    const expand = vi.fn();
    (window as any).Telegram = { WebApp: { initData: "abc", ready, expand } };
    initTelegramApp();
    expect(ready).toHaveBeenCalledOnce();
    expect(expand).toHaveBeenCalledOnce();
  });

  test("does nothing outside Telegram", () => {
    expect(() => initTelegramApp()).not.toThrow();
  });
});
