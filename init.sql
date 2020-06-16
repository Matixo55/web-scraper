GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
CREATE SEQUENCE id_seq;
CREATE TABLE IF NOT EXISTS Requests
(
id INT NOT NULL DEFAULT NEXTVAL('id_seq'),
url TEXT NOT NULL,
status TEXT,
website_text TEXT,
pictures TEXT[]
);