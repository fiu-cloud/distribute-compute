import numpy as np
arr = np.matrix([[1, 2, 3 , "a"], [5,6,7,"bc"]])
print(type(arr))
b = arr[:,[1,2,3]]
print(b)

#x = np.array([('Rex', 9, 81.0), ('Fido', 3, 27.0)],
#             dtype=[('name', 'U10000'), ('age', 'i4'), ('weight', 'f4')])
#name = (x['name'])
#print(name)
#print(type(name))
