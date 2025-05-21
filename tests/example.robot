*** Settings ***
Library    OperatingSystem

*** Test Cases ***
Example Test Passes
    Log    This is a passing test.
    Sleep    5s

Example Test Fails
    Fail    This test is meant to fail.