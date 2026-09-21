Set shell = CreateObject("WScript.Shell")
root = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
pythonw = root & "\.venv\Scripts\pythonw.exe"
script = root & "\sanvi_background.py"

If Not CreateObject("Scripting.FileSystemObject").FileExists(pythonw) Then
  MsgBox "SANVI environment is not installed. Run start_sanvi.bat once first.", 48, "SANVI AI"
  WScript.Quit 1
End If

shell.Run """" & pythonw & """ """ & script & """", 0, False
