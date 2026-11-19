# Membership database features

- `members.phone` is unique, so MySQL creates an index used by exact phone lookups.
- `members.card_code` has the unique `ix_members_card_code` index for QR lookups.
- Database startup adds `card_code` to an existing `members` table and fills codes
  for existing members.
- Startup creates `sp_get_valid_subscription_for_checkin` and the daily
  `ev_expire_subscriptions_daily` event. The procedure returns a subscription ID
  only when its status is `ACTIVE` and its start/end dates include today.
- MySQL's event scheduler must be enabled for expired subscriptions to be updated
  daily. Startup tries to enable it; the MySQL account needs permission to change
  the global setting. Otherwise, enable it as a database administrator:

  ```sql
  SET GLOBAL event_scheduler = ON;
  ```

`find_member_by_phone_or_qr` uses exact matching so both member indexes can be
used by the database.

## Sample data

The SQLAlchemy metadata currently registers 14 tables. From the `backend`
directory, run `python -m app.db.seed` to create the tables and seed all of them.
For MySQL, the command prompts for the database password without echoing it;
press Enter to use `DATABASE_URL` from the environment or `.env`:

- 5 plans, 20 members, 10 equipment items, 3 trainers, and 2 test accounts
- 20 subscriptions and invoices, 15 successful payments
- 9 trainer schedules and bookings, 20 trainer assignments, and 9 attendance records
- 8 feedback records, 5 notifications, and 5 audit logs

The seed uses stable natural keys and only inserts missing records, so it can be
run repeatedly without duplicating sample rows.

Test accounts:

- Admin: `admin` / `Admin123`
- Receptionist: `le_tan` / `Receptionist123`
- Seeded trainers: each account uses `Trainer123` (usernames start with `pt_`)
