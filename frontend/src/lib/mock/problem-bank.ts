export interface MockProblemBankItem {
  id: string;
  code: string;
  title: string;
  level: "DỄ" | "TRUNG BÌNH" | "KHÓ";
  description: string;
}

const MOCK_DESCRIPTION = "Sử dụng StringTokenizer hoặc regex \\s+ để tách văn bản thành các token đơn lẻ và đếm số lượng từ phân biệt.";

// MOCKUP: Dữ liệu tĩnh chỉ phục vụ dựng giao diện trước khi kết nối API ngân hàng đề.
export const MOCK_PUBLIC_PROBLEMS: MockProblemBankItem[] = Array.from({ length: 7 }, (_, index) => ({
  id: `public-${index + 1}`,
  code: "ARR_01",
  title: "Tách từ và đếm tần suất xuất hiện",
  level: "DỄ",
  description: MOCK_DESCRIPTION,
}));

// MOCKUP: Danh sách đề của giảng viên để kiểm tra tab, tìm kiếm và các nút thao tác.
export const MOCK_MY_PROBLEMS: MockProblemBankItem[] = Array.from({ length: 12 }, (_, index) => ({
  id: `mine-${index + 1}`,
  code: "ARR_01",
  title: "Tách từ và đếm tần suất xuất hiện",
  level: "DỄ",
  description: MOCK_DESCRIPTION,
}));
