// Runs once, on first start of an empty data volume, as the root user.
// Creates least-privilege users instead of letting apps use the root account.
const mantis = db.getSiblingDB("mantis");

// The scanner reads and writes scan data.
mantis.createUser({
  user: process.env.MANTIS_DB_USER,
  pwd: process.env.MANTIS_DB_PASSWORD,
  roles: [{ role: "readWrite", db: "mantis" }],
});

// The UI only ever reads, so give it the read role — even a bug or an
// injection in the dashboard cannot modify or drop scan data.
mantis.createUser({
  user: process.env.MANTIS_UI_USER,
  pwd: process.env.MANTIS_UI_PASSWORD,
  roles: [{ role: "read", db: "mantis" }],
});
