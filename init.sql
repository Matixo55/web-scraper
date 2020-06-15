GRANT ALL PRIVILEGES ON DATABASE postgres TO postgres;
CREATE TABLE IF NOT EXISTS Requests
(
id integer,
url text,
status text,
website_text text,
pictures text[]
);
ALTER TABLE Requests
ADD PRIMARY KEY (id);