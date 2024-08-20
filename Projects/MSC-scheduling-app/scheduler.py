import requests
from model import Tutor
from googleapiclient.discovery import build
from ortools.sat.python import cp_model
from tabulate import tabulate


def main() -> None:
  model = cp_model.CpModel()
  shift_options = {}

  # number of tutors
  num_tutors = 14

  # number of shifts in day
  num_shifts = 13

  # number of days
  num_days = 5

  # mininum number of hours worked
  min_hours = 4

  # max number of hours worked
  max_hours = 10

  # list of all tutors
  tutor_list = [Tutor() for i in range(num_tutors)]


  for x in range(num_tutors):
    for y in range(num_days):
      for z in range(num_shifts):
        shift_options[(x, y, z)] = model.NewBoolVar("shift with id" + str(x) + " " + str(y) + " " + str(z))

  # Constraint 1: at most 3 tutors per shift
  for y in range(num_days):
    for z in range(num_shifts):
      model.Add(sum(shift_options[(x,y,z)] for x in range(num_tutors)) <= 3)

  # Constraint 2: each tutor works a number of hours within the requested range
  for x in range(num_tutors):
    shifts_worked = []
    for y in range(num_days):
      for z in range(num_shifts):
        shifts_worked.append(shift_options[x, y, z])
    model.Add(sum(shifts_worked) >= min_hours * 2)
    model.Add(sum(shifts_worked) <= max_hours * 2)

  # Constraint 3: each tutor must only work the shifts in which they are available (TBD)
  # tutor_list[x].available_shifts[][] == 1

  # Constraint 4: no tutor is scheduled for a stand-alone 30 minute shift


  solver = cp_model.CpSolver()

  class ScheduleSolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self, shifts, num_tutors, num_shifts, num_days, limit):
      cp_model.CpSolverSolutionCallback.__init__(self)
      self._shifts = shifts
      self._num_tutors = num_tutors
      self._num_shifts = num_shifts
      self._num_days = num_days
      self._solution_count = 0
      self._solution_limit = limit 

    def on_solution_callback(self):
      self._solution_count += 1
      print(f"Solution {self._solution_count}")
      schedule = []
      for s in range(num_shifts):
        row = [f"Shift {s}"]
        for d in range(num_days):
          scheduled_tutors = []
          for t in range(num_tutors):
            if self.value(self._shifts[(t, d, s)]):
              scheduled_tutors.append(t)
          row.append(scheduled_tutors)
        schedule.append(row)
      headers = ["Shift/Day"] + [f"Day {d}" for d in range(num_days)]
      print(tabulate(schedule, headers = headers))
      if self._solution_count >= self._solution_limit:
        print(f"Stop search after {self._solution_limit} solutions")
        self.stop_search()
    
    def solutionCount(self):
      return self._solution_count
    
  solution_limit = 5
  solution_printer = ScheduleSolutionPrinter(shift_options, num_tutors, num_shifts, num_days, solution_limit)

  solver.solve(model, solution_printer)

if __name__ == "__main__":
  print("hello")
  main()


# SPREADSHEET_ID = ''
# API_KEY = 'AIzaSyCKgzekY18qYtQn2ILb3vS23Vjg8oxZhUE'

# def authenticate_sheets(api_key):
#  return build('sheets', 'v4', developerKey = api_key).spreadsheets()
