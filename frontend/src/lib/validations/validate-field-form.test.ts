import { describe, expect, it } from "vitest";
import { changePasswordSchema } from "./validate-field-form";

function parse(newPassword: string) {
  return changePasswordSchema.safeParse({
    currentPassword: "Old-Password-123",
    newPassword,
    confirmPassword: newPassword,
    logoutOtherDevices: true,
  });
}

describe("changePasswordSchema", () => {
  it.each(["Abcdef1!", "Mk_2026.utc", "Xin-Chao-9"])("chấp nhận mật khẩu mạnh %s", (pw) => {
    expect(parse(pw).success).toBe(true);
  });

  it.each([
    ["Ab1!", "Mật khẩu mới phải có ít nhất 8 ký tự"],
    ["abcdef1!", "Cần ít nhất 1 chữ cái viết hoa"],
    ["Abcdefg!", "Cần ít nhất 1 chữ số"],
    ["Abcdefg1", "Cần ít nhất 1 ký tự đặc biệt (ví dụ !@#$%^&*)"],
    ["Abcdef1 ", "Cần ít nhất 1 ký tự đặc biệt (ví dụ !@#$%^&*)"],
  ])("từ chối %s", (pw, message) => {
    const result = parse(pw);
    expect(result.success).toBe(false);
    expect(result.error?.issues.map((i) => i.message)).toContain(message);
  });
});
