-- Seed demo data
INSERT INTO course (course_id, course_name, term, created_by, start_date, end_date, avt_link, total_number_student)
VALUES ('CS101', 'Lập trình Python cơ bản', 'HK1-2026', '6451071003', '2026-09-01', '2026-12-31', 'https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg', 2)
ON CONFLICT (course_id) DO UPDATE SET course_name=EXCLUDED.course_name;

INSERT INTO enrollment (course_id, student_id) VALUES
  ('CS101', '6451071004'),
  ('CS101', '6451071005')
ON CONFLICT DO NOTHING;

INSERT INTO lesson (lesson_id, lesson_number, lesson_name, course_id, total_number_assignment, total_number_student_finished, start_date, end_date)
VALUES (1, 1, 'Buổi 1: Hello World', 'CS101', 5, 0, '2026-09-01', '2026-09-30')
ON CONFLICT (lesson_id) DO UPDATE SET lesson_name=EXCLUDED.lesson_name;

INSERT INTO problem (problem_id, lesson_id, title, description, time_limit_seconds, start_format_code, constraints, level, start_datetime, end_datetime, total_number_testcase, report) VALUES
  (1, 1, 'Hello World',            'In ra Hello World',    1, 'print("Hello World")', 'none', 'easy',  '2026-09-01 00:00:00', '2026-12-31 23:59:59', 5, NULL),
  (2, 1, 'Tính tổng 2 số',          'Nhập a, b in ra a+b',  1, 'a,b=map(int,input().split())', 'none', 'easy', '2026-09-01 00:00:00', '2026-12-31 23:59:59', 5, NULL),
  (3, 1, 'Số chẵn lẻ',              'In chan/ne',           1, 'n=int(input())', 'none', 'easy',       '2026-09-01 00:00:00', '2026-12-31 23:59:59', 5, NULL),
  (4, 1, 'Giai thừa',               'Tính n!',              1, 'n=int(input())', 'none', 'medium',     '2026-09-01 00:00:00', '2026-12-31 23:59:59', 5, NULL),
  (5, 1, 'Số nguyên tố',            'Kiểm tra n có phải SNT', 1, 'n=int(input())', 'none', 'medium',  '2026-09-01 00:00:00', '2026-12-31 23:59:59', 5, NULL)
ON CONFLICT (problem_id) DO UPDATE SET title=EXCLUDED.title;

INSERT INTO submission (problem_id, student_id, language, submitted_code, status, passed_count, submitted_datetime)
VALUES (1, '6451071004', 'python', 'print("Hello World")', 'accepted', 5, NOW())
ON CONFLICT DO NOTHING;

SELECT 'course' AS t, count(*) AS c FROM course
UNION ALL SELECT 'enrollment', count(*) FROM enrollment
UNION ALL SELECT 'lesson', count(*) FROM lesson
UNION ALL SELECT 'problem', count(*) FROM problem
UNION ALL SELECT 'submission', count(*) FROM submission;
