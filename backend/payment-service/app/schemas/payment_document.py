# MongoDB Document Schema — payments collection
#
# {
#   "_id":          ObjectId,
#   "account_id":   str,
#   "email":        str,
#   "student_id":   str,
#   "student_name": str,
#   "amount":       float,
#   "status":       str  ("PENDING" | "SUCCESS" | "FAILED"),
#   "error_code":   str | None,
#   "created_at":   datetime,
#   "completed_at": datetime | None
# }
