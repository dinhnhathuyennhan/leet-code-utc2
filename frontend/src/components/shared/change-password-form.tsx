"use client";

import * as React from "react";
import Image from "next/image";
import { Controller, FormProvider, useForm, useFormContext, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight, AtSign, Check, CircleX, Loader2 } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { PasswordInput } from "./password-input";
import { LanguageStrip } from "./language-strip";

import { useAuth } from "@/context/auth-context";
import { ApiError } from "@/lib/api/error";
import {
  changePasswordSchema,
  type ChangePasswordFormValues,
} from "@/lib/validations/validate-field-form";

interface ChangePasswordFormProps {
  onSuccess?: () => void;
}

// ----------------------------------------------------------------------
// Custom Form Field Layout Components
// ----------------------------------------------------------------------
function FormItem({ children, className = "" }: React.PropsWithChildren<{ className?: string }>) {
  return <div className={`flex flex-col gap-1.5 mb-0 ${className}`}>{children}</div>;
}

function FormLabel({ children, className = "" }: React.PropsWithChildren<{ className?: string }>) {
  return <label className={`text-xs font-semibold text-slate-700 sm:text-sm ${className}`}>{children}</label>;
}

function FormMessage({ name }: { name: keyof ChangePasswordFormValues }) {
  const { formState: { errors } } = useFormContext<ChangePasswordFormValues>();
  const message = errors[name]?.message;

  return message ? (
    <p className="text-xs font-medium text-red-500">{String(message)}</p>
  ) : null;
}

// ----------------------------------------------------------------------
// Sub-component: Checklist kiểm tra mật khẩu trực quan
// ----------------------------------------------------------------------
interface PasswordChecklistProps {
  newPassword: string;
  currentPassword: string;
}

