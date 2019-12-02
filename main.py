from collections import Counter
import pathlib
import re
from typing import List

import attr
import pdftotext
from pyparsing import (
    Literal,
    Or,
    nums,
    SkipTo,
    MatchFirst,
    Word,
    Group,
    ZeroOrMore,
    ParserElement,
)

Integer = Word(nums)


@attr.s(auto_attribs=True)
class Record(object):
    type: str
    content: str


def preprocess(text: str) -> str:
    """Delete the page headers and trailers and blank lines from the text."""
    lines = text.splitlines()
    clean_lines = (
        l
        for l in lines
        if not re.match(r" *Page \d+ of \d+ *", l)
        and not l.startswith("file://")
        and l.strip()
    )
    return "\n".join(clean_lines)


TYPES = [Literal("SALE"), Literal("VOIDED")]


def header_line() -> ParserElement:
    header_single = (
        Literal("Type :")
        + Or(TYPES).setResultsName("type")
        + Literal("Trs# :")
        + Integer.setResultsName("trs")
    )
    header_split = (
        Literal("Type :")
        + Literal("Trs# :")
        + Or(TYPES).setResultsName("type")
        + Integer.setResultsName("trs")
    )
    return MatchFirst([header_single, header_split])


def date_line() -> ParserElement:
    date_single = (
        Literal("Date :")
        + Word("1234567890-").setResultsName("date")
        + Literal("Invoice# :")
        + Integer.setResultsName("invoice")
    )
    date_split = (
        Literal("Date :")
        + Literal("Invoice# :")
        + Word("1234567890-").setResultsName("date")
        + Integer.setResultsName("invoice")
    )
    return MatchFirst([date_single, date_split]).setDebug()


def split_into_records(text: str) -> List[Record]:
    balance = Literal("BALANCE") + Word("-$1234567890.")
    record = Group(
        header_line() + SkipTo(balance, include=True).setResultsName("content")
    )
    file = ZeroOrMore(record)
    file.setDefaultWhitespaceChars(" \t")
    ret = []
    for r in file().parseString(text):
        ret.append(Record(type=r["type"], content=r["content"]))
    return ret


if __name__ == "__main__":
    p = pathlib.Path("input.pdf")
    with p.open("rb") as file:
        pdf = pdftotext.PDF(file)
        doc = "\n".join(page for page in pdf)
    prep = preprocess(doc)
    records = split_into_records(prep)
    print(f"{len(records)} records found")
    print(Counter(r.type for r in records))
