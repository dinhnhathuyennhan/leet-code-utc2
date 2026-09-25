// Schema kiểm tra định dạng dữ liệu phía client (use-case Đăng nhập, bước 4).
// Tách riêng khỏi component để tái dùng được và viết unit test được.

import { z } from "zod";

/** Sinh viên: @st.utc2.edu.vn — Giáo viên/Admin: @utc2.edu.vn */
const UTC2_EMAIL_PATTERN = /^[a-zA-Z0-9._%+-]+@(st\.)?utc2\.edu\.vn$/;

export const EMAIL_DOMAIN_MESSAGE = "Vui lòng sử dụng Email trường @st.utc2.edu.vn";

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, { message: "Vui lòng nhập Email UTC2" })
    .regex(UTC2_EMAIL_PATTERN, { message: EMAIL_DOMAIN_MESSAGE }),
  password: z.string().min(1, { message: "Vui lòng nhập mật khẩu" }),
  rememberMe: z.boolean().default(false),
});

export const changePasswordSchema = z
  .object({
    currentPassword: z
      .string()
      .min(1, { message: "Vui lòng nhập mật khẩu hiện tại" }),
    newPassword: z
      .string()
      .min(8, { message: "Mật khẩu mới phải có ít nhất 8 ký tự" })
      .regex(/[A-Z]/, { message: "Cần ít nhất 1 chữ cái viết hoa" })
      .regex(/[0-9]/, { message: "Cần ít nhất 1 chữ số" })
      .regex(/[!@#$%^&*]/, { message: "Cần ít nhất 1 ký tự đặc biệt (!@#$%^&*)" }),
    confirmPassword: z
      .string()
      .min(1, { message: "Vui lòng xác nhận mật khẩu mới" }),
    logoutOtherDevices: z.boolean(),
  })
  .refine((data) => data.newPassword !== data.currentPassword, {
    message: "Mật khẩu mới không được trùng với mật khẩu hiện tại",
    path: ["newPassword"],
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Mật khẩu xác nhận không trùng khớp",
    path: ["confirmPassword"],
  });

export type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>;
export type LoginFormValues = z.infer<typeof loginSchema>;