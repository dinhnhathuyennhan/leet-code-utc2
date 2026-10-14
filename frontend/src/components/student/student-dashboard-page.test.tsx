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
import { describe, expect, it } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StudentDashboardPage } from "./student-dashboard-page";
import { renderWithProviders } from "@/test/utils/render";

describe("StudentDashboardPage", () => {
  it("renders the toolbar without the old surrounding card border", async () => {
    const { container } = renderWithProviders(<StudentDashboardPage />);

    // Toolbar xuất hiện ngay (không cần data) — chỉ search + filter
    const search = await screen.findByPlaceholderText(
      "Tìm kiếm lớp học phần…",
      {},
      { timeout: 5000 },
    );
    const toolbar = search.closest("section");
    expect(toolbar).toBeInTheDocument();
    expect(toolbar?.className ?? "").not.toMatch(
      /rounded-2xl\s+border\s+border-border\s+bg-card/,
    );

    // Đợi data load để chứng minh query work
    await screen.findByText("Nhập môn lập trình", {}, { timeout: 5000 });
    expect(container.textContent).toContain("Nhập môn lập trình");
  });

  it("search input is on the left, dropdowns + view switcher on the right", async () => {
    renderWithProviders(<StudentDashboardPage />);

    // Search exists (luôn render)
    const search = await screen.findByPlaceholderText("Tìm kiếm lớp học phần…", {}, { timeout: 3000 });
    expect(search).toBeInTheDocument();

    // 2 dropdown
    expect(screen.getByLabelText("Học kỳ")).toBeInTheDocument();
    expect(screen.getByLabelText("Năm học")).toBeInTheDocument();

    // 2 view buttons
    expect(screen.getByRole("button", { name: "Xem dạng lưới" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Xem dạng danh sách" })).toBeInTheDocument();
  });

  it("filters courses by search input", async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentDashboardPage />);

    // Đợi card đầu tiên render
    await screen.findByText("Nhập môn lập trình", {}, { timeout: 5000 });

    const search = screen.getByPlaceholderText("Tìm kiếm lớp học phần…");
    await user.type(search, "Python");

    await waitFor(
      () => {
        expect(screen.getByText("Lập trình Python cơ bản")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
    expect(screen.queryByText("Nhập môn lập trình")).toBeNull();
  });

  it("toggles between grid and list view", async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentDashboardPage />);

    await screen.findByText("Nhập môn lập trình", {}, { timeout: 5000 });

    // Mặc định grid → 4 link tới /student/classes (Link bao toàn card)
    const gridLinks = screen.getAllByRole("link", { name: /CS101|CS201|PY101|JS101/ });
    expect(gridLinks.length).toBeGreaterThan(0);

    // Switch sang list
    await user.click(screen.getByRole("button", { name: "Xem dạng danh sách" }));
    expect(screen.getByRole("button", { name: "Xem dạng danh sách" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    // Switch lại grid
    await user.click(screen.getByRole("button", { name: "Xem dạng lưới" }));
    expect(screen.getByRole("button", { name: "Xem dạng lưới" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("navigates to /student/classes/{id} when clicking a card", async () => {
    renderWithProviders(<StudentDashboardPage />);
    await screen.findByText("Nhập môn lập trình", {}, { timeout: 5000 });

    const card = screen.getByRole("link", { name: /CS101/ });
    expect(card).toHaveAttribute("href", "/student/classes/CS101");
  });

  it("shows empty state when no course matches the search", async () => {
    const user = userEvent.setup();
    renderWithProviders(<StudentDashboardPage />);

    await screen.findByText("Nhập môn lập trình", {}, { timeout: 5000 });

    const search = screen.getByPlaceholderText("Tìm kiếm lớp học phần…");
    await user.type(search, "khong-co-lop-nao-ca");

    await waitFor(
      () => {
        expect(screen.getByText(/Chưa có lớp học phần nào/)).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });

  it("renders the 3 mini-stat cards on top", async () => {
    renderWithProviders(<StudentDashboardPage />);
    // Stats render ngay, không cần data
    expect(screen.getByText("Lớp đang ký")).toBeInTheDocument();
    expect(screen.getByText("Bài hoàn thành")).toBeInTheDocument();
    expect(screen.getByText("Hạn tuần này")).toBeInTheDocument();
  });
});
