# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(os.path.dirname(__file__)))
from _apply import apply

ar = [
"(تمتمة سكرانة غير مفهومة)",
"هيا. جرّبني.",
"هيه، يا حلو؟",
"ما رأيك؟",
"أتريد الشجار يا صاحبي؟",
"أتريد أن نصنع الوحش ذا الظهرين؟",
]

apply(96, ar)
