"""
Utility: generate bcrypt hashes for seed passwords.
Run once to regenerate hashes in init-mongo.js if needed.

Usage:
    pip install passlib[bcrypt]
    python init-db/gen-hash.py
"""
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

passwords = {
    "Test@123":  "sv.nguyen, sv.tran",
    "Ibank@456": "sv.le",
}

print("Copy these hashes into init-mongo.js:\n")
for plain, accounts in passwords.items():
    h = pwd.hash(plain)
    print(f"  password: {plain!r}  →  accounts: {accounts}")
    print(f"  hash:     {h}\n")
