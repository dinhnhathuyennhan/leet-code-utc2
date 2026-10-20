import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6 py-16 text-center">
      <div className="max-w-md rounded-2xl border bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold text-indigo-600">404</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">Không tìm thấy trang</h1>
        <p className="mt-2 text-sm text-slate-500">Đường dẫn này không tồn tại hoặc đã được thay đổi.</p>
        <Link href="/" className="mt-6 inline-flex rounded-lg bg-[#34227a] px-4 py-2 text-sm font-semibold text-white">Về trang chủ</Link>
      </div>
    </main>
  );
}
