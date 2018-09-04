import phe.paillier as paillier, math, random
pubkey, prikey = paillier.generate_paillier_keypair(n_length=1024)

print(str(prikey.decrypt(pubkey.encrypt(1) - pubkey.encrypt(2))))

def extractExponent(input):
    return pubkey.encrypt(input).exponent
def extractExponent2a(input):
    return (pubkey.encrypt(input) + pubkey.encrypt(math.pow(10,1))).exponent
def extractExponent2b(input):
    return (pubkey.encrypt(input) + pubkey.encrypt(math.pow(10,-100))).exponent


print("value,unencrypted_exponent, unencrypted_exponent after adjustment")
for i in range(0, 100):
    i = 100 - i
    value = math.pow(10,i) * random.random()
    print(str(value)+","+ str(extractExponent(value))+","+str(extractExponent2a(value)))
for i in range(0, 100):
    value = math.pow(10,-i) * random.random()
    print(str(value)+","+str(extractExponent(value))+","+str(extractExponent2b(value)))


