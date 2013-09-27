#!/bin/bash
set -eux

curl 'https://docs.google.com/document/d/1bK-x3UTGk2qVW1VqxSp2MmQEgQ4z_8cXuB0QlzAUfco/pub?embedded=true' > assets/content/u1l3.html
curl 'https://docs.google.com/document/d/1IUdglUPuUEymoqmn8WVsfe_wSjWDWPWloWSe03VIHMU/pub?embedded=true' > assets/content/u2l1.html
curl 'https://docs.google.com/document/d/1pyAChPS6ePKs09opecbPDYjdaodV0lWsJXkl7PkFAx4/pub?embedded=true' > assets/content/u2l2.html
curl 'https://docs.google.com/document/d/1bAR4SWYzW6gzBFldWPkQ9mb5bp_6OHwUc_B3G7YDhVk/pub?embedded=true' > assets/content/u3l1.html
curl 'https://docs.google.com/document/d/1ROhL2D75oA-9tBaz5Q8U0bLp8ZVk5YHSMZvQHMc49CQ/pub?embedded=true' > assets/content/u4l1.html
# 4
curl 'https://docs.google.com/document/d/1teeNy73qm7kDjSIdB8csrTXgopgQW2S11RIB1rTHccU/pub?embedded=true' > assets/content/u5l1.html
# 6
# 7
curl 'https://docs.google.com/document/d/118I4eHLcjgrdyj06vYDTzp2frKnR9wMIf9-Ydw10hpA/pub?embedded=true' > assets/content/u8l1.html
# 9
# 10
# 11

# tidy -utf8 -i -m file-to-modify
