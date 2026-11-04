import { AdminSubmissionDetail } from "@/components/admin/admin-submission-detail";

export default async function AdminSubmissionPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AdminSubmissionDetail id={id} />;
}
