# textwall-monitoring

To install clone the this repository and then run: `pip install -r requirements.txt`.

To execute in top folder: `python attendance_monitoring.py textwall_sample.csv student_numbers.csv module_codes.csv 2019-09-26`. The last argument is optional and defaults to `2019-08-26`.

The date is the first Monday of the academic year i.e. in 2018 this was 27th August 2018.

## Example `textwall_sample.csv`

Output from textwall.

```csv
"=""18082660, 0009, Q5ST""","","=""2019-01-13""","=""22:30:04"""
"="",17019608,0006,equi""","","=""2019-01-12""","=""12:10:26"""
```

## Example `student_numbers.csv`

List of student numbers by year group.

```csv
ug_year_one,ug_year_two,ug_year_three,ug_year_four
17047916,18124624,18135870,18137582
18047901,16015544,18144908,14014482

```

## Example `module_codes.csv`

List of all valid module codes without prefix PHAS.

```csv
module
0002
0003
```
