import os


def add_init_py_files(directory):
    for root, dirs, files in os.walk(directory):
        # Add __init__.py to each directory if it's missing
        init_file = os.path.join(root, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w"):  # Create an empty __init__.py file
                pass


add_init_py_files("../src")
