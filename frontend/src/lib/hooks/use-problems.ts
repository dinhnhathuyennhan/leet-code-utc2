import { keepPreviousData, useInfiniteQuery } from "@tanstack/react-query";

import { getProblems, type ProblemListParams } from "@/lib/api/endpoints/problems";

export const problemKeys = {
  all: ["problems"] as const,
  infinite: (params: Omit<ProblemListParams, "page">) => [...problemKeys.all, "infinite", params] as const,
};

/** Danh sách bài phân trang dạng "tải thêm": mỗi lần cuộn tới cuối gọi trang kế tiếp. */
export function useInfiniteProblems(params: Omit<ProblemListParams, "page">, enabled = true) {
  return useInfiniteQuery({
    queryKey: problemKeys.infinite(params),
    queryFn: ({ pageParam }) => getProblems({ ...params, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page * last.page_size < last.total ? last.page + 1 : undefined),
    placeholderData: keepPreviousData,
    // Danh sách đổi theo mọi thao tác gắn/tạo/xoá/sao chép bài ở nhiều màn hình khác nhau.
    // Thay vì invalidate ở từng chỗ, luôn coi là cũ: mỗi lần mở picker (mount hoặc bật
    // `enabled`) đều tải lại, trong lúc đó vẫn hiện dữ liệu đã cache.
    staleTime: 0,
    // Không tải lại toàn bộ các trang đã cuộn mỗi lần giảng viên chuyển tab rồi quay lại.
    refetchOnWindowFocus: false,
    enabled,
  });
}
