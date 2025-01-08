import sys
import csv
from tutor import Tutor
from ortools.sat.python import cp_model
from tabulate import tabulate
from enum import IntEnum
from datetime import datetime, timedelta

class Days(IntEnum):
  Monday = 0
  Tuesday = 1
  Wednesday = 2
  Thursday = 3
  Friday = 4
  Saturday = 5
  Sunday = 6

def parse_time(header) -> str:
  '''
  Given header string of the form 
  ". . . [0:00PM/AM]," 
  return time string within square brackets 
  '''
  start = header.rfind("[") + 1
  end = header.rfind("]")
  return header[start:end]

def validate_range(start, end):
  '''
  Checks if shift column range is valid 
  (start < end, either both are 0 or neither are 0)
  '''
  if start > end:
    print("Error: start column cannot be greater than end column")
    sys.exit(1)
  
  if (start == 0) ^ (end == 0):
    print("Error: if N/A, start and end must both be 0")
    sys.exit(1)

def assign_ranges(avail_start, avail_end, pref_start, pref_end):
  if pref_start == 0:
    rnge = range(avail_start - 1, avail_end)
    return rnge, rnge
  elif avail_start == 0:
    rnge = range(pref_start - 1, pref_end)
    return rnge, rnge
  else:
    avail_range = range(avail_start - 1, avail_end)
    pref_range = range(pref_start - 1, pref_end)
    return avail_range, pref_range

def get_column_ranges():
  '''
  Collects column ranges from user
  '''
  name_col = int(input("Name column: ")) - 1
  pref_name_col = int(input("Nickname column: ")) - 1
  hours_col = int(input("Hours range column: ")) - 1

  avail_col_start = int(input("Available daytime hours start column (Enter 0 if N/A): "))
  avail_col_end = int(input("Available daytime hours end column (Enter 0 if N/A): "))
  validate_range(avail_col_start, avail_col_end)

  pref_col_start = int(input("Preferred daytime hours start column (Enter 0 if N/A): "))
  pref_col_end = int(input("Preferred daytime hours end column (Enter 0 if N/A): "))
  validate_range(pref_col_start, pref_col_end)

  if (avail_col_start == 0) and (pref_col_start == 0): 
    print("Error: cannot have no daytime hours")
    sys.exit(1)

  avail_col_range, pref_col_range = assign_ranges(avail_col_start, avail_col_end, pref_col_start, pref_col_end)
  
  evening_avail_start = int(input("Available evening range start column (Enter 0 if N/A): "))
  evening_avail_end = int(input("Available evening range end column (Enter 0 if N/A): "))
  validate_range(evening_avail_start, evening_avail_end)

  evening_pref_start = int(input("Preferred evening range start column (Enter 0 if N/A): "))
  evening_pref_end = int(input("Preferred evening range end column (Enter 0 if N/A): "))  
  validate_range(evening_pref_start, evening_pref_end)

  if evening_avail_start == 0 and evening_pref_start == 0:
    evening_avail_col_range = evening_pref_col_range = range(0, 0)
  else:
    evening_avail_col_range, evening_pref_col_range = assign_ranges(evening_avail_start, evening_avail_end, evening_pref_start, evening_pref_end)

  return {"name_col" : name_col,
          "pref_name_col" : pref_name_col,
          "hours_col" : hours_col,
          "avail_col_range": avail_col_range,
          "pref_col_range": pref_col_range,
          "evening_avail_col_range": evening_avail_col_range,
          "evening_pref_col_range": evening_pref_col_range}
  
def get_hours(col_ranges, header): 
  '''
  Returns hours, a list of all possible shift times in a given day, and 
  header_to_time, which maps each header to its corresponding time string (for efficient access later)
  '''
  hours = []
  header_to_time = {}

  for i in col_ranges["avail_col_range"]:
    h = header[i]
    time_str = parse_time(h)
    header_to_time[h] = time_str
    hours.append(time_str)

  for j in col_ranges["evening_avail_col_range"]:
    h = header[j]
    time_str = parse_time(h)
    header_to_time[h] = time_str
    hours.append(time_str)

  hours = list(set(hours))
  hours.sort(key=lambda x: datetime.strptime(x, "%I:%M%p"))
  return hours, header_to_time

