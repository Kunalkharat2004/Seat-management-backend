from app.core.security import *

pwd = hash_password("Password123")
print(verify_password("Password12", pwd))

token = generate_secure_token()
print(hash_token(token))