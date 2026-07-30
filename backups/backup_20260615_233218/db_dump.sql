--
-- PostgreSQL database dump
--

\restrict FZmOgvYTJwao9Gc58oj14NN4CXxEUb12COfW0eaTInAdYnl8Z8UvNV9TaSBodjh

-- Dumped from database version 15.18
-- Dumped by pg_dump version 15.18

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
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
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: drkhare
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO drkhare;

--
-- Name: analytics; Type: TABLE; Schema: public; Owner: drkhare
--

CREATE TABLE public.analytics (
    id integer NOT NULL,
    event_type character varying(100),
    event_data json,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.analytics OWNER TO drkhare;

--
-- Name: analytics_id_seq; Type: SEQUENCE; Schema: public; Owner: drkhare
--

CREATE SEQUENCE public.analytics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.analytics_id_seq OWNER TO drkhare;

--
-- Name: analytics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drkhare
--

ALTER SEQUENCE public.analytics_id_seq OWNED BY public.analytics.id;


--
-- Name: chat_history; Type: TABLE; Schema: public; Owner: drkhare
--

CREATE TABLE public.chat_history (
    id integer NOT NULL,
    user_id integer,
    session_id character varying(64) NOT NULL,
    role character varying(20) NOT NULL,
    message text NOT NULL,
    sources json,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.chat_history OWNER TO drkhare;

--
-- Name: chat_history_id_seq; Type: SEQUENCE; Schema: public; Owner: drkhare
--

CREATE SEQUENCE public.chat_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.chat_history_id_seq OWNER TO drkhare;

--
-- Name: chat_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drkhare
--

ALTER SEQUENCE public.chat_history_id_seq OWNED BY public.chat_history.id;


--
-- Name: documents; Type: TABLE; Schema: public; Owner: drkhare
--

CREATE TABLE public.documents (
    id integer NOT NULL,
    filename character varying(512) NOT NULL,
    filepath character varying(1024) NOT NULL,
    filetype character varying(32) NOT NULL,
    status character varying(32),
    processing_stage character varying(64),
    chunks_count integer,
    error_message text,
    uploaded_by_id integer,
    upload_date timestamp with time zone DEFAULT now()
);


ALTER TABLE public.documents OWNER TO drkhare;

--
-- Name: documents_id_seq; Type: SEQUENCE; Schema: public; Owner: drkhare
--

CREATE SEQUENCE public.documents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.documents_id_seq OWNER TO drkhare;

--
-- Name: documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drkhare
--

ALTER SEQUENCE public.documents_id_seq OWNED BY public.documents.id;


--
-- Name: knowledge_entries; Type: TABLE; Schema: public; Owner: drkhare
--

CREATE TABLE public.knowledge_entries (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    category character varying(100),
    content text NOT NULL,
    source_document_id integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.knowledge_entries OWNER TO drkhare;

--
-- Name: knowledge_entries_id_seq; Type: SEQUENCE; Schema: public; Owner: drkhare
--

CREATE SEQUENCE public.knowledge_entries_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.knowledge_entries_id_seq OWNER TO drkhare;

--
-- Name: knowledge_entries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drkhare
--

ALTER SEQUENCE public.knowledge_entries_id_seq OWNED BY public.knowledge_entries.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: drkhare
--

CREATE TABLE public.roles (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    permissions json
);


ALTER TABLE public.roles OWNER TO drkhare;

--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: drkhare
--

CREATE SEQUENCE public.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.roles_id_seq OWNER TO drkhare;

--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drkhare
--

ALTER SEQUENCE public.roles_id_seq OWNED BY public.roles.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: drkhare
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role_id integer NOT NULL,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.users OWNER TO drkhare;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: drkhare
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO drkhare;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: drkhare
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: analytics id; Type: DEFAULT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.analytics ALTER COLUMN id SET DEFAULT nextval('public.analytics_id_seq'::regclass);


--
-- Name: chat_history id; Type: DEFAULT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.chat_history ALTER COLUMN id SET DEFAULT nextval('public.chat_history_id_seq'::regclass);


--
-- Name: documents id; Type: DEFAULT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.documents ALTER COLUMN id SET DEFAULT nextval('public.documents_id_seq'::regclass);


--
-- Name: knowledge_entries id; Type: DEFAULT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.knowledge_entries ALTER COLUMN id SET DEFAULT nextval('public.knowledge_entries_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.roles ALTER COLUMN id SET DEFAULT nextval('public.roles_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: drkhare
--

COPY public.alembic_version (version_num) FROM stdin;
3b73958c3b9f
\.


--
-- Data for Name: analytics; Type: TABLE DATA; Schema: public; Owner: drkhare
--

COPY public.analytics (id, event_type, event_data, created_at) FROM stdin;
1	intent_matched	{"intent": "Knowledge Question", "session_id": "4e236597-5fd0-47c5-b683-b686116439df"}	2026-06-15 18:01:18.179604+00
2	intent_matched	{"intent": "Knowledge Question", "session_id": "82712566-d5ac-43c4-9513-f32cefb94fbf"}	2026-06-15 18:01:18.907663+00
3	intent_matched	{"intent": "Knowledge Question", "session_id": "66b162cc-9729-4960-abb1-2e1c139f2e6c"}	2026-06-15 18:01:19.612776+00
\.


--
-- Data for Name: chat_history; Type: TABLE DATA; Schema: public; Owner: drkhare
--

COPY public.chat_history (id, user_id, session_id, role, message, sources, created_at) FROM stdin;
1	\N	4e236597-5fd0-47c5-b683-b686116439df	user	What is the capital of France? (Audit Test)	[]	2026-06-15 18:01:18.172687+00
2	\N	4e236597-5fd0-47c5-b683-b686116439df	assistant	I could not find verified information about this topic in Dr. Khare's available documents. You may discuss it with him during your next meeting.	{"citations": [{"filename": "knowledge_boundaries.txt", "document": "knowledge_boundaries.txt", "score": 0.0887, "chunk_preview": "# Explicit Knowledge Boundaries\\n\\nThe following information is NOT present in the verified source documents and is marked as strictly unavailable. \\nUnless future verified evidence is explicitly provide"}, {"filename": "publications.txt", "document": "publications.txt", "score": 0.0778, "chunk_preview": "# PUBLICATIONS\\n\\nPublications \\n \\nPeer Reviewed Journal Articles/Abstracts \\n \\nKhare S, Khare S, Seth D. Pseudodementia: An Artefact or a Grey Area of Geropsychiatry?. \\nInternational Journal of Research."}, {"filename": "certifications.txt", "document": "certifications.txt", "score": 0.0777, "chunk_preview": "CV \\n \\ncoursera.org/verif y/E4F6AC7ERXBZ \\n \\nAppendix 44 \\nDecentralized Finance (DeFi) Primitives \\nDuke University \\nAug 9, 2022 \\nhttps://coursera.org/verif y/8CZPG73H2G37 \\n \\nAppendix 45 \\nDFSS for the 6 "}, {"filename": "certifications.txt", "document": "certifications.txt", "score": 0.0774, "chunk_preview": "CV \\n \\nUniversity of Pennsylvania \\nAugust 3, 2022 \\ncoursera.org/verif y/4WLCCLV8SJUH \\n \\nAppendix 37 \\nSocial Entrepreneurship \\nUniversity of Pennsylvania \\nAug 4, 2022 \\ncoursera.org/verif y/TQJ5HLAA4AEM "}, {"filename": "awards.txt", "document": "awards.txt", "score": 0.0719, "chunk_preview": "CV \\n \\nSix Sigma Tools for Define and Measure \\nUniversity System of Georgia \\nJuly 12, 2022 \\nhttps://coursera.org/verif y/MTCNBUTTQENW \\n \\nAppendix 08 \\nSix Sigma Principles \\nUniversity System of Georgia "}], "answer_source": "System (Hard Grounding)", "confidence": 0.0887087453081912, "response_time_ms": 710, "model": "bypass", "bypassed_llm": true}	2026-06-15 18:01:18.187722+00
3	\N	82712566-d5ac-43c4-9513-f32cefb94fbf	user	What is the capital of France? (Audit Test)	[]	2026-06-15 18:01:18.902641+00
4	\N	82712566-d5ac-43c4-9513-f32cefb94fbf	assistant	I could not find verified information about this topic in Dr. Khare's available documents. You may discuss it with him during your next meeting.	{"citations": [{"filename": "knowledge_boundaries.txt", "document": "knowledge_boundaries.txt", "score": 0.0887, "chunk_preview": "# Explicit Knowledge Boundaries\\n\\nThe following information is NOT present in the verified source documents and is marked as strictly unavailable. \\nUnless future verified evidence is explicitly provide"}, {"filename": "publications.txt", "document": "publications.txt", "score": 0.0778, "chunk_preview": "# PUBLICATIONS\\n\\nPublications \\n \\nPeer Reviewed Journal Articles/Abstracts \\n \\nKhare S, Khare S, Seth D. Pseudodementia: An Artefact or a Grey Area of Geropsychiatry?. \\nInternational Journal of Research."}, {"filename": "certifications.txt", "document": "certifications.txt", "score": 0.0777, "chunk_preview": "CV \\n \\ncoursera.org/verif y/E4F6AC7ERXBZ \\n \\nAppendix 44 \\nDecentralized Finance (DeFi) Primitives \\nDuke University \\nAug 9, 2022 \\nhttps://coursera.org/verif y/8CZPG73H2G37 \\n \\nAppendix 45 \\nDFSS for the 6 "}, {"filename": "certifications.txt", "document": "certifications.txt", "score": 0.0774, "chunk_preview": "CV \\n \\nUniversity of Pennsylvania \\nAugust 3, 2022 \\ncoursera.org/verif y/4WLCCLV8SJUH \\n \\nAppendix 37 \\nSocial Entrepreneurship \\nUniversity of Pennsylvania \\nAug 4, 2022 \\ncoursera.org/verif y/TQJ5HLAA4AEM "}, {"filename": "awards.txt", "document": "awards.txt", "score": 0.0719, "chunk_preview": "CV \\n \\nSix Sigma Tools for Define and Measure \\nUniversity System of Georgia \\nJuly 12, 2022 \\nhttps://coursera.org/verif y/MTCNBUTTQENW \\n \\nAppendix 08 \\nSix Sigma Principles \\nUniversity System of Georgia "}], "answer_source": "System (Hard Grounding)", "confidence": 0.0887087453081912, "response_time_ms": 685, "model": "bypass", "bypassed_llm": true}	2026-06-15 18:01:18.914224+00
5	\N	66b162cc-9729-4960-abb1-2e1c139f2e6c	user	Spam 0	[]	2026-06-15 18:01:19.606592+00
\.


--
-- Data for Name: documents; Type: TABLE DATA; Schema: public; Owner: drkhare
--

COPY public.documents (id, filename, filepath, filetype, status, processing_stage, chunks_count, error_message, uploaded_by_id, upload_date) FROM stdin;
\.


--
-- Data for Name: knowledge_entries; Type: TABLE DATA; Schema: public; Owner: drkhare
--

COPY public.knowledge_entries (id, title, category, content, source_document_id, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: drkhare
--

COPY public.roles (id, name, permissions) FROM stdin;
1	admin	"*"
2	user	"chat"
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: drkhare
--

COPY public.users (id, email, password_hash, role_id, is_active, created_at) FROM stdin;
1	admin@drkhare.com	$2b$12$2wzKhJpX7TpVT2dxne35JOS11MQFt43QJbW.0Mfzhm0556SJ2NotS	1	t	2026-06-15 17:58:43.114019+00
\.


--
-- Name: analytics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drkhare
--

SELECT pg_catalog.setval('public.analytics_id_seq', 3, true);


--
-- Name: chat_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drkhare
--

SELECT pg_catalog.setval('public.chat_history_id_seq', 5, true);


--
-- Name: documents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drkhare
--

SELECT pg_catalog.setval('public.documents_id_seq', 1, false);


--
-- Name: knowledge_entries_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drkhare
--

SELECT pg_catalog.setval('public.knowledge_entries_id_seq', 1, false);


--
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drkhare
--

SELECT pg_catalog.setval('public.roles_id_seq', 2, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: drkhare
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: analytics analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.analytics
    ADD CONSTRAINT analytics_pkey PRIMARY KEY (id);


--
-- Name: chat_history chat_history_pkey; Type: CONSTRAINT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.chat_history
    ADD CONSTRAINT chat_history_pkey PRIMARY KEY (id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- Name: knowledge_entries knowledge_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.knowledge_entries
    ADD CONSTRAINT knowledge_entries_pkey PRIMARY KEY (id);


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_chat_history_id; Type: INDEX; Schema: public; Owner: drkhare
--

CREATE INDEX ix_chat_history_id ON public.chat_history USING btree (id);


--
-- Name: ix_chat_history_session_id; Type: INDEX; Schema: public; Owner: drkhare
--

CREATE INDEX ix_chat_history_session_id ON public.chat_history USING btree (session_id);


--
-- Name: ix_documents_id; Type: INDEX; Schema: public; Owner: drkhare
--

CREATE INDEX ix_documents_id ON public.documents USING btree (id);


--
-- Name: ix_knowledge_entries_id; Type: INDEX; Schema: public; Owner: drkhare
--

CREATE INDEX ix_knowledge_entries_id ON public.knowledge_entries USING btree (id);


--
-- Name: ix_roles_id; Type: INDEX; Schema: public; Owner: drkhare
--

CREATE INDEX ix_roles_id ON public.roles USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: drkhare
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: drkhare
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: chat_history chat_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.chat_history
    ADD CONSTRAINT chat_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: documents documents_uploaded_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_uploaded_by_id_fkey FOREIGN KEY (uploaded_by_id) REFERENCES public.users(id);


--
-- Name: knowledge_entries knowledge_entries_source_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.knowledge_entries
    ADD CONSTRAINT knowledge_entries_source_document_id_fkey FOREIGN KEY (source_document_id) REFERENCES public.documents(id);


--
-- Name: users users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: drkhare
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- PostgreSQL database dump complete
--

\unrestrict FZmOgvYTJwao9Gc58oj14NN4CXxEUb12COfW0eaTInAdYnl8Z8UvNV9TaSBodjh

