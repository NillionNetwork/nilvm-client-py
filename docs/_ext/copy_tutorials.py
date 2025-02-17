"""
Doc build support
"""

import json
from pathlib import Path


def setup(app):
    # pylint:disable=unused-argument
    """copy jupyter notebooks for sphinx inclusion"""
    file_dir = Path(__file__).parent
    for f in file_dir.joinpath("../../tutorials").glob("*.ipynb"):
        with open(
            file_dir.joinpath(f"../tutorials/{f.stem}.nblink"), "w", encoding="utf-8"
        ) as output_file:
            nb_link = {
                "path": f"../../tutorials/{f.name}",
                "extra-media": ["../../tutorials/_static"],
            }
            json.dump(nb_link, output_file)
