--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: routeid_dirtag; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE routeid_dirtag (
    route_id text,
    dirtag text
);


--
-- Name: shape_dirtag; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE shape_dirtag (
    shape_id text,
    dirtag text
);


--
-- Data for Name: routeid_dirtag; Type: TABLE DATA; Schema: public; Owner: -
--

COPY routeid_dirtag (route_id, dirtag) FROM stdin;
3868	38_IB1
3868	38_IB2
3868	38_IB3
3868	38_OB1
3868	38_OB2
3868	38_OB3
3868	38_OB4
3868	38_OB5
3669	01_IB02
3669	01_IB03
3669	01_IB04
3669	01_IB05
3669	01_IB06
3669	01_IB07
3669	01_IB08
3669	01_IB09
3669	01_IB10
3669	01_IB11
3669	01_OB01
3669	01_OB02
3669	01_OB04
3669	01_OB05
3669	01_OB06
3669	01_OB09
3669	01_OB10
3669	01_OB11
3669	01_OB13
3669	01_OB14
3693	36_IB1
3693	36_IB2
3693	36_OB1
3693	36_OB2
3679	18_IB1
3679	18_OB1
\.


--
-- Data for Name: shape_dirtag; Type: TABLE DATA; Schema: public; Owner: -
--

COPY shape_dirtag (shape_id, dirtag) FROM stdin;
34398	18_IB1
34397	18_OB1
34404	19_IB2
34400	19_OB2
34403	19_IB1
34399	19_OB1
\.


--
-- Name: shape_id_uniq; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE UNIQUE INDEX shape_id_uniq ON shape_dirtag USING btree (shape_id);


--
-- PostgreSQL database dump complete
--