def parse_shifts(col_ranges, line, header_to_time, hours_to_indices, header, shifts_range, days_range, avail):
  '''
  Parses available/preferred shifts for tutor at current line
  '''
  tutor_shifts = [[0 for _ in shifts_range] for _ in days_range]

  if avail:
    col_range = col_ranges["avail_col_range"]
    evening_col_range = col_ranges["evening_avail_col_range"]
    offset_daytime = 0 
    offset_evening = 0
  else:
    col_range = col_ranges["pref_col_range"]
    evening_col_range = col_ranges["evening_pref_col_range"]
    offset_daytime = col_ranges["pref_col_range"].start - col_ranges["avail_col_range"].start
    offset_evening = col_ranges["evening_pref_col_range"].start - col_ranges["evening_avail_col_range"].start

  for i in col_range:
    if (line[i] != ""):
      days_avail = line[i].split(";")
      time_str = header_to_time[header[i - offset_daytime]]
      for d in days_avail:
        tutor_shifts[Days[d].value][hours_to_indices[time_str]] = 1
  
  for i in evening_col_range:
    if (line[i] != ""):
      days_avail = line[i].split(";")
      time_str = header_to_time[header[i - offset_evening]]
      for d in days_avail:
        tutor_shifts[Days[d].value][hours_to_indices[time_str]] = 1
  
  return tutor_shifts

def parse_tutor(line, col_ranges, header_to_time, hours_to_indices, header, shifts_range, days_range):
  '''
  Parses fields of tutor from line and returns a Tutor object with 
  those fields
  '''
  # tutor name
  name = line[col_ranges["name_col"]]
  pref_name = line[col_ranges["pref_name_col"]]
  tutor_name = pref_name if pref_name else name.split(" ")[0]

  # min/max hours
  hours_range = line[col_ranges["hours_col"]].split("-")
  min_hours = float(hours_range[0])
  max_hours = min_hours if (len(hours_range) == 1 or hours_range[1] == "") else float(hours_range[1])

  # available and preferred shifts
  tutor_avail_shifts = parse_shifts(col_ranges, line, header_to_time, hours_to_indices, header, shifts_range, days_range, True)
  tutor_pref_shifts = parse_shifts(col_ranges, line, header_to_time, hours_to_indices, header, shifts_range, days_range, False)
  
  return Tutor(tutor_name, min_hours, max_hours, tutor_avail_shifts, tutor_pref_shifts)

def process_data(col_ranges): 
  '''
  Process data from CSV, storing it in structures that can be accessed by
  the algorithm. 
  '''
  with open('tutor_responses.csv', 'r') as file:
    reader = csv.reader(file)
    header = next(reader)
    hours, header_to_time = get_hours(col_ranges, header)
    hours_to_indices = {s : i for i, s in enumerate(hours)}
    
    # number of shifts in day
    num_shifts = len(hours)
    shifts_range = range(num_shifts)

    num_days = 7
    days_range = range(num_days)

    tutor_list = []
    for line in reader:
      tutor_list.append(parse_tutor(line, col_ranges, header_to_time, hours_to_indices, header, shifts_range, days_range))

    return hours, tutor_list

def create_constraints(model, tutor_list, days_range, shifts_range, breaks):
  '''
  Provide scheduling constraints and objective functions for the algorithm
  '''
  shift_options = {}
  tutor_range = range(len(tutor_list))

  for x in tutor_range:
    for y in days_range:
      for z in shifts_range:
        shift_options[(x, y, z)] = model.NewBoolVar("shift with id" + str(x) + " " + str(y) + " " + str(z))

  # Constraint: at most 3 tutors per shift
  for y in days_range:
    for z in shifts_range:
      model.Add(sum(shift_options[(x,y,z)] for x in tutor_range) <= 3)

  # Constraint: each tutor works a number of hours within their requested range
  for x in tutor_range:
    shifts_worked = []
    for y in days_range:
      for z in shifts_range:
        shifts_worked.append(shift_options[x, y, z])
    #model.Add(sum(shifts_worked) >= int(tutor_list[x].min_hours * 2))
    model.Add(sum(shifts_worked) <= int(tutor_list[x].max_hours * 2))

  # Constraint: each tutor works only the shifts in which they are available 
  for x in tutor_range:
    for y in days_range:
      for z in shifts_range:
        model.Add(shift_options[(x, y, z)] <= tutor_list[x].available_shifts[y][z])

  breaks_minus_one = [b - 1 for b in breaks]
  # Constraint: no tutor is scheduled for a stand-alone 30 minute shift
  for x in tutor_range:
    for y in days_range:
      for z in shifts_range:
          if (z == 0) or (z in breaks):
            model.Add(shift_options[(x, y, z + 1)] == 1).OnlyEnforceIf(shift_options[(x, y, z)])
          elif (z in breaks_minus_one) or (z == shifts_range.stop - 1):
            model.Add(shift_options[(x, y, z - 1)] == 1).OnlyEnforceIf(shift_options[(x, y, z)])
          else:
            model.AddBoolOr([shift_options[(x, y, z - 1)], shift_options[(x, y, z + 1)]]).OnlyEnforceIf(shift_options[(x, y, z)])

  # Maximize preferred shifts scheduled
  model.maximize(
    sum(
      tutor_list[t].preferred_shifts[d][s] * shift_options[(t, d, s)] 
      for t in tutor_range
      for d in days_range
      for s in shifts_range
    )
  )

  # Fill in as many shifts as possible
  model.maximize(
    sum(
      shift_options[(t, d, s)]
      for t in tutor_range
      for d in days_range
      for s in shifts_range
    )
  )

  return shift_options

