import Image from "next/image";
import type { ReactNode } from "react";

/**
 * Khung nền dùng chung cho các màn hình chưa đăng nhập
 * (login, change-password, forgot-password): ảnh nền + thanh tiêu đề + footer.
 *
 * Ảnh cần có trong `public/images/`:
 *   - login-bg.jpg  (ảnh toà nhà UTC2)
 *   - utc2-logo.png (logo tròn của trường)
 */
export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="auth-layout relative flex min-h-dvh w-full flex-col overflow-x-clip">
      <Image
        src="/images/login-bg.jpg"
        alt=""
        fill
        priority
        sizes="100vw"
        className="-z-10 object-cover object-center"
      />
      {/* <div className="absolute inset-0 -z-10 bg-gradient-to-br from-blue-900/45 via-blue-800/25 to-slate-900/60" /> */}

      <header className="auth-header flex items-center justify-between gap-4 bg-gradient-to-r from-[#5577AF] via-[#424E89] to-[#281857] px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <div className="size-12 shrink-0 sm:size-16">
            <Image
              src="/images/utc2-logo.png"
              alt="Logo Trường Đại học Giao thông Vận tải"
              width={72}
              height={72}
              className="size-full object-contain"
            />
          </div>
          <div className="flex min-w-0 flex-col gap-1 leading-tight text-white">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-[#FCD34D] sm:text-sm">
              Trường Đại học Giao thông Vận tải
            </p>
            <p className="text-[9px] font-semibold uppercase tracking-wide text-white/85 sm:text-xs">
              Phân hiệu tại TP. Hồ Chí Minh
            </p>
          </div>
        </div>

        <div className="hidden max-w-[50%] flex-col gap-1 text-right leading-tight lg:flex">
          <p className="text-xs font-medium uppercase tracking-wide text-white xl:text-sm">
            Hệ thống thực hành lập trình và thi trực tuyến UTC2
          </p>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-300 xl:text-sm">
            Bộ môn Công nghệ thông tin
          </p>
        </div>
      </header>

      <main className="auth-main flex w-full min-w-0 flex-1 items-center justify-center px-3 py-6 sm:px-6 sm:py-8 lg:justify-end lg:px-10 xl:px-16">
        {children}
      </main>

      <footer className="auth-footer px-4 py-3 text-center text-[10px] font-medium uppercase tracking-wider text-white/85 sm:text-xs">
        © {new Date().getFullYear()} Code Judge Master. All rights reserved.
      </footer>
    </div>
  );
}
