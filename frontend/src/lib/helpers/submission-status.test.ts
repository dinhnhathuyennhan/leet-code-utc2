/**
 * Unit tests cho helper trạng thái bài nộp và quy đổi điểm.
 */
import { describe, expect, it } from "vitest";

import { canReviewCode, scoreOutOfTen, submissionStatusMeta } from "./submission-status";

describe("canReviewCode", () => {
  it("cho review khi accepted và pass hết testcase", () => {
    expect(canReviewCode({ status: "accepted", passed_count: 3, total_testcases: 3 })).toBe(true);
  });

  it.each([
    ["wrong_answer", 2, 3],
    ["compile_error", 0, 3],
    ["runtime_error", 1, 3],
    ["time_limit_exceeded", 2, 3],
    ["internal_error", 0, 3],
    ["error", 0, 3],
    ["pending", 0, 3],
    ["processing", 0, 3],
    // accepted nhưng chưa đủ test (giáo viên thêm testcase sau khi chấm)
    ["accepted", 2, 3],
    // bài không có testcase nào
    ["accepted", 0, 0],
    // wrong_answer mà passed_count lại bằng total (dữ liệu bất thường) vẫn không cho
    ["wrong_answer", 3, 3],
  ])('không cho review: status="%s", passed=%i/%i', (status, passed, total) => {
    expect(canReviewCode({ status, passed_count: passed, total_testcases: total })).toBe(false);
  });

  it("null/undefined -> false", () => {
    expect(canReviewCode(null)).toBe(false);
    expect(canReviewCode(undefined)).toBe(false);
  });
});

describe("submissionStatusMeta", () => {
  it.each([
    ["accepted", "Đạt"],
    ["wrong_answer", "Sai kết quả"],
    ["compile_error", "Lỗi biên dịch"],
    ["runtime_error", "Lỗi khi chạy"],
    ["time_limit_exceeded", "Quá thời gian"],
    ["pending", "Đang chờ chấm"],
  ])('maps "%s" to "%s"', (status, label) => {
    expect(submissionStatusMeta(status).label).toBe(label);
  });

  it("falls back to the raw status for unknown values", () => {
    expect(submissionStatusMeta("weird_status").label).toBe("weird_status");
  });

  it("falls back to a default label for an empty status", () => {
    expect(submissionStatusMeta("").label).toBe("Không rõ");
  });
});

describe("scoreOutOfTen", () => {
  it("returns null when there are no testcases", () => {
    expect(scoreOutOfTen(0, 0)).toBeNull();
  });

  it("returns 10 when every testcase passed", () => {
    expect(scoreOutOfTen(3, 3)).toBe(10);
  });

  it("rounds to one decimal place", () => {
    expect(scoreOutOfTen(1, 3)).toBe(3.3);
    expect(scoreOutOfTen(2, 3)).toBe(6.7);
  });

  it("returns 0 when nothing passed", () => {
    expect(scoreOutOfTen(0, 4)).toBe(0);
  });
});
