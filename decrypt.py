import hashlib

# decrypt hashlib.sha256 using a known secret key
def decrypt_sha256(hashed_password, secret_key):
    hash = hashlib.sha256()
    hash.update(secret_key.encode('utf-8'))
    return hash.hexdigest() == hashed_password

def encrypt_md5(plain_text):
    hash = hashlib.md5()
    hash.update(plain_text.encode('utf-8'))
    return hash.hexdigest()

if __name__ == "__main__":
    # Example usage
    secret_key = "mysecret"
    hashed = hashlib.sha256(secret_key.encode('utf-8')).hexdigest()
    print("Decryption result:", decrypt_sha256(hashed, secret_key))
    print("MD5 encryption:", encrypt_md5("example"))
    












