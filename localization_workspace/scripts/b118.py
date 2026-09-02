# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(os.path.dirname(__file__)))
from _apply import apply

ar = [
"أنت حرّ في الذهاب.",
"لقد عدت.",
"لقد عدت؟",
"أنت… أنت فعلتَ هذا.",
"من أجل عودتي الظافرة.",
"«ينبغي أن يُرى الخادم الصالح… لا أن يُسمع».",
"…أُطيل إقامتي.",
"…كسولون، بسطاء، و…",
"…خادمي المتواضع.",
]

apply(118, ar)
