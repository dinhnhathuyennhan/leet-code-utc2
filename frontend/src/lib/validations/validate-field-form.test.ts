import { describe, expect, it } from "vitest";
import { changePasswordSchema, containsPersonalInfo } from "./validate-field-form";

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

describe("containsPersonalInfo", () => {
  it("phát hiện MSSV kể cả khi email không trùng MSSV", () => {
    expect(containsPersonalInfo("Mk@6451071234", "nguyenvana@st.utc2.edu.vn", "6451071234")).toBe(true);
  });

  it("phát hiện phần trước @ của email, không phân biệt hoa thường", () => {
    expect(containsPersonalInfo("Xx-NguyenVanA-1", "nguyenvana@st.utc2.edu.vn", null)).toBe(true);
  });

  it("bỏ qua chuỗi ngắn hơn 4 ký tự và mật khẩu không chứa thông tin cá nhân", () => {
    expect(containsPersonalInfo("Abc@12345", "abc@st.utc2.edu.vn", "")).toBe(false);
    expect(containsPersonalInfo("Mk@2026-utc", "nguyenvana@st.utc2.edu.vn", "6451071234")).toBe(false);
  });
});
