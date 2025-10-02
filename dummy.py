from numpy.random import default_rng as rng
print(rng(0).integers(0, 5000, size=(3, 30)).tolist())
