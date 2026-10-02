"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Controller,
  FormProvider,
  useForm,
  useFormContext,
} from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import type { z } from "zod";
import { ArrowRight, AtSign, CircleX, Loader2 } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { LanguageStrip } from "./language-strip";
import { PasswordInput } from "./password-input";

import { useAuth } from "@/context/auth-context";
import { ApiError } from "@/lib/api/error";
import { loginSchema, type LoginFormValues } from "@/lib/validations/validate-field-form";

import type { UserResponse } from "@/lib/api/types";

interface LoginFormProps {
  onSuccess?: (user: UserResponse) => void;
}

const FormField = Controller;

function FormItem({
  children,
  className = "",
}: React.PropsWithChildren<{ className?: string }>) {
  return <div className={className}>{children}</div>;
}

function FormControl({ children }: React.PropsWithChildren) {
  return <>{children}</>;
}

function FormLabel({
  children,
  className = "",
}: React.PropsWithChildren<{ className?: string }>) {
  return <label className={className}>{children}</label>;
}

function FormMessage({ name }: { name: string }) {
  const {
    formState: { errors },
  } = useFormContext();
  const message = errors[name]?.message;

  return message ? (
    <p className="text-xs font-normal text-red-500 mt-1">{String(message)}</p>
  ) : null;
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const { login } = useAuth();
  const [connectionError, setConnectionError] = React.useState<string | null>(null);

  const form = useForm<z.input<typeof loginSchema>, unknown, LoginFormValues>({
    resolver: zodResolver(loginSchema),
    mode: "onSubmit",
    reValidateMode: "onChange",
    defaultValues: {
      email: "",
      password: "",
      rememberMe: false,
    },
  });

  const isSubmitting = form.formState.isSubmitting;
  const errors = form.formState.errors;

  async function onSubmit(values: LoginFormValues) {
    setConnectionError(null);
    try {
      const user = await login({
        email: values.email,
        password: values.password,
      });

      onSuccess?.(user);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.isNetworkError) {
          setConnectionError("Mất kết nối từ server, vui lòng thử lại.");
          return;
        }

        form.setError("password", {
          message: error.detail || "Email hoặc mật khẩu không chính xác",
        });
        form.resetField("password", { keepError: true });
        return;
      }

      setConnectionError("Đã có lỗi xảy ra, vui lòng thử lại.");
    }
  }

  return (
    /* Outer Container: Tối ưu bo góc và padding thoáng hơn cho iPhone (p-3.5, rounded-[2rem]) */
    <div className="w-full max-w-[420px] sm:w-fit sm:max-w-full rounded-[2rem] sm:rounded-[3rem] bg-white/10 p-3.5 ring-1 ring-white/25 backdrop-blur-sm sm:p-6">
      
      {/* Inner White Card: p-5 & space-y-5 tạo độ thở hoàn hảo trên iPhone */}
      <div className="rounded-[1.5rem] sm:rounded-[2rem] bg-white p-5 space-y-5 sm:space-y-8 sm:p-8 shadow-2xl">
        
        {/* Header Section */}
        <header className="space-y-1.5 sm:space-y-2 text-center">
          <Image
            src="/images/code-logo.svg"
            alt="UTC2 Logo"
            width={72}
            height={40}
            className="mx-auto mb-3 h-10 w-auto sm:mb-5 sm:h-12"
          />
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#271756]">
            UTC2 Judge Master
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 leading-relaxed max-w-[280px] sm:max-w-none mx-auto">
            Sử dụng tài khoản nội bộ UTC2 để truy cập hệ thống lập trình
          </p>
        </header>

        <FormProvider {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="flex flex-col gap-4 sm:gap-6"
            noValidate
          >
            {/* Email Field */}
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem className="flex w-full flex-col gap-1.5 lg:w-[412px]">
                  <FormLabel className="text-slate-700 text-xs sm:text-sm font-semibold">
                    Email UTC2 <span className="text-red-500">*</span>
                  </FormLabel>
                  <FormControl>
                    <div className="relative">
                      <AtSign
                        aria-hidden
                        className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-[#808D9F]"
                      />
                      <Input
                        {...field}
                        type="email"
                        autoComplete="username"
                        disabled={isSubmitting}
                        placeholder="nguyenvana@st.utc2.edu.vn"
                        aria-invalid={!!errors.email}
                        className={`h-11 sm:h-12 lg:h-[48px] rounded-xl pl-11 text-xs sm:text-sm ${
                          errors.email
                            ? "border-red-500 !ring-0 focus-visible:!ring-3 focus-visible:!ring-red-500/20 focus-visible:border-red-500"
                            : ""
                        }`}
                      />
                    </div>
                  </FormControl>
                  <FormMessage name="email" />
                </FormItem>
              )}
            />

            {/* Password Field */}
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem className="flex w-full flex-col gap-1.5 lg:w-[412px]">
                  <div className="flex items-baseline justify-between gap-2">
                    <FormLabel className="text-slate-700 text-xs sm:text-sm font-semibold">
                      Mật khẩu <span className="text-red-500">*</span>
                    </FormLabel>
                    <Link
                      href="/forgot-password"
                      className="text-slate-700 text-xs sm:text-sm font-semibold hover:text-blue-600 transition-colors"
                    >
                      Quên mật khẩu?
                    </Link>
                  </div>
                  <FormControl>
                    <PasswordInput
                      {...field}
                      autoComplete="current-password"
                      disabled={isSubmitting}
                      placeholder="••••••••••••"
                      aria-invalid={!!errors.password}
                      className={`h-11 sm:h-12 lg:h-[48px] rounded-xl text-xs sm:text-sm ${
                        errors.password
                          ? "border-red-500 !ring-0 focus-visible:!ring-3 focus-visible:!ring-red-500/20 focus-visible:border-red-500"
                          : ""
                      }`}
                    />
                  </FormControl>
                  <FormMessage name="password" />
                </FormItem>
              )}
            />

            {/* Remember Me Checkbox */}
            <FormField
              control={form.control}
              name="rememberMe"
              render={({ field }) => (
                <FormItem className="flex items-center gap-2.5 space-y-0 mb-0 pt-0.5">
                  <FormControl>
                    <Checkbox
                      checked={field.value}
                      onCheckedChange={field.onChange}
                      disabled={isSubmitting}
                    />
                  </FormControl>
                  <FormLabel className="text-xs sm:text-sm font-normal text-slate-600 cursor-pointer select-none">
                    Ghi nhớ phiên đăng nhập
                  </FormLabel>
                </FormItem>
              )}
            />

            {/* Connection Error Alert */}
            {connectionError && (
              <Alert
                variant="destructive"
                className="items-center gap-2 rounded-xl border-red-300 bg-red-50 py-2.5 text-xs sm:text-sm text-red-600"
              >
                <CircleX className="size-4 shrink-0" />
                <AlertDescription className="text-red-600">
                  {connectionError}
                </AlertDescription>
              </Alert>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={isSubmitting}
              className="h-11 sm:h-12 lg:h-[48px] w-full rounded-xl bg-[linear-gradient(to_right,#1CB0FF_0%,#2F56D9_50%,#5F38B2_100%)] text-xs sm:text-base font-semibold shadow-lg shadow-blue-500/20 transition-[background-image,opacity] duration-200 hover:bg-[linear-gradient(to_right,#5F38B2_24%,#29184C_100%)] disabled:opacity-50"
            >
              Đăng nhập
              {isSubmitting ? (
                <Loader2 className="ml-2 size-4 sm:size-5 animate-spin" />
              ) : (
                <ArrowRight className="ml-2 size-4 sm:size-5" />
              )}
            </Button>
          </form>
        </FormProvider>

        {/* Footer Language Strip */}
        <div className="pt-1">
          <LanguageStrip />
        </div>
      </div>
    </div>
  );
}