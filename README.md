# MSC Shift Scheduler
A tutor shift scheduling program for Cornell's Math Support Center.

## Prerequisites
- Python (version 3.8+)
- Google OR-Tools for Python
  
  ```
  python -m pip install ortools
  ```
  
- Tabulate
  
  ```
  pip install tabulate
  ```
  
## Installation 
1. Navigate to the latest release.
2. Download the source code and unzip.

## Usage
### Preparing the Data
1. After collecting tutor availability information, download the Google Forms responses as a `.csv` file.
2. Go to this [csv editor](https://edit-csv.net/) and import your file.
3. Find the column with the question `What would you like to be called on the tutor sheet? (If different from above)`.  If applicable, make the following changes:
   - If a tutor entered both their first and last name for this question, remove their last name.
   - If there are multiple tutors with the same preferred name, add their last initials to distinguish between them
4. Download the updated `.csv` file and name it `tutor_responses.csv`
5. Move `tutor_responses.csv` into the root directory of the downloaded source code. It should be in the same directory as `scheduler.py`.

### Running the Program
1. With the Terminal/Command Prompt, navigate to the directory containing `tutor_responses.csv` and the source files.
2. Run `scheduler.py`:
   
   ```
   python scheduler.py
   ```
   
3. The program will ask for a series of column numbers, which you can look up in the csv editor. Here's a description of the columns each input prompt corresponds to:
   #### General Information
   - `Name column`: The column containing full tutor names (not necessarily preferred).
   - `Nickname column`: The column containing the names the tutors would like to be called on the tutor sheet.
   - `Hours range column` The column containing range of hours tutors would like to work.
   #### Daytime Hours
   - `Available daytime hours start column (Enter 0 if N/A)`: The first column asking for core daytime shift availability.
   - `Available daytime hours end column (Enter 0 if N/A):`: The last column asking for core daytime shift availability.
   - `Preferred daytime hours start column (Enter 0 if N/A)`: The first column asking for core daytime shift preferences.
   - `Preferred daytime hours end column (Enter 0 if N/A)`: The last column asking for core daytime shift preferences.
   #### Evening/Weekend Hours
   - `Available evening range start column (Enter 0 if N/A)`: The first column asking for evening/weekend shift availability.
   - `Available evening range end column (Enter 0 if N/A)`: The last column asking for evening/weekend shift availability.
   - `Preferred evening range start column (Enter 0 if N/A)`: The first column asking for evening/weekend shift preferences.
   - `Preferred evening range end column (Enter 0 if N/A)` The last column asking for evening/weekend shift preferences.
4. The program will create `schedule.csv` containing the generated schedule and basic statistics.
