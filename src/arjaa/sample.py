"""Synthetic thesis for --demo and the tests (invented text, invented authors; not from any real thesis).

``thesis(path, flawed=True)`` writes a three-chapter .docx with the usual cross-reference accidents of a thesis edited for a
year (figures renumbered by hand, a pasted caption, a deleted figure that is still mentioned, a reference list that
drifted from the text). The clean version has none of them.
"""
from __future__ import annotations

from .docxbuild import Doc, run_xml, field_runs

FONT, SZ = "B Nazanin", 28


def seq_caption(d: Doc, label: str, chapter: str, n: str, title: str, seq: str = "Figure", typed: bool = False):
    if typed:
        raw = run_xml(f"{label} {chapter}-{n}: {title}")
    else:
        raw = run_xml(f"{label} {chapter}-") + field_runs(f"SEQ {seq} \\* ARABIC", n) + run_xml(f": {title}")
    d.p(style="Caption", raw=raw)


def para(d: Doc, *parts, live: bool = False):
    """Text with in-text mentions; with live=True the tuples ("شکل ۲-۱",) become REF cross-reference fields."""
    raw = ""
    k = 100
    for x in parts:
        if isinstance(x, tuple):
            k += 1
            raw += field_runs(f"REF _Ref{k} \\h", x[0]) if live else run_xml(x[0])
        else:
            raw += run_xml(x)
    d.p(raw=raw)


