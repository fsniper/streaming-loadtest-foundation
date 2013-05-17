for i in $(seq 1 3); do (./loadtest rtsp://mvodstream04.truelife.com:554/loadtest/_definst_/mp4:3/ftpfile/Movie/movie/chocolate_480p.mp4 2>&1 | tee file.$i &)  ; done 
