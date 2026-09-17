--
-- PostgreSQL database dump
--

\restrict 5pQs2HdlAvKpj5RsZOXnCyB5oK4tfHNAigSa2egiNey4vgMI1EXx9dJX3iPTUxM

-- Dumped from database version 17.11
-- Dumped by pg_dump version 17.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: chamcode
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO chamcode;

--
-- Name: course; Type: TABLE; Schema: public; Owner: chamcode
--

CREATE TABLE public.course (
    course_id character varying(50) NOT NULL,
    course_name character varying NOT NULL,
    created_by character varying(50) NOT NULL,
    term character varying NOT NULL,
    start_date timestamp without time zone NOT NULL,
    end_date timestamp without time zone NOT NULL,
    total_number_student integer NOT NULL
);


ALTER TABLE public.course OWNER TO chamcode;

--
-- Name: enrollment; Type: TABLE; Schema: public; Owner: chamcode
--

CREATE TABLE public.enrollment (
    enrollment_id integer NOT NULL,
    course_id character varying(50) NOT NULL,
    student_id character varying(50) NOT NULL
);


ALTER TABLE public.enrollment OWNER TO chamcode;

--
-- Name: enrollment_enrollment_id_seq; Type: SEQUENCE; Schema: public; Owner: chamcode
--

CREATE SEQUENCE public.enrollment_enrollment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.enrollment_enrollment_id_seq OWNER TO chamcode;

--
-- Name: enrollment_enrollment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: chamcode
--

ALTER SEQUENCE public.enrollment_enrollment_id_seq OWNED BY public.enrollment.enrollment_id;


--
-- Name: lesson; Type: TABLE; Schema: public; Owner: chamcode
--

CREATE TABLE public.lesson (
    lesson_id integer NOT NULL,
    lesson_number integer NOT NULL,
    lesson_name character varying NOT NULL,
    course_id character varying(50) NOT NULL,
    total_number_assignment integer NOT NULL,
    total_number_student_finished integer NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL
);


ALTER TABLE public.lesson OWNER TO chamcode;

--
-- Name: lesson_lesson_id_seq; Type: SEQUENCE; Schema: public; Owner: chamcode
--

CREATE SEQUENCE public.lesson_lesson_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.lesson_lesson_id_seq OWNER TO chamcode;

--
-- Name: lesson_lesson_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: chamcode
--

ALTER SEQUENCE public.lesson_lesson_id_seq OWNED BY public.lesson.lesson_id;


--
-- Name: problem; Type: TABLE; Schema: public; Owner: chamcode
--

CREATE TABLE public.problem (
    problem_id integer NOT NULL,
    lesson_id integer NOT NULL,
    title character varying NOT NULL,
    description character varying NOT NULL,
    time_limit_seconds integer NOT NULL,
    start_format_code character varying NOT NULL,
    constraints character varying NOT NULL,
    level character varying NOT NULL,
    hint character varying,
    complexity character varying,
    start_datetime timestamp without time zone NOT NULL,
    end_datetime timestamp without time zone NOT NULL,
    total_number_testcase integer NOT NULL,
    report character varying
);


ALTER TABLE public.problem OWNER TO chamcode;

--
-- Name: problem_problem_id_seq; Type: SEQUENCE; Schema: public; Owner: chamcode
--

CREATE SEQUENCE public.problem_problem_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.problem_problem_id_seq OWNER TO chamcode;

--
-- Name: problem_problem_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: chamcode
--

ALTER SEQUENCE public.problem_problem_id_seq OWNED BY public.problem.problem_id;


--
-- Name: submission; Type: TABLE; Schema: public; Owner: chamcode
--

CREATE TABLE public.submission (
    submission_id integer NOT NULL,
    problem_id integer NOT NULL,
    student_id character varying(50) NOT NULL,
    language character varying NOT NULL,
    submitted_code character varying NOT NULL,
    status character varying NOT NULL,
    compile_output character varying,
    feedback character varying,
    passed_count integer NOT NULL,
    submitted_datetime timestamp without time zone NOT NULL
);


ALTER TABLE public.submission OWNER TO chamcode;

