#Requires AutoHotkey v2.0
#UseHook
#singleinstance force
KeyHistory 0

F1::
{
  ; Check the active process
  processName := WinGetProcessName("A")
  if (processName != "msedge.exe" && processName != "chrome.exe" && processName != "explorer.exe")
    return
  
  ; Get the active window's position and size
  WinGetPos(&x, &y, &width, &height, "A")
  
  ; Calculate new geometry for the launcher window
  newWidth := Round(width * 2 / 3)
  newHeight := Round(height / 3)
  newX := Round(x + (width - newWidth) / 2)
  newY := Round(y + height / 5)
  
  ; Construct the path to launcher.py
  scriptDir := A_ScriptDir
  pythonScript := scriptDir . "\launcher.py"
  
  ; Build and run the command
  command := '"python.exe" "' . pythonScript . '" "' . processName . '" ' . newX . ' ' . newY . ' ' . newWidth . ' ' . newHeight
  Run(command, , "Hide")
  
  ; Wait for the Bookmark Launcher window to appear (timeout after 5 seconds)
  WinWait("Bookmark Launcher", "", 5)
  if (!WinExist("Bookmark Launcher"))
    return
  
  ; Attempt to activate the window multiple times
  loop 3
  {
    WinActivate("Bookmark Launcher")
    Sleep 200
    if (WinActive("Bookmark Launcher"))
      break
  }
  
  ; If still not active, restore and retry
  if (!WinActive("Bookmark Launcher"))
  {
    WinRestore("Bookmark Launcher")  ; Ensure it’s not minimized
    Sleep 100
    WinActivate("Bookmark Launcher")
    Sleep 200
  }
  
  ; Last resort: temporarily set Always On Top
  if (!WinActive("Bookmark Launcher"))
  {
    WinSetAlwaysOnTop 1, "Bookmark Launcher"  ; Force to top
    Sleep 100
    WinSetAlwaysOnTop 0, "Bookmark Launcher"  ; Revert to normal
    Sleep 100
    WinActivate("Bookmark Launcher")
  }
}
