"""Text normalisation: digit sets, Arabic/Persian letter variants and the length-preserving guarantee."""
import random

from arjaa import norm


def test_norm_keeps_length_so_offsets_survive():
    rnd = random.Random(7)
    alphabet = "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩0123456789يكىیکابپ \u200cـ.،-"
    for _ in range(300):
        s = "".join(rnd.choice(alphabet) for _ in range(rnd.randint(0, 40)))
        assert len(norm.norm(s)) == len(s)


def test_digit_sets_and_letters_normalise_together():
    assert norm.ascii_digits("۱۲-٣٤") == "12-34"
    assert norm.key("كتـاب\u200cها  ۱") == norm.key("کتابها 1")
    assert norm.fa_digits("2-13") == "۲-۱۳"
