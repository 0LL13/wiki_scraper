def ask_for_wahlperiode():
    wahlperiode_default = '14'
    wahlperiode = input('Which legislature? ')
    if wahlperiode:
        return wahlperiode
    else:
        return wahlperiode_default
