import { AdminBankProblemDetail } from "@/components/admin/admin-bank-problem-detail";

export default async function AdminBankProblemPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AdminBankProblemDetail id={Number(id)} />;
}
