import { afterEach, describe, expect, test } from "vitest";
import { getInitData, isTelegramEnv } from "./telegram";

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
});
