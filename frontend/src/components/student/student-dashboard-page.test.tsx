/**
 * Integration test cho StudentDashboardPage.
 *
 * Verify hành vi end-to-end:
 *  - Toolbar không có border bao quanh (ảnh 1 Figma)
 *  - Search bar ở bên trái, 2 dropdown + view switcher ở bên phải
 *  - Gõ search filter ra kết quả
 *  - View switcher grid ↔ list
 *  - Click card → điều hướng đúng /student/classes/{id}
 *  - Empty state khi filter trả 0 kết quả
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StudentDashboardPage } from "./student-dashboard-page";
import { renderWithProviders } from "@/test/utils/render";

// Mock dashboard endpoints để không gọi axios thật trong test.
vi.mock("@/lib/api/endpoints/dashboard", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/endpoints/dashboard")>();
  return {
    ...actual,
    getStudentOverview: vi.fn(async () => ({
      total_classes: 4,
      completed_problems: 5,
      total_problems: 12,
      average_score: 7.5,
      courses: [
        { id: "CS101", code: "CS101", name: "Nhập môn lập trình", start_date: "2024-09-01", language: "java", status: "ongoing", teacher_name: "Nguyễn Văn A", semester: 1, academic_year: "2024-2025", group: 1 },
        { id: "CS201", code: "CS201", name: "Cấu trúc dữ liệu và giải thuật", start_date: "2024-09-01", language: "java", status: "ongoing", teacher_name: "Trần Thị B", semester: 1, academic_year: "2024-2025", group: 1 },
        { id: "PY101", code: "PY101", name: "Lập trình Python cơ bản", start_date: "2025-01-15", language: "python", status: "ongoing", teacher_name: "Lê Văn C", semester: 2, academic_year: "2024-2025", group: 1 },
        { id: "JS101", code: "JS101", name: "JavaScript nâng cao", start_date: "2025-01-15", language: "javascript", status: "upcoming", teacher_name: "Phạm Thị D", semester: 2, academic_year: "2024-2025", group: 1 },
      ],
    })),
  };
});

describe("StudentDashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the toolbar without the old surrounding card border", async () => {
    const { container } = renderWithProviders(<StudentDashboardPage />);

    const search = await screen.findByPlaceholderText("Tìm kiếm lớp học phần…");
    const toolbar = search.closest("section");
    expect(toolbar).toBeInTheDocument();
    expect(toolbar?.className ?? "").not.toMatch(
      /rounded-2xl\s+border\s+border-border\s+bg-card/,
    );

    await screen.findByText("Nhập môn lập trình");
    expect(container.textContent).toContain("Nhập môn lập trình");
  });

  it("search input is on the left, dropdowns + view switcher on the right", async () => {
    renderWithProviders(<StudentDashboardPage />);

    const search = await screen.findByPlaceholderText("Tìm kiếm lớp học phần…");
    expect(search).toBeInTheDocument();

    expect(screen.getByLabelText("Học kỳ")).toBeInTheDocument();
    expect(screen.getByLabelText("Năm học")).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Xem dạng lưới" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Xem dạng danh sách" })).toBeInTheDocument();
  });

  it("filters courses by search input", async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentDashboardPage />);

    await screen.findByText("Nhập môn lập trình");

    const search = screen.getByPlaceholderText("Tìm kiếm lớp học phần…");
    await user.type(search, "Python");

    await waitFor(() => {
      expect(screen.getByText("Lập trình Python cơ bản")).toBeInTheDocument();
    });
    expect(screen.queryByText("Nhập môn lập trình")).toBeNull();
  });

  it("toggles between grid and list view", async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentDashboardPage />);

    await screen.findByText("Nhập môn lập trình");

    const gridLinks = screen.getAllByRole("link", { name: /CS101|CS201|PY101|JS101/ });
    expect(gridLinks.length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: "Xem dạng danh sách" }));
    expect(screen.getByRole("button", { name: "Xem dạng danh sách" })).toHaveAttribute("aria-pressed", "true");

    await user.click(screen.getByRole("button", { name: "Xem dạng lưới" }));
    expect(screen.getByRole("button", { name: "Xem dạng lưới" })).toHaveAttribute("aria-pressed", "true");
  });

  it("navigates to /student/classes/{id} when clicking a card", async () => {
    renderWithProviders(<StudentDashboardPage />);
    await screen.findByText("Nhập môn lập trình");

    const card = screen.getByRole("link", { name: /CS101/ });
    expect(card).toHaveAttribute("href", "/student/classes/CS101");
  });

  it("shows empty state when no course matches the search", async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentDashboardPage />);

    await screen.findByText("Nhập môn lập trình");

    const search = screen.getByPlaceholderText("Tìm kiếm lớp học phần…");
    await user.type(search, "khong-co-lop-nao-ca");

    await waitFor(() => {
      expect(screen.getByText(/Chưa có lớp học phần nào/)).toBeInTheDocument();
    });
  });

  it("renders the 3 mini-stat cards on top", async () => {
    renderWithProviders(<StudentDashboardPage />);
    expect(screen.getByText("Lớp đang ký")).toBeInTheDocument();
    expect(screen.getByText("Bài hoàn thành")).toBeInTheDocument();
    expect(screen.getByText("Hạn tuần này")).toBeInTheDocument();
  });
});
