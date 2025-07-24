#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
# @Project: PyCharm
# @File    : tools.py
# @Time: 2025 2025/7/24 21:40
# @Author  : Leeby Gu
'''
import json
from pathlib import Path


data_dir = Path("../data")

input_file = data_dir.joinpath("example/tmp.json")
output_file = data_dir.joinpath("example/gywx_example.json")


with open(input_file, "r", encoding="utf-8") as f:
    data_dict = json.load(f)
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data_dict, f, ensure_ascii=False, indent=4)