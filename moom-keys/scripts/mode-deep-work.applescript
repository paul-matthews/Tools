-- Deep work
tell application id "com.vscodium" to activate
delay 0.2
tell application "Moom" to run "Left two-thirds"
tell application id "com.googlecode.iterm2" to activate
delay 0.2
tell application "Moom" to run "Right third"
do shell script "shortcuts run " & quoted form of "Deep Work"
