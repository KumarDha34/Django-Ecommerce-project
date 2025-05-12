import hashlib
import hmac

def generate_signature(secret_key, amt, txnid, scd):
    # String to be signed
    data = f"{amt}|{txnid}|{scd}"
    
    # Generate the signature using HMAC-SHA256
    signature = hmac.new(secret_key.encode(), data.encode(), hashlib.sha256).hexdigest()
    
    return signature