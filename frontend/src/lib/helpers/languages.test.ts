import { describe, expect, it } from "vitest";

import {
  DEFAULT_SKELETONS,
  LANGUAGE_OPTIONS,
  defaultStarterCode,
  findLanguageOption,
  starterCodeFor,
} from "./languages";

describe("LANGUAGE_OPTIONS", () => {
  it("khai bao day du 5 nguon ngu backend ho tro", () => {
    expect(LANGUAGE_OPTIONS.map((option) => option.value)).toEqual([
      "python",
      "cpp",
      "java",
      "c",
      "javascript",
    ]);
  });

  it("moi nguon ngu deu co duoi file", () => {
    for (const option of LANGUAGE_OPTIONS) {
      expect(option.extension).toBeTruthy();
      expect(option.label).toBeTruthy();
    }
  });
});

describe("findLanguageOption", () => {
  it("tim thay theo khoa nguon ngu", () => {
    expect(findLanguageOption("cpp")?.extension).toBe("cpp");
    expect(findLanguageOption("python")?.extension).toBe("py");
  });

  it("tra undefined cho nguon ngu la", () => {
    expect(findLanguageOption("cobol")).toBeUndefined();
  });
});

describe("defaultStarterCode", () => {
  it("co skeleton cho moi nguon ngu trong danh sach", () => {
    for (const option of LANGUAGE_OPTIONS) {
      expect(defaultStarterCode(option.value)).toBeTruthy();
    }
  });

  it("tra chuoi rong cho nguon ngu la", () => {
    expect(defaultStarterCode("cobol")).toBe("");
  });
});

describe("starterCodeFor", () => {
  it("uu tien starter_code cua giang vien", () => {
    const result = starterCodeFor(
      "cpp",
      { cpp: "int main(){return 0;}" },
      "def solve(): pass",
    );

    expect(result).toBe("int main(){return 0;}");
  });

  it("python dung fallback cua bai khi chua co starter rieng", () => {
    const result = starterCodeFor("python", { cpp: "x" }, "def solve(): pass");

    expect(result).toBe("def solve(): pass");
  });

  it("KHONG dua code python fallback sang nguon ngu khac", () => {
    const result = starterCodeFor("cpp", { python: "print(1)" }, "print(1)");

    // Không được chứa "print(" vì đó là code Python.
    expect(result).not.toContain("print(");
    expect(result).toBe(DEFAULT_SKELETONS.cpp);
  });

  it("java va javascript cung dung skeleton rieng", () => {
    expect(starterCodeFor("java", undefined, "print(1)")).toContain("public class Main");
    expect(starterCodeFor("javascript", undefined, "print(1)")).toContain("require('fs')");
  });

  it("khong bao gio tra chuoi rong", () => {
    for (const option of LANGUAGE_OPTIONS) {
      expect(starterCodeFor(option.value, undefined, "")).toBeTruthy();
    }
  });
});
