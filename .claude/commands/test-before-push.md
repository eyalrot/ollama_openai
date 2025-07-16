---
description: Simple test runner for uncommitted Python files
allowed-tools: Bash(git:*), Bash(python:*), Bash(pip:*), View, Edit, Create
---

# detect all python change or new files from last commit
find all the files that are going to be pushed to git
refer only to the files which are goint to be pushed

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

# Create a Detailed report
Create details report and save it as test_before_push.md

#Issue a warning in case of an error
in case there is violation or unit test is not passing add a clear messaged
!!!! changes need to be REVERTED or fixed before push

