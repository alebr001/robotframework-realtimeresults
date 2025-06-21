*** Settings ***
Library    OperatingSystem
Library    RequestsLibrary


*** Test Cases ***
Example API Call - Root
    Sleep    1s
    Create Session    mysession    http://127.0.0.1:5000
    ${response}=    GET On Session    mysession    /
    Should Be Equal As Integers    ${response.status_code}    200
    Log    Response: ${response.content}

Example API Call - Not Found
    Sleep    1s
    Create Session    mysession    http://127.0.0.1:5000
    ${response}=    GET On Session    mysession    /doesnotexist
    Should Be Equal As Integers    ${response.status_code}    404
    Log    Response: ${response.content}

Example 2 API Call - Root
    Sleep    1s
    Create Session    mysession    http://127.0.0.1:5000
    ${response}=    GET On Session    mysession    /
    Should Be Equal As Integers    ${response.status_code}    200
    Log    Response: ${response.content}

Example 2 API Call - Not Found
    Sleep    1s
    Create Session    mysession    http://127.0.0.1:5000
    ${response}=    GET On Session    mysession    /doesnotexist
    Should Be Equal As Integers    ${response.status_code}    404
    Log    Response: ${response.content}
    
Example 3 API Call - Root
    Sleep    1s
    Create Session    mysession    http://127.0.0.1:5000
    ${response}=    GET On Session    mysession    /
    Should Be Equal As Integers    ${response.status_code}    200
    Log    Response: ${response.content}

Example 3 API Call - Not Found
    Sleep    1s
    Create Session    mysession    http://127.0.0.1:5000
    ${response}=    GET On Session    mysession    /doesnotexist
    Should Be Equal As Integers    ${response.status_code}    404
    Log    Response: ${response.content}