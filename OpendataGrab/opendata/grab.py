#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
opendata-grab -- Download new files from opendata.dwd.de

grab is a script comparing log-files from
https://opendata.dwd.de and downloading all new files.

Distributed on an "AS IS" basis without warranties
or conditions of any kind, either express or implied.

@author:     DWD/amaul

@copyright:  2017 Deutscher Wetterdienst (DWD). All rights reserved.

@license:    GNU GENERAL PUBLIC LICENSE Vers.3

@contact:    opendata@dwd.de
"""
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from bz2 import BZ2File, decompress
from logging import handlers
import logging
import os.path
import sys
from requests import Session

__version__ = "0.1"
__date__ = "2017-07-20"
__updated__ = "2017-07-26"

URL_OPENDATA = "http://opendata.dwd.de"
CONTENT = "content.log.bz2"

logger = logging.getLogger("opendata_grab")

def compare_content(dest_path, folder=None, from_date=None):
    """Download content.log from folder and compare with that on disk."""
    if folder is not None:
        fname = os.path.join(dest_path, "weather", folder, CONTENT)
        url = "/".join((URL_OPENDATA, "weather", folder, CONTENT))
    else:
        fname = os.path.join(dest_path, "weather", CONTENT)
        url = "/".join((URL_OPENDATA, "weather", CONTENT))
    content_last = set()
    content_new = set()
    try:
        with BZ2File(fname, mode="r") as fh:
            for line in fh.readlines():
                content_last.add(line.rstrip())
    except:
        pass
    logger.info("last content.log: %d lines", len(content_last))
    sess = Session()
    try:
        if url.startswith("https"):
            sess.verify = False
        resp = sess.get(url, stream=True)
        if httpresponse(resp):
            content_buf = resp.content
            from codecs import decode
            for line in decompress(content_buf).splitlines():
                sline = decode(line)
                if CONTENT in sline:
                    continue
                date_ok = True
                parts = sline.split("|")
                if from_date is not None:
                    dtg = parts[-1].split(" ")
                    if dtg[0] < from_date:
                        date_ok = False
                if date_ok and sline not in content_last:
                        if folder is not None:
                            content_new.add(os.path.join("weather", folder, parts[0][2:]))
                        else:
                            content_new.add(os.path.join("weather", parts[0][2:]))
            logger.info("new content.log: %d lines", len(content_new))
            dir_name = os.path.dirname(fname)
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
            with open(fname, "wb") as fd:
                fd.write(content_buf)
    except:
        logger.error("request/compare content.log failed", exc_info=True)
        return None
    finally:
        sess.close()
    return content_new

def download_files(dest_path, file_list):
    """Download all files listed from opendata."""
    i = 0
    with Session() as sess:
        if URL_OPENDATA.startswith("https"):
            sess.verify = False
        for file_name in file_list:
            resp = sess.get("/".join((URL_OPENDATA, file_name)), stream=True)
            if httpresponse(resp):
                full_name = os.path.join(dest_path, file_name)
                dir_name = os.path.dirname(full_name)
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)
                with open(full_name, 'wb') as fh:
                    for chunk in resp.iter_content(chunk_size=8200, decode_unicode=False):
                        fh.write(chunk)
                i += 1
    return i

def httpresponse(response, text=""):
    r = False
    if response.status_code < 200 or response.status_code >= 300:
        logger.warn("HTTP %s %s : %s", response.status_code, response.reason, text)
    else:
        logger.debug("HTTP %s %s", response.status_code, response.reason)
        r = True
    logger.debug("Response headers: %s", response.headers)
    return r

def parse_args():
    """Command line options."""
#     program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = "%%(prog)s %s (%s)" % (program_version, program_build_date)
    program_shortdesc = __import__("__main__").__doc__.split("\n")[1]
    program_license = """%s

USAGE
""" % (program_shortdesc)
    # Setup argument parser
    parser = ArgumentParser(description=program_license,
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-V",
                        "--version",
                        action="version",
                        version=program_version_message)
    parser.add_argument("-v",
                        "--verbose",
                        dest="verbose",
                        action="count",
                        help="set verbosity level [default: 0]")
    parser.add_argument("--log",
                        help="path for log-files",
                        metavar="DIR")
    parser.add_argument("-f",
                        "--from",
                        dest="from_date",
                        help="download only files later than this date [yyyy-mm-dd].",
                        metavar="DATE")
    parser.add_argument("-d",
                        "--destination",
                        dest="destination",
                        help="save all files in DIR [default: $PWD]",
                        metavar="DIR",
                        default=os.getcwd())
    parser.add_argument(dest="folders",
                        help="folder(s) below 'weather' with data file(s)",
                        metavar="path",
                        nargs="*")
    # Process arguments
    args = parser.parse_args()
    # Setup logging
    if not args.verbose:
        loglevel = logging.WARN
    else:
        if args.verbose == 1:
            loglevel = logging.INFO
        elif args.verbose >= 2:
            loglevel = logging.DEBUG
    if args.log:
        previous = os.path.exists(args.log)
        handler = handlers.RotatingFileHandler(args.log, backupCount=5)
        if previous:
            handler.doRollover()
    else:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s: %(asctime)s :"
                                           " %(name)s] %(message)s",
                                           "%Y-%m-%d %H:%M:%S"))
    handler.setLevel(loglevel)
    logging.getLogger("").setLevel(loglevel)
    logging.getLogger("").addHandler(handler)
    logger.debug(args)
    return args

def main(argv=None):
    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)
    args = parse_args()
    if not len(args.folders):
        args.folders = [None]
    try:
        for folder in args.folders:
            logger.debug("opendata folder '%s'", folder)
            file_list = compare_content(args.destination, folder, args.from_date)
            cnt = download_files(args.destination, file_list)
            logger.info("downloaded %d files", cnt)
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0

if __name__ == "__main__":
    sys.exit(main())
