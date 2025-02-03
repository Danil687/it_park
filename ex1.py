def sum_list(a):
    s = 0
    s1 = 0
    for x in a:
        if type(x) == int:
            s += x
        elif isinstance(x, str):
            s1 += len(x)
        elif type(x) == list:
          ss, ss1 = sum_list(x)
          s += ss
          s1 += ss1
    return s, s1
a = [1,3,5,7,[12,3, 'q'],'snds']
print(sum_list(a))