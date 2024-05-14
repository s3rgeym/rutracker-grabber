#!/usr/bin/env python
import argparse
import re
import sys
import time
from functools import partial
from itertools import count
from typing import Sequence, TextIO
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

__author__ = "Sergey M"
__license__ = "MIT"
__version__ = "0.1.0"

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


CSI = "\x1b["
RESET = f"{CSI}m"
CLEAR_LINE = f"{CSI}2K\r"
BLACK = f"{CSI}30m"
RED = f"{CSI}31m"
GREEN = f"{CSI}32m"
YELLOW = f"{CSI}33m"
BLUE = f"{CSI}34m"
MAGENTA = f"{CSI}35m"
CYAN = f"{CSI}36m"
WHITE = f"{CSI}37m"


echo = partial(print, file=sys.stderr, flush=True)


class NameSpace(argparse.Namespace):
    forum_url: str
    user_agent: str
    delay: float
    output: TextIO


def parse_args(argv: Sequence[str] | None) -> tuple[argparse.ArgumentParser, NameSpace]:
    parser = argparse.ArgumentParser(
        epilog='eg. %(prog)s "https://rutracker.org/forum/index.php?c=19"'
    )
    parser.add_argument("forum_url")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument("-d", "--delay", type=float, default=0.3)
    parser.add_argument("-o", "--output", type=argparse.FileType("w"), default="-")
    return parser, parser.parse_args(argv)


def get_session(args: NameSpace) -> requests.Session:
    session = requests.session()
    session.headers.update({"User-Agent": args.user_agent})
    return session


def get_soup(resp: requests.Response) -> BeautifulSoup:
    return BeautifulSoup(resp.text, "lxml")


def extract_category_urls(soup: BeautifulSoup, base_url: str) -> list[str]:
    return [
        urljoin(base_url, link["href"])
        for link in soup.find_all(href=re.compile(r"viewforum\.php\?f=\d+"))
    ]


def parse_category(sess: requests.Session, category_url: str, args: NameSpace):
    for start_param in count(0, step=50):
        url = category_url + (f"&start={start_param}" if start_param else "")
        echo(f"{GREEN}parse category: {url}{RESET}")
        try:
            time.sleep(args.delay)

            r = sess.get(url)
            # echo(r.text)

            soup = get_soup(r)
            topic_urls = extract_topic_urls(soup, r.url)

            parse_topic_urls(sess, topic_urls, args)

            if not has_next_page(soup):
                echo(f"{YELLOW}no more pages{RESET}")
                break
        except Exception as e:
            echo(f"{RED}{e=}{RESET}")


def extract_topic_urls(soup: BeautifulSoup, base_url) -> list[str]:
    return [urljoin(base_url, link["href"]) for link in soup.select("a.torTopic")]


def parse_topic_urls(
    sess: requests.Session, urls: list[str], args: NameSpace
) -> list[str]:
    for url in urls:
        echo(f"{GREEN}parse topic: {url}{RESET}")

        time.sleep(args.delay)

        try:
            r = sess.get(url)
            soup = get_soup(r)

            if link := soup.select_one('a[href^="magnet:"]'):
                print(link["href"], file=args.output, flush=True)
        except Exception as e:
            echo(f"{RED}{e=}{RESET}")


def has_next_page(soup: BeautifulSoup) -> bool:
    if last_link := soup.select_one("#pagination .pg:last-child"):
        return last_link.text == "След."
    return False


def main(argv: Sequence[str] | None = None):
    _, args = parse_args(argv)
    sess = get_session(args)

    # r = sess.get("https://rutracker.org/forum/index.php?map")
    # soup = get_soup(r)
    # for category_url in extract_category_urls(soup, sess.url):
    #     parse_category(sess, category_url, args)

    # https://rutracker.org/forum/index.php?c=19
    r = sess.get(args.forum_url)
    s = get_soup(r)
    for cat_url in extract_category_urls(s, r.url):
        parse_category(sess, cat_url, args)


if __name__ == "__main__":
    sys.exit(main())
