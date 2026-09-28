"use client";

import type { ReactNode } from "react";
import { Construction } from "lucide-react";

import { EmptyState } from "@/components/shared/page-state";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export type CourseTab = "sessions" | "students" | "grades";

const TRIGGER =
  "rounded-none border-b-2 border-transparent bg-transparent px-5 py-3 text-base shadow-none data-[state=active]:border-indigo-600 data-[state=active]:bg-transparent data-[state=active]:font-semibold data-[state=active]:text-indigo-700 data-[state=active]:shadow-none dark:data-[state=active]:text-indigo-300";

function ComingSoon({ title }: { title: string }) {
  return <EmptyState icon={Construction} title={title} description="Màn hình này chưa có thiết kế — sẽ bổ sung sau." />;
}

interface CourseDetailTabsProps {
  value: CourseTab;
  onValueChange: (value: CourseTab) => void;
  updatedAtLabel: string;
  sessions: ReactNode;
}

export function CourseDetailTabs({ value, onValueChange, updatedAtLabel, sessions }: CourseDetailTabsProps) {
  return (
    <Tabs value={value} onValueChange={(next) => onValueChange(next as CourseTab)} className="rounded-2xl bg-card p-2 shadow-sm sm:p-4">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b">
        <TabsList className="h-auto gap-1 rounded-none bg-transparent p-0">
          <TabsTrigger value="sessions" className={TRIGGER}>Buổi học</TabsTrigger>
          <TabsTrigger value="students" className={TRIGGER}>Sinh viên</TabsTrigger>
          <TabsTrigger value="grades" className={TRIGGER}>Bảng điểm</TabsTrigger>
        </TabsList>
        <p className="pr-2 text-sm text-muted-foreground">Cập nhật lúc: {updatedAtLabel}</p>
      </div>

      <TabsContent value="sessions" className="mt-5">{sessions}</TabsContent>
      <TabsContent value="students" className="mt-5"><ComingSoon title="Danh sách sinh viên" /></TabsContent>
      <TabsContent value="grades" className="mt-5"><ComingSoon title="Bảng điểm" /></TabsContent>
    </Tabs>
  );
}
