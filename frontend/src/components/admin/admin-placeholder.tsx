import { Construction } from "lucide-react";

import { EmptyState } from "@/components/shared/page-state";

export function AdminPlaceholder({ title }: { title: string }) {
  return <div className="space-y-6"><div><p className="text-sm font-medium text-indigo-700">Quản trị hệ thống</p><h1 className="mt-1 text-3xl font-bold tracking-tight">{title}</h1></div><EmptyState icon={Construction} title="Màn hình đang được chuẩn bị" description="Giao diện này sẽ được nối với API tương ứng ở phase tiếp theo." /></div>;
}
