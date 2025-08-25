-- Create database
create extension if not exists "pgcrypto";

-- USERS
create table users (
  id uuid primary key default gen_random_uuid (),
  name text not null,
  email text unique not null,
  created_at timestamp default now()
);

-- EVENTS
create table events (
  id uuid primary key default gen_random_uuid (),
  title text not null,
  description text,
  date date not null,
  city text,
  created_by uuid not null references users (id) on delete cascade
);

-- RSVPs
create table rsvps (
  id uuid primary key default gen_random_uuid (),
  user_id uuid not null references users (id) on delete cascade,
  event_id uuid not null references events (id) on delete cascade,
  status text check (status in ('Yes', 'No', 'Maybe')),
  unique (user_id, event_id) -- prevent duplication RSVP per user per event
);


-- USERS
INSERT INTO users (id, name, email, created_at) VALUES
  (gen_random_uuid(), 'Alice Johnson', 'alice@example.com', NOW()),
  (gen_random_uuid(), 'Bob Smith', 'bob@example.com', NOW()),
  (gen_random_uuid(), 'Charlie Brown', 'charlie@example.com', NOW()),
  (gen_random_uuid(), 'Diana Prince', 'diana@example.com', NOW()),
  (gen_random_uuid(), 'Ethan Hunt', 'ethan@example.com', NOW()),
  (gen_random_uuid(), 'Fiona Clark', 'fiona@example.com', NOW()),
  (gen_random_uuid(), 'George Miller', 'george@example.com', NOW()),
  (gen_random_uuid(), 'Hannah Lee', 'hannah@example.com', NOW()),
  (gen_random_uuid(), 'Ivan Torres', 'ivan@example.com', NOW()),
  (gen_random_uuid(), 'Julia Adams', 'julia@example.com', NOW());


-- events
-- Replace with actual UUIDs from Users table
INSERT INTO events (title, description, date, city, created_by) VALUES
  ('Tech Meetup', 'Monthly tech meetup in Delhi', '2025-08-30', 'Delhi', (SELECT id FROM users LIMIT 1)),
  ('Startup Pitch Night', 'Pitch your startup to investors', '2025-09-05', 'Bangalore', (SELECT id FROM users OFFSET 1 LIMIT 1)),
  ('AI Conference', 'Discuss the latest in AI research', '2025-09-10', 'Hyderabad', (SELECT id FROM users OFFSET 2 LIMIT 1)),
  ('Music Festival', 'Live music and food festival', '2025-09-15', 'Goa', (SELECT id FROM users OFFSET 3 LIMIT 1)),
  ('Job Fair', 'Meet top recruiters and apply for jobs', '2025-09-20', 'Mumbai', (SELECT id FROM users OFFSET 4 LIMIT 1));

-- rsvps
INSERT INTO rsvps (user_id, event_id, status)
SELECT u.id, e.id, (ARRAY['Yes','No','Maybe'])[floor(random()*3+1)]
FROM users u, events e
LIMIT 20;
