import inspect
import os
from datetime import datetime

# def log_execution(description=""):
#     current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     frame = inspect.currentframe().f_back
#     function_name = frame.f_code.co_name
#     file_name = frame.f_code.co_filename
#     line_number = frame.f_lineno
#     with open('execute.log', 'a') as log_file:
#         log_file.write(f"{current_time} {function_name} {file_name}:{line_number} {description}\n")

# # Usage example within other functions:
# # log_execution('Description of what the function is doing')

import inspect
from datetime import datetime

def log_execution(log_level="DEBUG", description=""):
    # Ensure the 'log' directory exists
    log_dir = 'log'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)


    # Construct log file path
    log_file_path = os.path.join(log_dir, 'execute.log')


    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    frame = inspect.currentframe().f_back
    function_name = frame.f_code.co_name
    file_name = frame.f_code.co_filename
    line_number = frame.f_lineno
    
    log_entry = f"[{current_time}] [{log_level.upper()}] [{file_name}] [{function_name}:{line_number}] - {description}\n"
    
    with open(log_file_path, 'a') as log_file:
        log_file.write(log_entry)
        
'''
Log Level
Common log levels include:

DEBUG: Detailed information for diagnosing problems.
INFO: Confirmation that things are working as expected.
WARNING: An indication that something unexpected happened, or indicative of some problem in the near future (e.g., ‘disk space low’). The software is still working as expected.
ERROR: Due to a more serious problem, the software has not been able to perform some function.
CRITICAL: A serious error, indicating that the program itself may be unable to continue running.
By including the log level, you can filter or search logs effectively based on the severity of the issues.
'''