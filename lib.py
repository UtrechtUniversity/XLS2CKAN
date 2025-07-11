import hashlib
import logging
import re

log = logging.getLogger(__name__)

def generate_identifier(string_input):
    new_input = string_input.replace(' ', '')
    new_input = new_input.lower()
    return hashlib.md5(new_input.encode()).hexdigest()

def encode(input):
    return generate_identifier(input)

def decode(input):
    return None
    # TODO: depends on lowering/removing spaces in source stringss


def get_dict_as_strings(my_dict):
    """
    returns a vertical string list of key, value pairs
    :param my_dict:
    :return:
    """

    out = None
    for k, v in my_dict.items():
        if k is None:
            key = 'None'
        else:
            key = str(k)
        if v is None:
            value = 'None'
        else:
            value = str(v)
        if out is not None:
            out = out +'\n'
            out = out + key + ' : ' + value
        else:
            out = key + ' : ' + value
    return out

def open_folder(path):
    import subprocess
    import platform

    # Path to the folder you want to open
    folder_path = path

    # Determine the file manager based on the platform
    if platform.system() == "Windows":
        subprocess.Popen(f'explorer "{folder_path}"')
    elif platform.system() == "Linux":
        subprocess.Popen(['xdg-open', folder_path])
    elif platform.system() == "Darwin":
        subprocess.Popen(['open', folder_path])

def row_string_to_integer_list(inputstring):
    """
    returns row list to be processed in pandas!
    :param inputstring:
    :return:
    """
    # inefficient way:
    # replacements = str.maketrans({" ": "", "[": "", "]": ""})
    # new_string = str(inputstring).translate(replacements)

    new_string = re.sub(r'[^0-9-,]', '', inputstring)
    row_list = new_string.split(',')
    # remove possible empty values:
    row_list = [row for row in row_list if row != '']
    ranges = []
    for index, row in enumerate(row_list):
        # check on validity of ranges of and expand intervals
        if row.find('-') != -1:
            if ((row.count('-') > 1) or (row[0] == '-') or (row[-1] == '-')):
                log.info(row + ' is not a valid range.')
                row_list = None
            else:
                start = int(row.split('-')[0])
                end = int(row.split('-')[1])
                if start > end:
                    temp = start
                    start = end
                    end = temp
                row_list[index] = str(start)
                if start != end:
                    # we have a valid non-zero length range
                    number = start + 1
                    range = []
                    while number <= end:
                        range.append(str(number))
                        number += 1
                    ranges.append(range)
    for range in ranges:
        row_list += range
        # make unique and sorted
    export_list = []
    for index, row in enumerate(row_list):
        # convert to integer list
        export_list.append(int(row_list[index]))
    export_list = sorted(set(export_list))
    export_list = [i for i in export_list if i > 1]  # only Excel rows >1 (header) are allowed
    # from Excel to pandas: (move to zero-based and remove header
    for index, rownum in enumerate(export_list):
        export_list[index] = rownum - 2
    return export_list
