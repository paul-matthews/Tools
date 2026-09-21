-- Review
tell application id "com.google.chrome" to activate
delay 0.2
tell application "Moom" to run "Left half"
tell application id "com.googlecode.iterm2" to activate
delay 0.2
tell application "Moom" to run "Right half"
