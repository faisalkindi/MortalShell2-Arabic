# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(os.path.dirname(__file__)))
from _apply import apply

ar = [
"انصرف.",
"أنت… تتحسّن.",
"صرتَ… مثلي تمامًا.",
"أنت… أعرف أنك أخذته.",
"إنه… عمل لا بأس به.",
"… سقطتُ. ساعدني على النهوض أخيرًا.",
]

apply(103, ar)