--
-- Name: submission_submission_id_seq; Type: SEQUENCE; Schema: public; Owner: chamcode
--

CREATE SEQUENCE public.submission_submission_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.submission_submission_id_seq OWNER TO chamcode;

--
-- Name: submission_submission_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: chamcode
--

ALTER SEQUENCE public.submission_submission_id_seq OWNED BY public.submission.submission_id;


--
-- Name: testcase; Type: TABLE; Schema: public; Owner: chamcode
--

CREATE TABLE public.testcase (
    testcase_id integer NOT NULL,
    problem_id integer NOT NULL,
    input character varying NOT NULL,
    expected_output character varying NOT NULL,
    is_sample boolean NOT NULL,
    input_type character varying NOT NULL,
    expected_output_type character varying NOT NULL
);


ALTER TABLE public.testcase OWNER TO chamcode;

--
-- Name: testcase_testcase_id_seq; Type: SEQUENCE; Schema: public; Owner: chamcode
--

CREATE SEQUENCE public.testcase_testcase_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.testcase_testcase_id_seq OWNER TO chamcode;

--
-- Name: testcase_testcase_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: chamcode
--

ALTER SEQUENCE public.testcase_testcase_id_seq OWNED BY public.testcase.testcase_id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: chamcode
--

CREATE TABLE public."user" (
    user_id character varying(50) NOT NULL,
    full_name character varying NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying NOT NULL,
    must_change_password boolean NOT NULL,
    role_id integer NOT NULL,
    token_version integer NOT NULL,
    date_of_birth date
);


ALTER TABLE public."user" OWNER TO chamcode;

--
-- Name: enrollment enrollment_id; Type: DEFAULT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.enrollment ALTER COLUMN enrollment_id SET DEFAULT nextval('public.enrollment_enrollment_id_seq'::regclass);


--
-- Name: lesson lesson_id; Type: DEFAULT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.lesson ALTER COLUMN lesson_id SET DEFAULT nextval('public.lesson_lesson_id_seq'::regclass);


--
-- Name: problem problem_id; Type: DEFAULT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.problem ALTER COLUMN problem_id SET DEFAULT nextval('public.problem_problem_id_seq'::regclass);


--
-- Name: submission submission_id; Type: DEFAULT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.submission ALTER COLUMN submission_id SET DEFAULT nextval('public.submission_submission_id_seq'::regclass);


