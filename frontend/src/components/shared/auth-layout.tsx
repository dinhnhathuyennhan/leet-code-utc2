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
    <div className="auth-layout relative flex h-dvh min-h-0 flex-col overflow-hidden">
      <Image
        src="/images/login-bg.jpg"
        alt=""
        fill
        priority
        sizes="100vw"
        className="-z-10 object-cover object-center"
      />
      {/* <div className="absolute inset-0 -z-10 bg-gradient-to-br from-blue-900/45 via-blue-800/25 to-slate-900/60" /> */}

      <header className="auth-header flex items-center justify-between gap-4 bg-gradient-to-r from-[#5577AF] via-[#424E89] to-[#281857] px-4 py-3 sm:px-8">
        <div className="flex items-start gap-3 mt-3">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center">
            <div className="flex h-16 w-16 shrink-0 items-center justify-center">
              <Image
                src="/images/utc2-logo.png"
                alt="Logo Trường Đại học Giao thông Vận tải"
                width={72}
                height={72}
                className="h-20 w-20 object-contain"
              />
            </div>
          </div>
          <div className="flex gap-1 flex-col leading-tight text-white">
            <p className="text-[11px] font-semibold uppercase tracking-wide sm:text-sm text-[#FCD34D]">
              Trường Đại học Giao thông Vận tải
            </p>
            <p className="text-[9px] font-semibold uppercase tracking-wide text-white/85 sm:text-xs">
              Phân hiệu tại TP. Hồ Chí Minh
            </p>
          </div>
        </div>

        <div className="gap-2 hidden text-right leading-tight md:flex md:flex-col md:gap-1">
          <p className="text-xs font-medium uppercase tracking-wide text-white lg:text-sm text-[#FCD34D]">
            Hệ thống thực hành lập trình và thi trực tuyến UTC2
          </p>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-300 lg:text-sm">
            Bộ môn Công nghệ thông tin
          </p>
        </div>
      </header>

      {/* <main className="flex flex-1 items-center justify-center px-4 py-10 lg:justify-end lg:px-16"> */}
      <main className="auth-main flex min-h-0 flex-1 items-center justify-center overflow-y-auto px-4 py-4 sm:py-6 lg:justify-end lg:px-16 lg:py-2">
        {children}
      </main>

      <footer className="auth-footer px-4 py-4 text-center text-[10px] font-medium uppercase tracking-wider text-white/85 sm:text-xs">
        © {new Date().getFullYear()} Code Judge Master. All rights reserved.
      </footer>
    </div>
  );
}