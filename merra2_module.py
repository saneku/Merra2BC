import pathes
import re
import os


numbers = re.compile(r'(\d+)')
def numericalSort(value):
    parts = numbers.split(value)
    return parts[9]


def get_ordered_mera_files_in_mera_dir():
    return sorted([f for f in os.listdir(pathes.mera_dir) if re.match(pathes.mera_files, f)], key=numericalSort)