--
-- Name: testcase testcase_id; Type: DEFAULT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.testcase ALTER COLUMN testcase_id SET DEFAULT nextval('public.testcase_testcase_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: chamcode
--

COPY public.alembic_version (version_num) FROM stdin;
7a1c2d3e4f5a
\.


--
-- Data for Name: course; Type: TABLE DATA; Schema: public; Owner: chamcode
--

COPY public.course (course_id, course_name, created_by, term, start_date, end_date, total_number_student) FROM stdin;
\.


--
-- Data for Name: enrollment; Type: TABLE DATA; Schema: public; Owner: chamcode
--

COPY public.enrollment (enrollment_id, course_id, student_id) FROM stdin;
\.


--
-- Data for Name: lesson; Type: TABLE DATA; Schema: public; Owner: chamcode
--

COPY public.lesson (lesson_id, lesson_number, lesson_name, course_id, total_number_assignment, total_number_student_finished, start_date, end_date) FROM stdin;
\.


--
-- Data for Name: problem; Type: TABLE DATA; Schema: public; Owner: chamcode
--

COPY public.problem (problem_id, lesson_id, title, description, time_limit_seconds, start_format_code, constraints, level, hint, complexity, start_datetime, end_datetime, total_number_testcase, report) FROM stdin;
\.


--
-- Data for Name: submission; Type: TABLE DATA; Schema: public; Owner: chamcode
--

COPY public.submission (submission_id, problem_id, student_id, language, submitted_code, status, compile_output, feedback, passed_count, submitted_datetime) FROM stdin;
\.


--
-- Data for Name: testcase; Type: TABLE DATA; Schema: public; Owner: chamcode
--

COPY public.testcase (testcase_id, problem_id, input, expected_output, is_sample, input_type, expected_output_type) FROM stdin;
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: chamcode
--

COPY public."user" (user_id, full_name, email, hashed_password, must_change_password, role_id, token_version, date_of_birth) FROM stdin;
user@example.com	Đinh Nhật Huyền Nhân	user@example.com	$2b$12$OtBzdwDyUrP6oKJkxr.xaufRUHob5635vcdesK/KO4gUXhPXJsv1C	t	3	0	\N
\.


--
-- Name: enrollment_enrollment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: chamcode
--

SELECT pg_catalog.setval('public.enrollment_enrollment_id_seq', 1, false);


--
-- Name: lesson_lesson_id_seq; Type: SEQUENCE SET; Schema: public; Owner: chamcode
--

SELECT pg_catalog.setval('public.lesson_lesson_id_seq', 1, false);


--
-- Name: problem_problem_id_seq; Type: SEQUENCE SET; Schema: public; Owner: chamcode
--

SELECT pg_catalog.setval('public.problem_problem_id_seq', 1, false);


--
-- Name: submission_submission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: chamcode
--

SELECT pg_catalog.setval('public.submission_submission_id_seq', 1, false);


--
-- Name: testcase_testcase_id_seq; Type: SEQUENCE SET; Schema: public; Owner: chamcode
--

SELECT pg_catalog.setval('public.testcase_testcase_id_seq', 1, false);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: course course_pkey; Type: CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.course
    ADD CONSTRAINT course_pkey PRIMARY KEY (course_id);


--
-- Name: enrollment enrollment_pkey; Type: CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.enrollment
    ADD CONSTRAINT enrollment_pkey PRIMARY KEY (enrollment_id);


--
-- Name: lesson lesson_pkey; Type: CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.lesson
    ADD CONSTRAINT lesson_pkey PRIMARY KEY (lesson_id);


--
-- Name: problem problem_pkey; Type: CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.problem
    ADD CONSTRAINT problem_pkey PRIMARY KEY (problem_id);


--
-- Name: submission submission_pkey; Type: CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.submission
    ADD CONSTRAINT submission_pkey PRIMARY KEY (submission_id);


--
-- Name: testcase testcase_pkey; Type: CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.testcase
    ADD CONSTRAINT testcase_pkey PRIMARY KEY (testcase_id);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (user_id);


--
-- Name: ix_user_email; Type: INDEX; Schema: public; Owner: chamcode
--

CREATE UNIQUE INDEX ix_user_email ON public."user" USING btree (email);


--
-- Name: course course_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.course
    ADD CONSTRAINT course_created_by_fkey FOREIGN KEY (created_by) REFERENCES public."user"(user_id);


--
-- Name: enrollment enrollment_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.enrollment
    ADD CONSTRAINT enrollment_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.course(course_id);


--
-- Name: enrollment enrollment_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.enrollment
    ADD CONSTRAINT enrollment_student_id_fkey FOREIGN KEY (student_id) REFERENCES public."user"(user_id);


--
-- Name: lesson lesson_course_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.lesson
    ADD CONSTRAINT lesson_course_id_fkey FOREIGN KEY (course_id) REFERENCES public.course(course_id);


--
-- Name: problem problem_lesson_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.problem
    ADD CONSTRAINT problem_lesson_id_fkey FOREIGN KEY (lesson_id) REFERENCES public.lesson(lesson_id);


--
-- Name: submission submission_problem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.submission
    ADD CONSTRAINT submission_problem_id_fkey FOREIGN KEY (problem_id) REFERENCES public.problem(problem_id);


--
-- Name: submission submission_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.submission
    ADD CONSTRAINT submission_student_id_fkey FOREIGN KEY (student_id) REFERENCES public."user"(user_id);


--
-- Name: testcase testcase_problem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: chamcode
--

ALTER TABLE ONLY public.testcase
    ADD CONSTRAINT testcase_problem_id_fkey FOREIGN KEY (problem_id) REFERENCES public.problem(problem_id);


--
-- PostgreSQL database dump complete
--

\unrestrict 5pQs2HdlAvKpj5RsZOXnCyB5oK4tfHNAigSa2egiNey4vgMI1EXx9dJX3iPTUxM

