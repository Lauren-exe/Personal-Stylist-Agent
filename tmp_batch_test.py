import importlib.util

spec = importlib.util.spec_from_file_location('weather_mod', 'weather.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

samples = [
    'Berkeley, CA',
    'berkely, ca',
    'seatlle, wa',
    'sammamish, wa',
    'newyork, ny',
    'sanfransisco, ca',
    'losangeles, ca',
    '????????',
    'wasington, dc',
    'washinton, dc',
    'californa',
    'santaclara, ca'
]
for sample in samples:
    print(sample, '->', mod.normalize_location_input(sample))
