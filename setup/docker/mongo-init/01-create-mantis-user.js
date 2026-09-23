// Runs once, on first start of an empty data volume, as the root user.
// Creates a least-privilege user that Mantis and the dashboard use instead of root.
db.getSiblingDB("mantis").createUser({
  user: process.env.MANTIS_DB_USER,
  pwd: process.env.MANTIS_DB_PASSWORD,
  roles: [{ role: "readWrite", db: "mantis" }],
});
