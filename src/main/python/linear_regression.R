######################################
# Set up a simple artificial dataset
######################################
n = 50
x1 = 11:(10+n)
x2 = runif(n,5,95)
x3 = rbinom(n,1,0.5)

x = data.frame(x1,x2,x3)
x = scale(x)
x = data.frame(1,x) # the intercept is handled using a column of 1's

sigma = 1.4
eps = rnorm(x1, 0, sigma) # generate noise vector

b = c(17, -2.5, 0.5,-5.2) # the real model coefficient

y = b[1] + b[2] * x[,2] + b[3] * x[,3] + b[4] * x[,4] + scale(eps) # target variable
print(paste(">Y",y))
##############################################################################
# Batch Gradient Descent algorithm, here for benchmarking and error checking
# For a refresher on the algorithm, read the first 6 pages of
# http://cs229.stanford.edu/notes/cs229-notes1.pdf
##############################################################################

lm_sgd <- function(iter, rate) {
    theta = c(0,0,0,0)
    alpha = rate
    for (iter in 1:iter) {
        adj = c(0,0,0,0)
        for (i in 1:4) {
            for (j in 1:n) {
                adj[i] = adj[i] + (sum(x[j,] * theta) - y[j]) * x[j,i]
            }
            # theta[i] = theta[i] - (alpha / n) * adj[i] # adjust as we go is faster
        }
        for (i in 1:4) theta[i] = theta[i] - (alpha / n) * adj[i]
        print(adj)
    }
    print(theta)
}

# lm_sgd(50, 0.1)

##########################################################################################
# Distributed Privacy-Preserving Gradient Descent algorithm for Linear Regression
##########################################################################################
# Basic setup:
# FIU holds the vector y of true labels
# RE1 holds the data x[,1:3]
# RE2 holds the data x[,4]
# Together, they want to learn a linear model to predict y using x but in such a way that
# - nobody sees each other's data,
# - RE1 holds the coefficients for the variables it holds, which is not visible to others
# - RE2 holds the coefficients for the variables it holds, which is not visible to others
# - Prediction of a new instance requires the collaboration of RE1 and RE2
###########################################################################################

###############################################################################################
# FIU first generates a public-private key pair using the Paillier scheme
# Public key is used by RE1 and RE2 to encrypt their data and do maths on them.
# Private key is visible only to FIU and is used by the FIU to decrypt data sent from the REs.
###########

library(homomorpheR)
source("paillier.R")  # import functions for extending Paillier to floating-point numbers
keypair = PaillierKeyPair$new(modulusBits = 1024)
pubkey = keypair$pubkey
privkey = keypair$getPrivateKey()

# Some useful constants
zero = pubkey$encrypt('0')
one = pubkey$encrypt('1')

##################################################################
# Here are the functions to setup the parties in the computation
#################

x1 = c() # these 3 vectors belong to RE1
x2 = c()
x3 = c()

re1setup = function() {
    x1 <<- encrypt(x[,1])
    x2 <<- encrypt(x[,2])
    x3 <<- encrypt(x[,3])
}

x4 = c() # this belong to RE2

re2setup = function() {
    x4 <<- encrypt(x[,4])
}

mastersetup = function() {
    re1setup()
    re2setup()
}

############
# This function computes the gradient: the difference between predicted values (encrypted) by REs and the true values
# Note the gradient is unencrypted. We could encrypt it if necessary.
#########

master_grad <- function(x) {
    xd = decrypt(x)
    xd - y
}

###########
# This is used to compute the partial predictions based on RE1's data only. The values are encrypted.
###########
re1pred <- function() {
    return (addenc(smultenc(x1, theta1),
    addenc(smultenc(x2, theta2),
    smultenc(x3, theta3))))
}

#############
# Here, RE2 takes the partial prediction of RE1 and then add its contribution to the prediction.
# The final prediction values are encrypted.
###########

re2pred <- function(z) {
    return (addenc(z, smultenc(x4, theta4)))
}

cadj = c(0,0,0,0) # a variable we want to print to keep track of progress

#############
# This is RE1's model update function and implements the gradient descent update formula.
# It takes the gradient (unencrypted) from the master and then adjust its own theta.
# The whole computation is assumed to take place within RE1 and no encryption is required.
# We can encrypt the whole thing if we want to.
###########

re1update <- function(z) {
    theta1 <<- theta1 - (alpha / n) * sum(z * x[,1])
    theta2 <<- theta2 - (alpha / n) * sum(z * x[,2])
    theta3 <<- theta3 - (alpha / n) * sum(z * x[,3])
    cadj[1] <<- sum(z * x[,1])
    cadj[2] <<- sum(z * x[,2])
    cadj[3] <<- sum(z * x[,3])
}

#############
# This is RE2's model update function and implements the gradient descent update formula.
# It takes the gradient (unencrypted) from the master and then adjust its own theta.
# The whole computation is assumed to take place within RE1 and no encryption is required.
# We can encrypt the whole thing if we want to.
###########

re2update <- function(z) {
    theta4 <<- theta4 - (alpha / n) * sum(z * x[,4])
    cadj[4] <<- sum(z * x[,4])
}

##########################################################################
# Finally, this is the privacy-preserving linear regression algorithm.
# The algorithm can be sensitive to the learning rate.
##########################################################################

pp_lm_sgd <- function(iter, rate) {

    theta1 <<- 0
    theta2 <<- 0
    theta3 <<- 0
    theta4 <<- 0
    alpha <<- rate

    mastersetup() # encrypt the data and set up communication

    for (i in 1:iter) {
        p1 = re1pred() # partial prediction
        px = re2pred(p1) # full prediction
        grad = master_grad(px) # compute gradient based on difference between true values and predicted values
        print(paste(">GRAD",grad))
        re1update(grad) # update models independently
        re2update(grad)
        #print(cadj)
    }
    print(c(theta1,theta2,theta3,theta4))
}

#model0 = lm_sgd(100, 0.1)
model1 = pp_lm_sgd(20, 0.1)