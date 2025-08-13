# input="video.mp4"
# ffmpeg -i "$input" -ss 00:00:30 -t 00:01:00 -c copy "${input%.*}_cut.${input##*.}"
# Output: video_cut.mp4

input="raw_files/IMG_2506.M4V"
ffmpeg -i "$input" -ss 00:00:31.88 -to 00:00:37.00 -c copy "${input%.*}_cut_1.mp4"

ffmpeg -i "$input" -ss 00:01:12.00 -to 00:01:22.00 -c copy "${input%.*}_cut_2.mp4"

ffmpeg -i "$input" -ss 00:01:38.47 -to 00:01:45.12 -c copy "${input%.*}_cut_3.mp4"

ffmpeg -i "$input" -ss 00:01:52.19 -to 00:02:16.00 -c copy "${input%.*}_cut_4.mp4"

ffmpeg -i "$input" -ss 00:02:23.09 -to 00:02:29.27 -c copy "${input%.*}_cut_4.mp4"

ffmpeg -i "$input" -ss 00:02:29.27 -to 00:02:50.00 -c copy "${input%.*}_cut_5.mp4"

input="raw_files/IMG_2508.M4V"

ffmpeg -i "$input" -ss 00:00:05.46 -to 00:00:10.00 -c copy "${input%.*}_cut_0.mp4"

ffmpeg -i "$input" -ss 00:00:10.00 -to 00:00:15.00 -c copy "${input%.*}_cut_1.mp4"

ffmpeg -i "$input" -ss 00:00:15.00 -to 00:00:20.00 -c copy "${input%.*}_cut_2.mp4"

ffmpeg -i "$input" -ss 00:00:20.00 -to 00:00:25.00 -c copy "${input%.*}_cut_3.mp4"

ffmpeg -i "$input" -ss 00:00:25.00 -to 00:00:30.48 -c copy "${input%.*}_cut_4.mp4"

input="raw_files/IMG_2509.M4V"

ffmpeg -i "$input" -ss 00:00:05.46 -to 00:00:10.00 -c copy "${input%.*}_cut_0.mp4"