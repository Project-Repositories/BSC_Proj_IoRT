# https://stackoverflow.com/a/58470178
def clamp(value, lower, upper):
    return lower if value < lower else upper if value > upper else value
