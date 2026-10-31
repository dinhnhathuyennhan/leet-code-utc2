import { AdminProblemDetail } from "@/components/admin/admin-problem-detail";

export default async function AdminProblemPage({ params }: { params: Promise<{ id: string; sessionId: string; problemId: string }> }) {
  const { id, sessionId, problemId } = await params;
  return <AdminProblemDetail courseId={id} lessonId={sessionId} problemId={problemId} />;
}
