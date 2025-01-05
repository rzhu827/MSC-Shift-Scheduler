class Tutor:
  def __init__(self, name, min_hours, max_hours, available_shifts, preferred_shifts):
    self.name = name
    self.min_hours = min_hours
    self.max_hours = max_hours
    self.scheduled_hours = 0
    self.available_shifts = available_shifts
    self.preferred_shifts = preferred_shifts


