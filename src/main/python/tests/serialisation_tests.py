import phe.paillier as paillier, math, pickle, binascii
pubkey, prikey = paillier.generate_paillier_keypair(n_length=1024)
text = binascii.b2a_hex(pickle.dumps(pubkey)).decode('ascii')
print(text)
binary = binascii.a2b_hex(text.encode('ascii'))
pubkey = pickle.loads(binary)
encrypted = pubkey.encrypt(math.pi)
pickledEncrypted = binascii.b2a_base64(pickle.dumps(encrypted))
encrypted2 = pickle.loads(binascii.a2b_base64(pickledEncrypted))
decrypted = prikey.decrypt(encrypted)

print(type(decrypted))
print(decrypted)
