from time import process_time

def elapsed_time(funcion, return_value=False):
    start = process_time()
    ret = funcion()
    end = process_time()
    time = end - start
    return time if not return_value else (time, ret)

