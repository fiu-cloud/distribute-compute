import math
import phe.paillier as paillier
pubkey, prikey = paillier.generate_paillier_keypair(n_length=1024)

# when iterations more than 17 (key length 1024) irrational test intermittently fails. Result either incorrect (random) or overflow
iterations = 17

# factorial test
factorial = pubkey.encrypt(1)
for x in range(1,iterations+1):
    factorial = factorial * x
print("Factorial test ok "+ str(math.factorial(iterations) == prikey.decrypt(factorial)))

# irrational test:  pi * 1/pi * pi * 1/pi...
piEnc = pubkey.encrypt(math.pi)
for x in range(0,iterations):
    if x % 2 == 0:
        piEnc = piEnc * 1/math.pi
    else:
        piEnc = piEnc * math.pi

if iterations % 2 == 0:
    print("Irrational test ok "+ str(math.fabs(math.pi - prikey.decrypt(piEnc)) < 0.0001))
else:
    print("Irrational test ok "+ str(math.fabs(1 - prikey.decrypt(piEnc)) < 0.0001))


