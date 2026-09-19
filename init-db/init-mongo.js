// =============================================================================
// MongoDB Init Seed Script
// Auto-runs once on first container startup via /docker-entrypoint-initdb.d/
// =============================================================================
//
// Test credentials  (password verified against bcrypt hash below):
//   username: sv.nguyen   password: Test@123    balance:  7,500,000 VND
//   username: sv.tran     password: Test@123    balance:  2,300,000 VND
//   username: sv.le       password: Ibank@456   balance: 12,000,000 VND
//
// MSSV mapping (account → student):
//   sv.nguyen → 521H0001
//   sv.tran   → 521H0002
//   sv.le     → 521H0003
// =============================================================================

// ── account_db ────────────────────────────────────────────────────────────────
db = db.getSiblingDB("account_db");

db.accounts.drop();
db.accounts.createIndex({ username: 1 }, { unique: true });

db.accounts.insertMany([
  {
    username:      "sv.nguyen",
    // bcrypt(cost=12) of "Test@123"
    password_hash: "$2b$12$kEJGg8fVLyvUhWg2zsBY1ejZ.KFf1oRRPgrbTgOJmwUye9/50vcUi",
    full_name:     "Nguyen Van An",
    email:         "nguyen.van.an@student.tdtu.edu.vn",
    phone:         "0901234567",
    balance:       7500000,
    created_at:    new Date()
  },
  {
    username:      "sv.tran",
    // bcrypt(cost=12) of "Test@123"
    password_hash: "$2b$12$kEJGg8fVLyvUhWg2zsBY1ejZ.KFf1oRRPgrbTgOJmwUye9/50vcUi",
    full_name:     "Tran Thi Bao",
    email:         "tran.thi.bao@student.tdtu.edu.vn",
    phone:         "0912345678",
    balance:       2300000,
    created_at:    new Date()
  },
  {
    username:      "sv.le",
    // bcrypt(cost=12) of "Ibank@456"
    password_hash: "$2b$12$9FoyHF0vwXN4C1PGu/YQCuNZowPWs5DzatcZuvm2VOZ7pMSjMG5BC",
    full_name:     "Le Hoang Cuong",
    email:         "le.hoang.cuong@student.tdtu.edu.vn",
    phone:         "0923456789",
    balance:       12000000,
    created_at:    new Date()
  }
]);

print("account_db: " + db.accounts.countDocuments() + " accounts inserted.");

// ── tuition_db ────────────────────────────────────────────────────────────────
db = db.getSiblingDB("tuition_db");

db.tuitions.drop();
db.tuitions.createIndex({ student_id: 1 }, { unique: true });

db.tuitions.insertMany([
  {
    student_id:     "521H0001",
    student_name:   "Nguyen Van An",
    major:          "Cong nghe Thong tin",
    semester:       "HK1/2024-2025",
    amount:         4850000,
    status:         "UNPAID",
    paid_at:        null,
    paid_by:        null,
    transaction_id: null,
    created_at:     new Date()
  },
  {
    student_id:     "521H0002",
    student_name:   "Tran Thi Bao",
    major:          "Ke toan",
    semester:       "HK1/2024-2025",
    amount:         3620000,
    status:         "UNPAID",
    paid_at:        null,
    paid_by:        null,
    transaction_id: null,
    created_at:     new Date()
  },
  {
    student_id:     "521H0003",
    student_name:   "Le Hoang Cuong",
    major:          "Ky thuat Dien tu",
    semester:       "HK1/2024-2025",
    amount:         5130000,
    status:         "UNPAID",
    paid_at:        null,
    paid_by:        null,
    transaction_id: null,
    created_at:     new Date()
  },
  {
    student_id:     "522H0017",
    student_name:   "Pham Duc Dung",
    major:          "Quan tri Kinh doanh",
    semester:       "HK1/2024-2025",
    amount:         3975000,
    status:         "UNPAID",
    paid_at:        null,
    paid_by:        null,
    transaction_id: null,
    created_at:     new Date()
  },
  {
    student_id:     "522H0041",
    student_name:   "Hoang Thi Yen",
    major:          "Ngon ngu Anh",
    semester:       "HK1/2024-2025",
    amount:         3280000,
    status:         "UNPAID",
    paid_at:        null,
    paid_by:        null,
    transaction_id: null,
    created_at:     new Date()
  },
  {
    student_id:     "523H0089",
    student_name:   "Vo Minh Khoa",
    major:          "Cong nghe Thong tin",
    semester:       "HK1/2024-2025",
    amount:         4720000,
    status:         "UNPAID",
    paid_at:        null,
    paid_by:        null,
    transaction_id: null,
    created_at:     new Date()
  }
]);

print("tuition_db: " + db.tuitions.countDocuments() + " tuition records inserted.");

// ── payment_db ────────────────────────────────────────────────────────────────
db = db.getSiblingDB("payment_db");
db.createCollection("payments");
print("payment_db: collection payments ready.");

// ── notification_db ───────────────────────────────────────────────────────────
db = db.getSiblingDB("notification_db");
db.createCollection("otps");
db.otps.createIndex({ payment_id: 1 });
// TTL index: MongoDB auto-deletes expired OTP documents
db.otps.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 });
print("notification_db: otps ready (TTL index on expires_at).");

print("\n=== Seed complete ===");
