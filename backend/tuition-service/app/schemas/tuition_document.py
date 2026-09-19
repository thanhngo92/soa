# MongoDB Document Schema — tuitions collection
#
# {
#   "_id":            ObjectId,
#   "student_id":     str  (unique index, MSSV),
#   "student_name":   str,
#   "major":          str,
#   "semester":       str,
#   "amount":         float,
#   "status":         str  ("UNPAID" | "PAID"),
#   "paid_at":        datetime | None,
#   "paid_by":        str | None,
#   "transaction_id": str | None,
#   "created_at":     datetime
# }
