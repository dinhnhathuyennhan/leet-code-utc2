"use client";

import type { ReactNode } from "react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export type StudentCourseTab = "info" | "roster";

const TRIGGER =
  "rounded-none border-b-2 border-transparent bg-transparent px-5 py-3 text-base shadow-none data-[state=active]:border-indigo-600 data-[state=active]:bg-transparent data-[state=active]:font-semibold data-[state=active]:text-indigo-700 data-[state=active]:shadow-none dark:data-[state=active]:text-indigo-300";

interface StudentCourseDetailTabsProps {
  value: StudentCourseTab;
  onValueChange: (value: StudentCourseTab) => void;
  info: ReactNode;
  roster: ReactNode;
}

export function StudentCourseDetailTabs({ value, onValueChange, info, roster }: StudentCourseDetailTabsProps) {
  return (
    <Tabs
      value={value}
      onValueChange={(next) => onValueChange(next as StudentCourseTab)}
      className="rounded-2xl bg-card p-2 shadow-sm sm:p-4"
    >
      <div className="border-b">
        <TabsList className="h-auto gap-1 rounded-none bg-transparent p-0">
          <TabsTrigger value="info" className={TRIGGER}>Thông tin lớp</TabsTrigger>
          <TabsTrigger value="roster" className={TRIGGER}>Sinh viên cùng lớp</TabsTrigger>
        </TabsList>
      </div>

      <TabsContent value="info" className="mt-5">{info}</TabsContent>
      <TabsContent value="roster" className="mt-5">{roster}</TabsContent>
    </Tabs>
  );
}