def get_breaks(hours):
  '''
  Given sorted list of hours, return list containing all indices i where 
  the difference between hours[i] and hours[i-1] is greater than 30 minutes
  '''
  breaks = []
  i = 1
  while i < len(hours):
    if (datetime.strptime(hours[i], "%I:%M%p") - datetime.strptime(hours[i - 1], "%I:%M%p") > timedelta(minutes=30)):
      breaks.append(i)
    i += 1
  return breaks

def print_solution(solver, shift_options, hours, tutor_list, tutor_range, days_range, shifts_range):
  '''
  Prints formatted schedule generated by algorithm. Returns list representation
  of schedule.
  '''
  print("Solution: ")
  schedule = []
  schedule_list = []

  for s in shifts_range:
    row = [hours[s]]
    for d in days_range:
      scheduled_tutors = []
      for t in tutor_range:
        if solver.value(shift_options[(t, d, s)]):
          scheduled_tutors.append(tutor_list[t].name)
          tutor_list[t].scheduled_hours += 0.5
      row.append(", ".join(scheduled_tutors))
    schedule.append(row)
  headers = ["Shift/Day"] + [Days(d).name for d in days_range]
  schedule_table = tabulate(schedule, headers = headers)
  print(schedule_table)

  schedule_list = []
  schedule_list.append(headers) 
  schedule_list.extend(schedule)

  num_pref_shifts = sum(sum(row) for tutor in tutor_list for row in tutor.preferred_shifts)
  print(
    f"Number of shift requests met = {solver.objective_value}",
    f"(out of {num_pref_shifts})",
  )

  return schedule_list

def print_stats(tutor_list, tutor_range):
  '''
  Prints formatted table displaying each tutor's min and max hours, as well as
  how many hours they are scheduled for. Returns list representation of table
  '''
  print("Statistics: ")
  stats = []
  for t in tutor_range:
    curr_tutor = tutor_list[t]
    row = [curr_tutor.name]
    row.append(curr_tutor.min_hours)
    row.append(curr_tutor.max_hours)
    row.append(curr_tutor.scheduled_hours)
    stats.append(row)
  headers_stats = ["Tutor"] + ["Min hours"] + ["Max hours"] + ["Scheduled hours"]
  stats_table = tabulate(stats, headers = headers_stats)
  print(stats_table)

  stats_list = []
  stats_list.append(headers_stats)
  stats_list.extend(stats)
  return stats_list

def create_csv(schedule_list, stats_list):
  '''
  Writes schedule and stats table to CSV file
  '''
  with open("schedule.csv", "w") as output_file:
    writer = csv.writer(output_file)
    writer.writerows(schedule_list)
    writer.writerow([])
    writer.writerows(stats_list)

def output_solution(solver, status, shift_options, hours, tutor_list, tutor_range, days_range, shifts_range):
  '''
  Prints optimal solution with statistics and writes results to CSV output file.
  '''
  if status == cp_model.OPTIMAL:
    schedule_list = print_solution(solver, shift_options, hours, tutor_list, tutor_range, days_range, shifts_range)
    print()
    stats_list = print_stats(tutor_list, tutor_range)
    create_csv(schedule_list, stats_list)
  else:
    print("No optimal solution found!")

def main() -> None:
  col_ranges = get_column_ranges()
  hours, tutor_list = process_data(col_ranges)
  breaks = get_breaks(hours)

  tutor_range = range(len(tutor_list))
  days_range = range(7)
  hours_range = range(len(hours))

  model = cp_model.CpModel()
  shift_options = create_constraints(model, tutor_list, days_range, hours_range, breaks)
  solver = cp_model.CpSolver()
  status = solver.solve(model)
  output_solution(solver, status, shift_options, hours, tutor_list, tutor_range, days_range, hours_range)

if __name__ == "__main__":
  main()