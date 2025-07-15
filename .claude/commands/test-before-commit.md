---
description: Simple test runner for uncommitted Python files
allowed-tools: Bash(git:*), Bash(python:*), Bash(pip:*), View, Edit, Create
---

# detect all python change or new files from last commit
list all the new files or changes file releative to the last commit
if you don't find any changes in current git state don't bring changes from previous commit
refer only to the files in project that were changed locally


# what to do next
if no changes were detected skip the next steps below

#verify archtecture is not broken
insepct the last chnages found and verify the changes are not against the @ARCHITECTURE.md file if changes seems to break the archtecture create full report on what seems to break the archtecture




#detect releated unit test
for the change files identify unit tests which cover this files
check if the unit test are handling this files

#activate venv
look for venv directory in this project 
activate it

#run corrsponding unit test
for the releated unit test RUN  the unit tests and create a report

#create a Detailed report
Create details report and save it as test_before_commit.md