def thesis(path: str, flawed: bool = True) -> str:
    F = flawed
    L = not F
    d = Doc(cs_font=FONT, szcs=SZ)
    d.heading("چکیده", 1)
    d.p("در این پژوهش عملکرد چند الگوریتم خوشه‌بندی برای داده‌های حسگرهای محیطی بررسی شده است.")
    # ------------------------------------------------------------ chapter 1
    d.heading("فصل اول: مقدمه", 1)
    d.p("خوشه‌بندی داده‌های حسگر در سال‌های اخیر مورد توجه بوده است (رضایی و کریمی، ۱۳۹۸؛ Smith & Lee, 2020).")
    d.p("نخستین بار این مسئله را اسمیت و لی (۲۰۲۰) در شبکه‌های حسگر بی‌سیم مطرح کردند." if False else
        "ساختار پایان‌نامه به این شرح است: مبانی نظری در فصل دوم و روش پژوهش در فصل سوم می‌آید" + (" و نتایج در فصل ۷ گزارش می‌شود." if F else "."))
    d.p("برای ارزیابی، یک مجموعه‌داده‌ی حسگر دما با ۱۲۰ نمونه به کار رفت (Brown, 2018)" + ("، و برآورد خطا طبق (Brown, 2031) انجام شد." if F else "."))
    # ------------------------------------------------------------ chapter 2
    d.heading("فصل دوم: مبانی نظری", 1)
    para(d, "همان‌طور که در ", ("شکل ۲-۱",), " دیده می‌شود، خوشه‌های میانی بیشترین پراکندگی را دارند.", live=L)
    d.picture()
    if F:
        seq_caption(d, "شکل", "۲", "۱", "پراکندگی خوشه‌ها")
    else:
        seq_caption(d, "شکل", "۲", "۱", "پراکندگی خوشه‌ها")
    d.p("پژوهش‌های پیشین نشان می‌دهد که الگوریتم‌ها به داده‌های پرت حساس هستند (احمدی، " + ("۱۴۰۱" if F else "۱۴۰۰") + ").")
    d.picture()
    seq_caption(d, "شکل", "۲", "۲", "نمودار خطا بر حسب تعداد خوشه")
    if L:
        para(d, "خطا بر حسب تعداد خوشه در ", ("شکل ۲-۲",), " آمده است.", live=True)
    d.p("روش پیشنهادی از رویکرد اسمیت و همکاران (Smith et al., 2020) پیروی می‌کند" + (" و در " + "(Johnson, 2017)" + " نیز آمده است." if F else "."))
    if F:
        d.p("نتیجه‌ی مقایسه‌ی دو روش در شکل ۲-۳ و نمودار ۲-۱ نشان داده شده است.")
        d.picture()
        seq_caption(d, "شکل", "۲", "۴", "مقایسه‌ی دو روش", typed=True)
    else:
        para(d, "نتیجه‌ی مقایسه‌ی دو روش در ", ("شکل ۲-۳",), " نشان داده شده است.", live=True)
        d.picture()
        seq_caption(d, "شکل", "۲", "۳", "مقایسه‌ی دو روش")
    para(d, "ویژگی‌های حسگرها در ", ("جدول ۲-۱",), " آمده است. ", "رضایی و همکاران (۱۳۹۸) نیز همین رده‌بندی را به کار برده‌اند.", live=L)
    seq_caption(d, "جدول", "۲", "۱", "ویژگی‌های حسگرها", seq="Table")
    d.table([["نوع حسگر", "دقت", "بازه"], ["دما", "۹۸", "۱۰۰"], ["رطوبت", "۹۵", "۸۰"]], bidi_visual=True)
    # ------------------------------------------------------------ chapter 3
    d.heading("فصل سوم: روش پژوهش", 1)
    para(d, "جریان کلی روش در ", ("شکل ۳-۱",), " آمده است.", live=L)
    d.picture()
    seq_caption(d, "شکل", "۳", "۱", "جریان کلی روش")
    if F:
        d.picture()
        seq_caption(d, "شکل", "۳", "۱", "ساختار شبکه‌ی حسگر", typed=True)
    else:
        para(d, "ساختار شبکه در ", ("شکل ۳-۲",), " دیده می‌شود.", live=True)
        d.picture()
        seq_caption(d, "شکل", "۳", "۲", "ساختار شبکه‌ی حسگر")
    para(d, "پارامترهای آزمایش در ", ("جدول " + ("۲-۲" if F else "۳-۱"),), " فهرست شده است.", live=L)
    seq_caption(d, "جدول", "۲" if F else "۳", "۲" if F else "۱", "پارامترهای آزمایش", seq="Table", typed=F)
    d.table([["پارامتر", "مقدار"], ["تعداد خوشه", "۵"], ["تکرار", "۳۰"]], bidi_visual=True)
    d.p("نتایج با میانگین سی اجرا گزارش می‌شود و روش مقایسه‌ی دو گروه در " + ("(Smith & Lee, 2020)" if True else "") + " شرح داده شده است.")
    # ------------------------------------------------------------ references
    d.heading("فهرست منابع", 1)
    refs = [
        "رضایی، علی و کریمی، سارا (۱۳۹۸). خوشه‌بندی داده‌های حسگر در شبکه‌های بی‌سیم. مجله‌ی پژوهش‌های داده، ۱۲(۳)، ۴۵–۶۰.",
        "احمدی، مریم (۱۴۰۰). مبانی تشخیص داده‌های پرت. تهران: انتشارات نمونه.",
        "Smith, J., & Lee, K. (2020). Clustering streaming sensor data. Journal of Sensor Studies, 10(2), 100–115.",
        "Brown, T. (2018). Calibrating low-cost temperature sensors. Sensor Notes, 4(1), 1–9.",
    ]
    if F:
        refs += [
            "Brown, T. (2018). Calibrating low-cost temperature sensors. Sensor Notes, 4(1), 1–9.",
            "Miller, A. (1399). Outlier handling in clustering. Data Letters, 3(4), 20–31.",
            "Wang, L. (2019). A survey of density-based clustering. Survey Quarterly, 7(1), 5–40.",
            "کاظمی، حسین (2019). مقایسه‌ی روش‌های خوشه‌بندی. پایان‌نامه‌ی کارشناسی ارشد، دانشگاه نمونه.",
        ]
    for r in refs:
        d.p(r, jc="left" if r[0].isascii() else None, bidi=False if r[0].isascii() else None)
    if F:
        d.p("Zhou, Q. (2032). Forthcoming results on sensor drift. Preprint.", bidi=False, jc="left")
    d.heading("Abstract", 1)
    d.p("This thesis compares several clustering algorithms on environmental sensor data.", bidi=False, jc="left")
    return d.save(path)
