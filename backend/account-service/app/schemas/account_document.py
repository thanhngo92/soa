# MongoDB Document Schema — accounts collection
#
# {
#   "_id":           ObjectId,
#   "username":      str  (unique index),
#   "password_hash": str,
#   "full_name":     str,
#   "email":         str,
#   "phone":         str,
#   "balance":       float (>= 0),
#   "created_at":    datetime
# }
