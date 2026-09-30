// app/change-password/page.tsx
"use client";

import { useRouter } from "next/navigation";
import { ChangePasswordForm } from "@/components/shared/change-password-form";
import { useAuth } from "@/context/auth-context";
import { getHomePath } from "@/lib/auth/redirect";

export default function ChangePasswordPage() {
  const router = useRouter();
  const auth = useAuth();

  const handleSuccess = () => {
    if (auth.status === "authenticated") {
      router.replace(getHomePath({ ...auth.user, must_change_password: false }));
    }
  };

  return (
    <div
      className="flex min-h-screen w-full items-center justify-center p-4"
      style={{
        backgroundImage: "url('/images/change-password-bg.png')",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      }}
    >
      <ChangePasswordForm onSuccess={handleSuccess} />
    </div>
  );
}