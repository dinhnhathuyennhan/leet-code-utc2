"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  AlertTriangle,
  ArrowLeft,
  ShieldAlert,
} from "lucide-react";

import { useBreadcrumbLabel } from "@/components/shared/breadcrumb-context";
import { Button } from "@/components/ui/button";

export default function PlagiarismDetailPage() {
  const { id } = useParams<{ id: string }>();
  useBreadcrumbLabel(`Đối chiếu mã nguồn (Ca #${id})`);

  const [status, setStatus] = useState<string | null>(null);

  const studentACode = `// Sinh viên: Đỗ Minh Quân - MSSV: 2151129805
class Node {
    int key;
    Node left, right;
    public Node(int item) {
        key = item;
        left = right = null;
    }
}

class BinarySearchTree {
    Node root;
    void insert(int key) {
        root = insertRec(root, key);
    }
    Node insertRec(Node root, int key) {
        if (root == null) {
            root = new Node(key);
            return root;
        }
        if (key < root.key)
            root.left = insertRec(root.left, key);
        else if (key > root.key)
            root.right = insertRec(root.right, key);
        return root;
    }
}`;

  const studentBCode = `// Sinh viên: Trần Văn Cường - MSSV: 2151129806
class TreeNode {
    int val;
    TreeNode left, right;
    public TreeNode(int v) {
        val = v;
        left = right = null;
    }
}

class MyBST {
    TreeNode root;
    void insert(int val) {
        root = insertRec(root, val);
    }
    TreeNode insertRec(TreeNode root, int val) {
        if (root == null) {
            root = new TreeNode(val);
            return root;
        }
        if (val < root.val)
            root.left = insertRec(root.left, val);
        else if (val > root.val)
            root.right = insertRec(root.right, val);
        return root;
    }
}`;

  return (
    <div className="space-y-6">
      {/* ─── Top Header ────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Button asChild variant="outline" size="sm" className="gap-1.5 border-slate-300">
            <Link href="/teacher">
              <ArrowLeft className="size-4" /> Quay lại
            </Link>
          </Button>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-2xl">
              Đối chiếu mã nguồn đạo văn #{id}
            </h1>
            <p className="text-xs text-muted-foreground">
              Bài tập: BST_01 - Cây nhị phân tìm kiếm · Lớp JAVA01
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <Button
            onClick={() => setStatus("ignored")}
            variant="outline"
            className="border-slate-300 font-semibold"
          >
            Bỏ qua nghi vấn
          </Button>
          <Button
            onClick={() => setStatus("penalty")}
            className="bg-red-600 font-semibold text-white hover:bg-red-700"
          >
            <ShieldAlert className="size-4 mr-1.5" /> Xác nhận vi phạm (0 điểm)
          </Button>
        </div>
      </div>

      {status && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm font-semibold text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300">
          ✓ Đã lưu quyết định xử lý: {status === "penalty" ? "Kỷ luật 0 điểm cả 2 bài nộp vi phạm" : "Bỏ qua nghi vấn tương đồng"}.
        </div>
      )}

      {/* ─── Metrics Banner ────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-red-200 bg-red-50/70 p-5 shadow-xs dark:border-red-500/30 dark:bg-red-500/10">
        <div className="flex items-center gap-3">
          <div className="flex size-11 items-center justify-center rounded-xl bg-red-600 text-white">
            <AlertTriangle className="size-6" />
          </div>
          <div>
            <p className="text-lg font-bold text-red-950 dark:text-red-200">
              Mức độ tương đồng cấu trúc cây AST: 88.5%
            </p>
            <p className="text-xs text-red-800 dark:text-red-300">
              Thuật toán phát hiện sự trùng khớp cấu trúc lặp, biến đổi tên định danh (variable renaming), và tương đồng giải thuật 100%.
            </p>
          </div>
        </div>
      </div>

      {/* ─── Side-by-side comparison ──────────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Sinh viên 1 */}
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-xl border bg-card p-3.5 shadow-xs">
            <div className="flex items-center gap-2.5">
              <span className="flex size-8 items-center justify-center rounded-full bg-indigo-100 font-bold text-xs text-indigo-900">
                1
              </span>
              <div>
                <p className="text-sm font-bold">Đỗ Minh Quân</p>
                <p className="text-xs text-muted-foreground">MSSV: 2151129805</p>
              </div>
            </div>
            <span className="text-xs text-muted-foreground">Nộp lúc 21:15:30</span>
          </div>

          <div className="overflow-hidden rounded-xl border bg-slate-950 text-slate-100 shadow-sm">
            <div className="border-b border-slate-800 bg-slate-900 px-4 py-2 font-mono text-xs text-slate-300">
              BinarySearchTree.java
            </div>
            <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-slate-200">
              <code>{studentACode}</code>
            </pre>
          </div>
        </div>

        {/* Sinh viên 2 */}
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-xl border bg-card p-3.5 shadow-xs">
            <div className="flex items-center gap-2.5">
              <span className="flex size-8 items-center justify-center rounded-full bg-red-100 font-bold text-xs text-red-900">
                2
              </span>
              <div>
                <p className="text-sm font-bold">Trần Văn Cường</p>
                <p className="text-xs text-muted-foreground">MSSV: 2151129806</p>
              </div>
            </div>
            <span className="text-xs text-muted-foreground">Nộp lúc 21:42:15</span>
          </div>

          <div className="overflow-hidden rounded-xl border bg-slate-950 text-slate-100 shadow-sm">
            <div className="border-b border-slate-800 bg-slate-900 px-4 py-2 font-mono text-xs text-slate-300">
              MyBST.java
            </div>
            <pre className="overflow-x-auto p-4 font-mono text-xs leading-relaxed text-slate-200">
              <code>{studentBCode}</code>
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
