/**
 * Unit tests cho hệ thống i18n (vi/en).
 *
 * Bao phủ:
 *  - Dictionary: mọi key có đủ 2 bản dịch khác nhau (không sót key).
 *  - LocaleProvider: đổi ngôn ngữ thật sự đổi nội dung render.
 *  - Persist: locale được lưu vào localStorage và khôi phục sau reload.
 *  - <html lang> được đồng bộ.
 */
import { describe, expect, it, beforeEach } from "vitest";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DICTIONARY, type TranslationKey } from "./dictionary";
import { LocaleProvider, useLocale } from "./locale-context";
import { DEFAULT_LOCALE, LOCALE_STORAGE_KEY, isLocale, resetLocaleStore } from "./locale";

/** Probe đọc context — dùng để assert giá trị locale/t. */
function LocaleProbe({ onRender }: { onRender?: (locale: string) => void }) {
  const { locale, t, setLocale } = useLocale();
  onRender?.(locale);
  return (
    <div>
      <span data-testid="locale">{locale}</span>
      <span data-testid="title">{t("nav.overview")}</span>
      <span data-testid="courses">{t("nav.courses")}</span>
      <button type="button" onClick={() => setLocale("en")}>
        switch-en
      </button>
    </div>
  );
}

/** Wrapper ép locale lưu sẵn trong localStorage được nạp lúc mount. */
function LocaleHarness({ onRender }: { onRender?: (locale: string) => void }) {
  return (
    <LocaleProvider>
      <LocaleProbe onRender={onRender} />
    </LocaleProvider>
  );
}

describe("i18n dictionary", () => {
  it("mọi key đều có cả bản tiếng Việt và tiếng Anh", () => {
    const missing: string[] = [];
    for (const [key, entry] of Object.entries(DICTIONARY)) {
      if (!entry.vi?.trim()) missing.push(`${key}.vi`);
      if (!entry.en?.trim()) missing.push(`${key}.en`);
    }
    expect(missing).toEqual([]);
  });

  it("bản tiếng Anh khác bản tiếng Việt cho các nhãn chính", () => {
    const keyChecks: TranslationKey[] = [
      "nav.overview",
      "nav.courses",
      "nav.assignments",
      "nav.history",
      "student.assignments.title",
      "history.title",
      "student.assignment.submit",
      "result.heading",
    ];
    for (const key of keyChecks) {
      expect(DICTIONARY[key].en, key).not.toBe(DICTIONARY[key].vi);
    }
  });

  it("không có chuỗi tiếng Việt còn sót trong bản tiếng Anh của nhóm nhãn chính", () => {
    // Nhãn được dùng trong nav + header — bắt buộc là tiếng Anh.
    const navKeys: TranslationKey[] = [
      "nav.overview",
      "nav.courses",
      "nav.assignments",
      "nav.history",
      "layout.changePassword",
      "layout.logout",
    ];
    for (const key of navKeys) {
      expect(DICTIONARY[key].en, key).not.toMatch(/[àáảãạăâđêôơư]/i);
    }
  });
});

describe("i18n locale helpers", () => {
  it("isLocale nhận diện đúng 2 locale", () => {
    expect(isLocale("vi")).toBe(true);
    expect(isLocale("en")).toBe(true);
    expect(isLocale("fr")).toBe(false);
    expect(isLocale(null)).toBe(false);
  });

  it("default locale là vi", () => {
    expect(DEFAULT_LOCALE).toBe("vi");
  });
});

describe("LocaleProvider", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.lang = "";
    // Store sống ở module scope → reset để mỗi test bắt đầu từ trạng thái sạch.
    resetLocaleStore();
  });

  it("mặc định render bằng tiếng Việt", async () => {
    render(<LocaleHarness />);

    expect(await screen.findByTestId("locale")).toHaveTextContent("vi");
    expect(screen.getByTestId("title")).toHaveTextContent("Tổng quan");
    expect(screen.getByTestId("courses")).toHaveTextContent("Lớp học phần");
  });

  it("đổi sang tiếng Anh sẽ đổi nội dung render", async () => {
    const user = userEvent.setup();
    render(<LocaleHarness />);

    await screen.findByTestId("locale");
    await user.click(screen.getByRole("button", { name: "switch-en" }));

    expect(screen.getByTestId("locale")).toHaveTextContent("en");
    expect(screen.getByTestId("title")).toHaveTextContent("Overview");
    expect(screen.getByTestId("courses")).toHaveTextContent("Courses");
  });

  it("lưu locale vào localStorage khi đổi", async () => {
    const user = userEvent.setup();
    render(<LocaleHarness />);

    await screen.findByTestId("locale");
    await user.click(screen.getByRole("button", { name: "switch-en" }));

    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("en");
  });

  it("khôi phục locale đã lưu sau khi reload trang", async () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "en");

    render(<LocaleHarness />);

    expect(await screen.findByTestId("locale")).toHaveTextContent("en");
    expect(screen.getByTestId("title")).toHaveTextContent("Overview");
  });

  it("đồng bộ thuộc tính lang của <html>", async () => {
    const user = userEvent.setup();
    render(<LocaleHarness />);

    await screen.findByTestId("locale");
    await act(async () => {
      await user.click(screen.getByRole("button", { name: "switch-en" }));
    });

    expect(document.documentElement.lang).toBe("en");
  });

  it("bỏ qua locale không hợp lệ trong localStorage", async () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "fr");

    render(<LocaleHarness />);

    expect(await screen.findByTestId("locale")).toHaveTextContent("vi");
  });
});

describe("useTranslation params", () => {
  it("thay thế tham số {name} trong bản dịch", () => {
    function ParamProbe() {
      const { t } = useLocale();
      return <span data-testid="msg">{t("auth.login.welcome", { name: "An" })}</span>;
    }

    render(
      <LocaleProvider>
        <ParamProbe />
      </LocaleProvider>,
    );

    expect(screen.getByTestId("msg")).toHaveTextContent("Chào mừng An quay lại!");
  });
});

describe("useLocale ngoài provider", () => {
  it("trả về locale mặc định và hàm dịch dùng được", () => {
    function BareProbe() {
      const { locale, t } = useLocale();
      return <span data-testid="bare">{locale}:{t("nav.overview")}</span>;
    }

    render(<BareProbe />);

    expect(screen.getByTestId("bare")).toHaveTextContent("vi:Tổng quan");
  });
});
