import { AdminCourseDetail } from "@/components/admin/admin-course-detail";

export default async function AdminCourseDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AdminCourseDetail id={id} />;
}
