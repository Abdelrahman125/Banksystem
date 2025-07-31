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
    #cusromer
    print(encrypt_md5("malek2020"))
    print(encrypt_md5("nour12"))
    print(encrypt_md5("terminator2020"))
    print(encrypt_md5("sasa2020"))
    print(encrypt_md5("bedo2006"))



# employee
print(encrypt_md5("jana2020"))
print(encrypt_md5("fawzy2020"))












