"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Bot } from "lucide-react";

import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { Button } from "@/components/ui/button";

export default function PlagiarismDetailPage() {
  const { id } = useParams<{ id: string }>();
  useBreadcrumbLabel(`Đối chiếu mã nguồn (Ca #${id})`);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Button asChild variant="outline" size="sm">
          <Link href="/teacher/plagiarism"><ArrowLeft className="size-4" /> Quay lại</Link>
        </Button>
        <div>
          <h1 className="text-xl font-bold sm:text-2xl">Đối chiếu mã nguồn đạo văn #{id}</h1>
          <p className="text-xs text-muted-foreground">Dữ liệu chi tiết chưa được backend cung cấp.</p>
        </div>
      </div>

      <section className="rounded-xl border bg-card p-8 text-center shadow-sm">
        <Bot className="mx-auto mb-3 size-10 text-indigo-600" />
        <h2 className="font-semibold">Chưa có dữ liệu đối chiếu</h2>
        <p className="mt-1 text-sm text-muted-foreground">Không hiển thị dữ liệu seed hoặc thông tin sinh viên khi API chưa trả về kết quả thật.</p>
        {/* TODO: nối màn hình này với API plagiarism trước khi mở các thao tác xử lý. */}
        <div className="mt-5 flex justify-center gap-2">
          <Button disabled variant="outline">Bỏ qua nghi vấn</Button>
          <Button disabled>Xác nhận vi phạm</Button>
        </div>
      </section>
    </div>
  );
}
