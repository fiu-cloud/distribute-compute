import phe.paillier as paillier, numpy as np,sys, math, random
import compute.gpdb_io as io
import compute.serialisation as ser
party = sys.argv[1]
_s3_endpoint = sys.argv[2]
_s3_bucket = sys.argv[3]
_host = sys.argv[4]
_database = sys.argv[5]
_user = sys.argv[6]
_password = sys.argv[7]
_s3_finished = "_finished_"

io.init(_host,_database,_user,_password,_s3_endpoint, _s3_bucket)

# start experiment parameters (set these in the code as need to be shared by all parties)
alpha = 0.1
iterations = 10
dataset_size = 20
# finish experiment parameters

# write the thetas to a local store
thetas = open("thetas.log", "a",1)

def main():
    # generate synthetic data & initialise variables
    init = np.linspace(-5, 5, math.sqrt(dataset_size))
    x1, x2 = np.meshgrid(init, init)
    np.random.seed(1)
    y = 31*x1 - 5.5*x2 + np.random.normal(size=x1.shape)
    x1 = x1.flatten()
    x2 = x2.flatten()
    y = y.flatten()
    n = float(len(x1))
    x1_theta = random.random() * max(x1)
    x2_theta = random.random() * max(x2)

    # initialise
    if party == "y":
        x1 = []
        x2 = []
        pubkey, prikey = paillier.generate_paillier_keypair(n_length=1024)
        key = ser.serialisePubKey(pubkey)
        io.write([[key]], "pubkey/", "key text",-1)
    elif party == "x1":
        y = []
        x2 = []
        pubkey = ser.deserialisePubKey((io.read("pubkey/", "key text",-1))[0][0])
    elif party == "x2":
        y = []
        x1 = []
        pubkey = ser.deserialisePubKey((io.read("pubkey/", "key text",-1))[0][0])

    # gradient descent
    for i in range(0, iterations):
        if party == "x1":
            x1_prediction = x1 * x1_theta
            x1_prediction_encrypted = [[ser.serialiseEncrypted(pubkey.encrypt(x))] for x in x1_prediction]
            io.write(x1_prediction_encrypted,"x1/"+str(i)+"/","x1_prediction text",i)
            g1 = io.read("gradient/"+str(i)+"/","gradient float",i)
            x1_gradient = [a[0]*b for a,b in zip(g1,x1)]
            x1_diff = sum(x1_gradient)
            x1_theta = x1_theta - (alpha / n) * x1_diff
            thetas.write("x1 "+ str(x1_theta) + "["+str(x1_diff)+"]\r\n")
        elif party == "x2":
            x1_prediction_serialised = io.read("x1/"+str(i)+"/","x1_prediction text",i)
            x1_prediction = [ser.deserialiseEncrypted(pubkey,x[0]) for x in x1_prediction_serialised]
            x2_prediction = x1_prediction + x2 * x2_theta
            x2_prediction_encrypted = [[ser.serialiseEncrypted(x)] for x in x2_prediction]
            io.write(x2_prediction_encrypted,"x2/"+str(i)+"/","x2_prediction text",i)
            g2 = io.read("gradient/"+str(i)+"/","gradient float",i)
            x2_gradient = [a[0]*b for a,b in zip(g2,x2)]
            x2_diff = sum(x2_gradient)
            x2_theta = x2_theta - (alpha / n) * x2_diff
            thetas.write("x2 "+ str(x2_theta) + "["+str(x2_diff)+"]\r\n")
        elif party == "y":
            x2_prediction_serialised =io.read("x2/"+str(i)+"/","x2_prediction text",i)
            x2_prediction = [prikey.decrypt(ser.deserialiseEncrypted(pubkey,x[0])) for x in x2_prediction_serialised]
            gradient = x2_prediction - y
            gradient_out = [[x] for x in gradient]
            io.write(gradient_out,"gradient/"+str(i)+"/","gradient float",i)



main()