function PasswordChecklist({ newPassword, currentPassword }: PasswordChecklistProps) {
  const isDifferentFromCurrent = newPassword.length > 0 && newPassword !== currentPassword;
  const isMinLength = newPassword.length >= 8;
  const hasComplexChars =
    /[A-Z]/.test(newPassword) &&
    /[0-9]/.test(newPassword) &&
    /[!@#$%^&*]/.test(newPassword);

  const rules = [
    { label: "Khác mật khẩu hiện tại", valid: isDifferentFromCurrent },
    { label: "Tối thiểu 8 ký tự", valid: isMinLength },
    { label: "Chứa ít nhất 1 chữ hoa, 1 số và 1 ký tự đặc biệt (!@#$%^&*)", valid: hasComplexChars },
  ];

  return (
    <div className="mb-0 space-y-1 rounded-lg bg-slate-50/80 p-2.5 text-[11px] sm:text-xs">
      {rules.map((rule, idx) => (
        <div
          key={idx}
          className={`flex items-center gap-2 transition-colors ${
            rule.valid ? "font-medium text-emerald-600" : "text-slate-500"
          }`}
        >
          <Check className={`size-3.5 shrink-0 ${rule.valid ? "opacity-100 text-emerald-600" : "opacity-40"}`} />
          <span>{rule.label}</span>
        </div>
      ))}
    </div>
  );
}

// ----------------------------------------------------------------------
// Main Component
// ----------------------------------------------------------------------
export function ChangePasswordForm({ onSuccess }: ChangePasswordFormProps) {
  const { user, changePassword } = useAuth();
  const [apiError, setApiError] = React.useState<string | null>(null);

  const form = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(changePasswordSchema),
    mode: "onChange",
    defaultValues: {
      currentPassword: "",
      newPassword: "",
      confirmPassword: "",
      logoutOtherDevices: true,
    },
  });

  const { isSubmitting, errors } = form.formState;

  const newPassword = useWatch({ control: form.control, name: "newPassword" }) || "";
  const currentPassword = useWatch({ control: form.control, name: "currentPassword" }) || "";

  async function onSubmit(values: ChangePasswordFormValues) {
    setApiError(null);
    try {
      await changePassword({
        current_password: values.currentPassword,
        new_password: values.newPassword,
        confirm_password: values.confirmPassword,
      });

      onSuccess?.();
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 401) {
          form.setError("currentPassword", {
            message: "Mật khẩu hiện tại không chính xác",
          });
          return;
        }
        setApiError(error.detail || "Đã có lỗi xảy ra, vui lòng thử lại.");
        return;
      }
      setApiError("Mất kết nối từ server, vui lòng thử lại.");
    }
  }

  return (
    /* Khung Kính Mờ */
    <div className="mx-auto w-full max-w-[1100px] rounded-[2.5rem] bg-[#ffffff]/10 p-4 ring-1 ring-white/15 backdrop-blur-xl shadow-2xl sm:p-6 lg:p-6">
      <div className="grid grid-cols-1 items-center gap-6 lg:gap-8 lg:grid-cols-12">

        {/* ---------------- CỘT BÊN TRÁI: Logo, Text & Language Strip ---------------- */}
        <div className="flex flex-col items-center text-center lg:items-start lg:text-left justify-between space-y-6 lg:space-y-8 lg:col-span-5 lg:p-4 xl:col-span-5 h-full">
          {/* Top Logo */}
          <div className="flex items-center gap-3">
            <Image
              src="/images/logo-white.svg"
              alt="UTC2 Logo"
              width={36}
              height={36}
              className="h-9 w-auto"
            />
            <span className="text-sm font-medium tracking-widest text-white uppercase">
              UTC2 JUDGE MASTER
            </span>
          </div>

          <div className="flex flex-col items-center lg:items-start gap-6">
            {/* Hero Main Content */}
            <div className="space-y-4">
              <div>
                <span className="inline-block rounded-full bg-gradient-to-r from-[#1D83FF] to-[#351C7E] px-4 py-1.5 text-xs font-semibold text-white shadow-md">
                  Học Code Dễ Dàng
                </span>
              </div>
              <h1 className="text-2xl font-medium tracking-tight text-white sm:text-4xl lg:text-[40px]">
                Nền Tảng Thực Hành{" "}
                <span className="bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
                  Lập Trình
                </span>
              </h1>
              <p className="max-w-md text-xs sm:text-sm text-slate-300 leading-relaxed">
                Môi trường kiểm thử tự động, chuẩn hóa thuật toán với độ chính xác tuyệt đối, hỗ trợ sinh viên CNTT vững bước kiến tạo tương lai.
              </p>
            </div>

            {/* Language Strip Component */}
            <div className="pt-2">
              <LanguageStrip height={60} width={60} hiddenText={true} />
            </div>
          </div>
        </div>

        {/* ---------------- CỘT TRỐNG Ở GIỮA (1 CỘT - GIỮ NGUYÊN LAPTOP) ---------------- */}
        <div className="hidden lg:block lg:col-span-1" />

        {/* ---------------- CỘT BÊN PHẢI: Card Trắng chứa Form ---------------- */}
        <div className="lg:col-span-6 xl:col-span-6">
          <div className="flex flex-col gap-6 lg:gap-8 w-full rounded-[2rem] bg-white p-5 sm:p-8 lg:p-12 shadow-2xl">
            <header className="mb-0 text-center flex flex-col items-center justify-center gap-2 sm:gap-3">
              <h2 className="text-lg font-bold uppercase tracking-tight text-[#271756] sm:text-2xl mb-0">
                THIẾT LẬP MẬT KHẨU MỚI
              </h2>
              <p className="text-xs sm:text-sm text-slate-500">
                Cập nhật mật khẩu cá nhân để bảo vệ tài khoản nộp bài
              </p>
            </header>

            <FormProvider {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-4 space-y-3.5" noValidate>
                {/* Email UTC2 (Chỉ đọc) */}
                <FormItem>
                  <FormLabel>Email UTC2</FormLabel>
                  <div className="relative">
                    <AtSign className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
                    <Input
                      type="email"
                      value={user?.email || "nguyenvana@st.utc2.edu.vn"}
                      disabled
                      className="h-10 cursor-not-allowed rounded-xl bg-slate-50 pl-10 text-xs text-slate-500 sm:text-sm"
                    />
                  </div>
                </FormItem>

                {/* Mật khẩu hiện tại */}
                <Controller
                  control={form.control}
                  name="currentPassword"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Mật khẩu hiện tại <span className="text-red-500">*</span>
                      </FormLabel>
                      <PasswordInput
                        {...field}
                        autoComplete="current-password"
                        disabled={isSubmitting}
                        placeholder="••••••••••••"
                        aria-invalid={!!errors.currentPassword}
                        className={`h-10 rounded-xl text-xs sm:text-sm ${
                          errors.currentPassword
                            ? "border-red-500 !ring-0 focus-visible:border-red-500 focus-visible:!ring-2 focus-visible:!ring-red-500/20"
                            : ""
                        }`}
                      />
                      <FormMessage name="currentPassword" />
                    </FormItem>
                  )}
                />

                <div className="flex flex-col gap-3 mb-0">
                  {/* Mật khẩu mới */}
                  <Controller
                    control={form.control}
                    name="newPassword"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>
                          Mật khẩu mới <span className="text-red-500">*</span>
                        </FormLabel>
                        <PasswordInput
                          {...field}
                          autoComplete="new-password"
                          disabled={isSubmitting}
                          placeholder="••••••••••••"
                          aria-invalid={!!errors.newPassword}
                          className={`h-10 rounded-xl text-xs sm:text-sm ${
                            errors.newPassword
                              ? "border-red-500 !ring-0 focus-visible:border-red-500 focus-visible:!ring-2 focus-visible:!ring-red-500/20"
                              : ""
                          }`}
                        />
                        <FormMessage name="newPassword" />
                      </FormItem>
                    )}
                  />

                  {/* Password Checklist */}
                  <PasswordChecklist newPassword={newPassword} currentPassword={currentPassword} />
                </div>

                {/* Xác nhận mật khẩu mới */}
                <Controller
                  control={form.control}
                  name="confirmPassword"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>
                        Xác nhận mật khẩu mới <span className="text-red-500">*</span>
                      </FormLabel>
                      <PasswordInput
                        {...field}
                        autoComplete="new-password"
                        disabled={isSubmitting}
                        placeholder="••••••••••••"
                        aria-invalid={!!errors.confirmPassword}
                        className={`h-10 rounded-xl text-xs sm:text-sm ${
                          errors.confirmPassword
                            ? "border-red-500 !ring-0 focus-visible:border-red-500 focus-visible:!ring-2 focus-visible:!ring-red-500/20"
                            : ""
                        }`}
                      />
                      <FormMessage name="confirmPassword" />
                    </FormItem>
                  )}
                />

                {/* Checkbox Đăng xuất thiết bị khác */}
                <Controller
                  control={form.control}
                  name="logoutOtherDevices"
                  render={({ field }) => (
                    <div className="flex items-start sm:items-center gap-2 pt-0.5 mb-2">
                      <Checkbox
                        id="logoutOtherDevices"
                        checked={field.value}
                        onCheckedChange={field.onChange}
                        disabled={isSubmitting}
                        className="mt-0.5 sm:mt-0"
                      />
                      <label
                        htmlFor="logoutOtherDevices"
                        className="cursor-pointer select-none text-xs sm:text-sm text-slate-600 leading-tight"
                      >
                        Đăng xuất khỏi tất cả thiết bị khác sau khi hoàn tất
                      </label>
                    </div>
                  )}
                />

                {/* Hiển thị lỗi API chung */}
                {apiError && (
                  <Alert variant="destructive" className="py-2 text-xs">
                    <CircleX className="size-4 shrink-0" />
                    <AlertDescription>{apiError}</AlertDescription>
                  </Alert>
                )}

                {/* Submit Button */}
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="h-12 w-full rounded-xl bg-[linear-gradient(to_right,#1CB0FF_0%,#2F56D9_50%,#5F38B2_100%)] text-sm font-semibold shadow-lg shadow-blue-500/20 transition-all hover:opacity-95"
                >
                  Đổi mật khẩu
                  {isSubmitting ? (
                    <Loader2 className="ml-2 size-4 animate-spin" />
                  ) : (
                    <ArrowRight className="ml-2 size-4" />
                  )}
                </Button>
              </form>
            </FormProvider>
          </div>
        </div>

      </div>
    </div>
  );
}