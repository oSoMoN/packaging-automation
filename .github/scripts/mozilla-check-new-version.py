#!/usr/bin/python3

import argparse
import copy
import json
import logging
import lxml.html
import os.path
import sys
from http import HTTPStatus
from packaging import version
from urllib import request
from urllib.parse import urlencode


ROOT_URL = "http://ftp.mozilla.org/pub/{product}/candidates/"
CANDIDATES_FILE = "{product}-candidates.json"
BETA = "beta"
RELEASE = "release"
ESR = "esr"
VERSION = "version"
BUILD = "build"
TG_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_tg_message(tg_token, tg_chat_id, text):
    data = urlencode({"chat_id": tg_chat_id,
                      "text": text,
                      "parse_mode": "Markdown"}).encode()
    request.urlopen(request.Request(TG_URL.format(token=tg_token), data))


def get_latest_build(product, candidate):
    result = request.urlopen(
        ROOT_URL.format(product=product) + candidate + "-candidates/")
    if result.getcode() != HTTPStatus.OK:
        logging.error("failed to fetch the list of builds for {}"
                      .format(candidate))
        return 0
    builds = lxml.html.fromstring(result.read())
    builds = builds.xpath("//a[contains(@href,'-candidates/build')]/text()")
    builds.sort()
    return builds[-1][:-1]


def test_version(product, versions, candidate, channel):
    v = version.parse(candidate)
    ov = version.parse(versions[channel][VERSION])
    if v >= ov:
        build = get_latest_build(product, candidate)
        if v > ov or build > versions[channel][BUILD]:
            versions[channel][VERSION] = candidate
            versions[channel][BUILD] = build
            return True
    return False


def send_new_candidate_message(tg_token, tg_chat_id, versions, channel):
    cname = {RELEASE: "release", ESR: "ESR", BETA: "beta"}[channel]
    c = versions[channel]
    url = "{}{}-candidates/{}/".format(ROOT_URL, c[VERSION], c[BUILD])
    send_tg_message(tg_token, tg_chat_id, "New {} candidate: [{} {}]({})"
                    .format(cname, c[VERSION], c[BUILD], url))


def check_new_candidates(product, tg_token, tg_chat_id):
    result = request.urlopen(ROOT_URL.format(product=product))
    if result.getcode() != HTTPStatus.OK:
        sys.exit("failed to fetch list of candidates")
    candidates = lxml.html.fromstring(result.read())
    candidates = candidates.xpath("//a[contains(@href,'-candidates/')]/text()")
    candidates = [c[:-12] for c in candidates if not c.startswith("None")]
    empty = {VERSION: "", BUILD: ""}
    versions = {RELEASE: copy.deepcopy(empty),
                ESR: copy.deepcopy(empty),
                BETA: copy.deepcopy(empty)}
    updates = {RELEASE: False, ESR: False, BETA: False}
    candidates_file = CANDIDATES_FILE.format(product=product)
    if os.path.isfile(candidates_file):
        with open(candidates_file, "r") as f:
            try:
                versions = json.load(f)
            except json.decoder.JSONDecodeError:
                pass
    for candidate in candidates:
        if candidate.endswith("esr"):
            updates[ESR] |= test_version(product, versions, candidate, ESR)
        elif "b" in candidate:
            updates[BETA] |= test_version(product, versions, candidate, BETA)
        else:
            updates[RELEASE] |= test_version(
                product, versions, candidate, RELEASE)
    logging.info("{} versions: {}".format(product, versions))
    logging.info("{} updates: {}".format(product, updates))
    with open(candidates_file, "w") as f:
        json.dump(versions, f)
    if updates[RELEASE]:
        send_new_candidate_message(tg_token, tg_chat_id, versions, RELEASE)
    if updates[ESR]:
        send_new_candidate_message(tg_token, tg_chat_id, versions, ESR)
    if updates[BETA]:
        send_new_candidate_message(tg_token, tg_chat_id, versions, BETA)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    parser = argparse.ArgumentParser(
        description='Check for new versions for Mozilla products ' +
        '(Firefox and Thunderbird)')
    parser.add_argument('product', type=str,
                        choices=['firefox', 'thunderbird'], help='the product')
    parser.add_argument('--tg-token', help='Telegram bot authentication token',
                        type=str, required=True)
    parser.add_argument('--tg-chat-id', help='Telegram user to target',
                        type=str, required=True)
    args = parser.parse_args()
    check_new_candidates(args.product, args.tg_token, args.tg_chat_id)
