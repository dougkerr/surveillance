# If kswapd0 uses over 10% of the CPU, reboot.
# Check every ten minutes.

while true
do
    kswappct=`ps -C kswapd0 -o '%cpu' --no-header`
    #kswappct=`ps -C python -o '%cpu' --no-header`
    if expr $kswappct '>' 1 > /dev/null
    then
        echo `date --iso-8601=seconds` \
            "kswapd0 using $kswappct% of CPU." \
            >> /var/opt/communityview/log/kswapd0hack.log
        echo `date --iso-8601=seconds` `uptime` \
            >> /var/opt/communityview/log/kswapd0hack.log
    fi
    if expr $kswappct '>' 10 > /dev/null
    then
        echo `date --iso-8601=seconds` \
            "kswapd0 using $kswappct% of CPU. Rebooting." \
            >> /var/opt/communityview/log/kswapd0hack.log
        echo `date --iso-8601=seconds` `uptime` \
            >> /var/opt/communityview/log/kswapd0hack.log
        ps ax >> /var/opt/communityview/log/kswapd0hack.log
        shutdown -r
    fi
    sleep 600
done
