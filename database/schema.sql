CREATE TABLE users (
    id PRIMARY KEY,
    gender VARCHAR(20),
    age_range VARCHAR(20),
    handler VARCHAR(100)
);

CREATE TABLE counsellors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    username VARCHAR(50) UNIQUE,
    password VARCHAR(255),
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    channels VARCHAR(255),
    current_ticket VARCHAR REFERENCES tickets(id)
);

CREATE TABLE tickets (
    id PRIMARY KEY,
    status VARCHAR(50),
    handler VARCHAR(100),
    user INTEGER REFERENCES users(id),
    transcript TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);

CREATE TABLE tickets_assignment (
    counsellor_id INTEGER REFERENCES counsellors(id),
    ticket_id VARCHAR REFERENCES tickets(id),
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (counsellor_id, ticket_id)
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    _from VARCHAR(100),
    _to VARCHAR(100),
    _type VARCHAR(50),
    source VARCHAR(100),
    content TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE channels(
    counsellor_id INTEGER REFERENCES counsellors(id),
    channel VARCHAR(100),
    channel_id VARCHAR(100),
    order_priority INT,
    PRIMARY KEY (counsellor_id, channel)
)