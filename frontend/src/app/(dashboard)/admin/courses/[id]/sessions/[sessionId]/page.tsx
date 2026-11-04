import { AdminLessonDetail } from "@/components/admin/admin-lesson-detail";

export default async function AdminLessonPage({ params }: { params: Promise<{ id: string; sessionId: string }> }) {
  const { id, sessionId } = await params;
  return <AdminLessonDetail courseId={id} lessonId={sessionId} />;
}
