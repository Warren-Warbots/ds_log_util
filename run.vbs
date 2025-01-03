'Create File System Object for working with directories
Set fso = WScript.CreateObject("Scripting.FileSystemObject")



'Get the full path to the Python script
fullPythonScript = "C:\Users\Admin\Documents\warbots\ds_log_util\app.py"


'Get the full path to the Python executable (replace with your actual Python path)
pythonExe = "C:\Users\Admin\Documents\warbots\ds_log_util\.ds_log_util\Scripts\python.exe"


' Create Shell Object
Set objShell = WScript.CreateObject("WScript.Shell")
Set objEnv = objShell.Environment("PROCESS")
dim runObject

' Allow us to catch a script run failure
On Error Resume Next
Set runObj = objShell.Exec(pythonExe & " " & fullPythonScript)

' Loop to capture and display the output in real-time
Do While runObj.Status = 0
    ' Read from the output stream (stdout)
    If Not runObj.StdOut.AtEndOfStream Then
        WScript.StdOut.Write(runObj.StdOut.Read(1))  ' Read one character at a time
    End If
    WScript.Sleep 100 ' Small delay to prevent high CPU usage
Loop

' Check if an error occurred
If Err.Number <> 0 Then
    If WScript.Arguments.Count > 0 Then
        If (WScript.Arguments(0) <> "silent") Then
            WScript.Echo "Error Launching Python Script" + vbCrLf + Err.Description
        Else
            WScript.StdOut.Write("Error Launching Python Script")
            WScript.StdOut.Write(Error.Description)
        End If
    Else
        WScript.Echo "Error Launching Python Script"  + vbCrLf + Err.Description
    End If
    Set runObj = Nothing
    Set objShell = Nothing
    Set fso = Nothing
    WScript.Quit(1)
End If

Set runObj = Nothing
Set objShell = Nothing
Set fso = Nothing
WScript.Quit(0)