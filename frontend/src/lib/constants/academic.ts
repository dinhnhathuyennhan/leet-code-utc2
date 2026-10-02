export const SEMESTERS = [1, 2, 3] as const;
export const ACADEMIC_YEARS = ["2023-2024", "2024-2025", "2025-2026"] as const;

// TODO(api): lấy học kỳ hiện tại từ server thay vì hằng số.
export const DEFAULT_TERM = { semester: 1, academicYear: "2024-2025" };
