import numpy as np, random as random

iterations = 20
init = np.linspace(-5, 5, 1000)

# We generate a 2D grid
x1, x2 = np.meshgrid(init, init)

# To get reproducable values, provide a seed value
np.random.seed(1)

# Z is the elevation of this 2D grid
y = 31*x1 - 5.5*x2 + np.random.normal(size=x1.shape)


x1 = x1.flatten()
x2 = x2.flatten()
y = y.flatten()

alpha = 0.1
n = float(len(x1))
x1_theta = random.random() * max(x1)
x2_theta = random.random() * max(x2)
gradients = [0] * len(x1)

for i in range(0, iterations):

    #predict x1
    x1_prediction = x1 * x1_theta

    #predict x2
    x2_prediction = x1_prediction + x2 * x2_theta

    #calculate gradient
    gradient = x2_prediction - y

    #update x1
    x1_diff = sum(gradient * x1)
    x1_theta = x1_theta - (alpha / n) * x1_diff

    #update x2
    #x2_diff = sum(gradient * x2)
    x2_diff = sum([a*b for a,b in zip(gradient,x2)])
    x2_theta = x2_theta - (alpha / n) * x2_diff
    print(str(i) +" : " + str(x1_theta) + "["+str(x1_diff)+"], "+ str(x2_theta) + "["+str(x2_diff)+"]")

print("x1="+ str(x1_theta) + " x2="+str(x2_theta))