/**
 * Component test: verify toggle VI/EN thực sự đổi nội dung giao diện.
 *
 * Đây là test hồi quy cho lỗi "toggle ngôn ngữ chỉ đổi màu chứ không đổi chữ".
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { StudentDashboardPage } from "./student-dashboard-page";
import { renderWithProviders } from "@/test/utils/render";
import { LocaleProvider, resetLocaleStore, useLocale } from "@/lib/i18n";

vi.mock("@/lib/api/endpoints/dashboard", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api/endpoints/dashboard")>();
  return {
    ...actual,
    getStudentOverview: vi.fn(async () => ({
      total_classes: 1,
      completed_problems: 5,
      total_problems: 12,
      average_score: 7.5,
      courses: [
        {
          id: "CS101",
          code: "CS101",
          name: "Nhập môn lập trình",
          start_date: "2024-09-01",
          language: "java",
          status: "ongoing",
          teacher_name: "Nguyễn Văn A",
          semester: 1,
          academic_year: "2024-2025",
          group: 1,
        },
      ],
    })),
  };
});

/** Toggle VI/EN giống hệt component trong topbar. */
function LanguageToggle() {
  const { locale, setLocale } = useLocale();
  return (
    <div>
      <button type="button" onClick={() => setLocale("en")}>
        switch-to-en
      </button>
      <button type="button" onClick={() => setLocale("vi")}>
        switch-to-vi
      </button>
      <span data-testid="current-locale">{locale}</span>
    </div>
  );
}

describe("i18n — LanguageToggle đổi nội dung thật", () => {
  beforeEach(() => {
    window.localStorage.clear();
    // Store locale sống ở module scope → reset giữa các test.
    resetLocaleStore();
    vi.clearAllMocks();
  });

  it("dashboard đổi từ tiếng Việt sang tiếng Anh", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <LocaleProvider>
        <LanguageToggle />
        <StudentDashboardPage />
      </LocaleProvider>,
    );

    // Trạng thái ban đầu: tiếng Việt.
    await screen.findByText("Lớp đang ký");
    expect(screen.getByText("Bài hoàn thành")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Tìm kiếm lớp học phần…")).toBeInTheDocument();
    expect(screen.getByLabelText("Học kỳ")).toBeInTheDocument();

    // Chuyển sang tiếng Anh.
    await user.click(screen.getByRole("button", { name: "switch-to-en" }));

    await waitFor(() => {
      expect(screen.getByText("Enrolled courses")).toBeInTheDocument();
    });
    expect(screen.getByText("Completed problems")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Search courses…")).toBeInTheDocument();
    expect(screen.getByLabelText("Semester")).toBeInTheDocument();

    // Nhãn tiếng Việt cũ phải biến mất.
    expect(screen.queryByText("Lớp đang ký")).toBeNull();
    expect(screen.queryByText("Bài hoàn thành")).toBeNull();

    // Chuyển lại tiếng Việt.
    await user.click(screen.getByRole("button", { name: "switch-to-vi" }));

    await waitFor(() => {
      expect(screen.getByText("Lớp đang ký")).toBeInTheDocument();
    });
    expect(screen.getByPlaceholderText("Tìm kiếm lớp học phần…")).toBeInTheDocument();
  });

  it("nhãn học kỳ hiển thị theo ngôn ngữ", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <LocaleProvider>
        <LanguageToggle />
        <StudentDashboardPage />
      </LocaleProvider>,
    );

    await screen.findByText("Lớp đang ký");
    // Trigger của dropdown học kỳ.
    const trigger = screen.getByLabelText("Học kỳ");
    expect(trigger).toHaveTextContent("Tất cả học kỳ");

    await user.click(screen.getByRole("button", { name: "switch-to-en" }));

    await waitFor(() => {
      expect(screen.getByLabelText("Semester")).toHaveTextContent("All semesters");
    });
  });
});
