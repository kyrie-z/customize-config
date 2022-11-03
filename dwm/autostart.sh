#while true; do
#	xsetroot -name "$( date )"
#	sleep 1s
#done &

while true; do
  feh --bg-fill --no-fehbg -z ~/Downloads/*.png
  sleep 5m
done &

#slstatus &
dwmblocks &

#picom --experimental-backends -b
picom -b

after_dwm_run(){
  sleep 1s
  nm-applet 
}

after_dwm_run &
