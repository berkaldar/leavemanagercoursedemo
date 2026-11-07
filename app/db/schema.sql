CREATE TABLE IF NOT EXISTS people (
    id         TEXT PRIMARY KEY,
    full_name  TEXT NOT NULL,
    manager_id TEXT REFERENCES people (id)
);

CREATE TABLE IF NOT EXISTS leave_requests (
    id          TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL REFERENCES people (id),
    leave_type  TEXT NOT NULL CHECK (leave_type IN ('Annual', 'Unpaid')),
    start_date  TEXT NOT NULL,
    end_date    TEXT NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('Pending', 'Approved', 'Rejected', 'Cancelled')),
    created_at  TEXT NOT NULL
);
