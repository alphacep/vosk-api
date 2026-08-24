#!/usr/bin/env python

import argparse
import codecs
import srt
import logging
import sys
import itertools
import os

try:
    from collections.abc import MutableSequence
except ImportError:
    from collections import MutableSequence

PROG_NAME = os.path.basename(sys.argv[0]).replace("-", " ", 1)

STDIN_BYTESTREAM = getattr(sys.stdin, "buffer", sys.stdin)
STDOUT_BYTESTREAM = getattr(sys.stdout, "buffer", sys.stdout)

DASH_STREAM_MAP = {"input": STDIN_BYTESTREAM, "output": STDOUT_BYTESTREAM}

try:  # Python 2
    range = xrange  # pytype: disable=name-error
except NameError:
    pass

log = logging.getLogger(__name__)


def noop(stream):
    """
    Used when we didn't explicitly specify a stream to avoid using
    codecs.get{reader,writer}
    """
    return stream


def dash_to_stream(arg, arg_type):
    if arg == "-":
        return DASH_STREAM_MAP[arg_type]
    return arg


def basic_parser(
    description=None,
    multi_input=False,
    no_output=False,
    examples=None,
    hide_no_strict=False,
):
    example_lines = []

    if examples is not None:
        example_lines.append("examples:")

        for desc, code in examples.items():
            example_lines.append("  {}".format(desc))
            example_lines.append("    $ {}\n".format(code))

    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        description=description,
        epilog="\n".join(example_lines),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Cannot use argparse.FileType as we need to know the encoding from the
    # args

    if multi_input:
        parser.add_argument(
            "--input",
            "-i",
            metavar="FILE",
            action="append",
            type=lambda arg: dash_to_stream(arg, "input"),
            help="the files to process",
            required=True,
        )
    else:
        parser.add_argument(
            "--input",
            "-i",
            metavar="FILE",
            default=STDIN_BYTESTREAM,
            type=lambda arg: dash_to_stream(arg, "input"),
            help="the file to process (default: stdin)",
        )

    if not no_output:
        parser.add_argument(
            "--output",
            "-o",
            metavar="FILE",
            default=STDOUT_BYTESTREAM,
            type=lambda arg: dash_to_stream(arg, "output"),
            help="the file to write to (default: stdout)",
        )
        if not multi_input:
            parser.add_argument(
                "--inplace",
                "-p",
                action="store_true",
                help="modify file in place",
            )

    shelp = "allow blank lines in output, your media player may explode"
    if hide_no_strict:
        shelp = argparse.SUPPRESS

    parser.add_argument("--no-strict", action="store_false", dest="strict", help=shelp)
    parser.add_argument(
        "--debug",
        action="store_const",
        dest="log_level",
        const=logging.DEBUG,
        default=logging.INFO,
        help="enable debug logging",
    )

    parser.add_argument(
        "--ignore-parsing-errors",
        "-c",
        action="store_true",
        help="try to keep going, even if there are parsing errors",
    )

    parser.add_argument(
        "--encoding", "-e", help="the encoding to read/write files in (default: utf8)"
    )
    return parser


def set_basic_args(args):
    # TODO: dedupe some of this
    if getattr(args, "inplace", None):
        if args.input == DASH_STREAM_MAP["input"]:
            raise ValueError("Cannot use --inplace on stdin")

        if args.output != DASH_STREAM_MAP["output"]:
            raise ValueError("Cannot use -o and -p together")

        args.output = args.input

    for stream_name in ("input", "output"):
        log.debug('Processing stream "%s"', stream_name)

        try:
            stream = getattr(args, stream_name)
        except AttributeError:
            # For example, in the case of no_output
            continue

        # We don't use system default encoding, because usually one runs this
        # on files they got from elsewhere. As such, be opinionated that these
        # files are probably UTF-8. Looking for the BOM on reading allows us to
        # be more liberal with what we accept, without adding BOMs on write.
        read_encoding = args.encoding or "utf-8-sig"
        write_encoding = args.encoding or "utf-8"

        r_enc = codecs.getreader(read_encoding)
        w_enc = codecs.getwriter(write_encoding)

        log.debug("Got %r as stream", stream)
        # We don't use encoding= option to open because we want to have the
        # same universal newlines behaviour as STD{IN,OUT}_BYTESTREAM
        if stream in DASH_STREAM_MAP.values():
            log.debug("%s in DASH_STREAM_MAP", stream_name)
            if stream is args.input:
                args.input = srt.parse(
                    r_enc(args.input).read(), ignore_errors=args.ignore_parsing_errors
                )
            elif stream is args.output:
                # Since args.output is not in text mode (since we didn't
                # earlier know the encoding), we have no universal newline
                # support and need to do it ourselves
                args.output = w_enc(args.output)
        else:
            log.debug("%s not in DASH_STREAM_MAP", stream_name)
            if stream is args.input:
                if isinstance(args.input, MutableSequence):
                    for i, input_fn in enumerate(args.input):
                        if input_fn in DASH_STREAM_MAP.values():
                            if stream is args.input:
                                args.input[i] = srt.parse(
                                    r_enc(input_fn).read(),
                                    ignore_errors=args.ignore_parsing_errors,
                                )
                        else:
                            f = r_enc(open(input_fn, "rb"))
                            with f:
                                args.input[i] = srt.parse(
                                    f.read(), ignore_errors=args.ignore_parsing_errors
                                )
                else:
                    f = r_enc(open(stream, "rb"))
                    with f:
                        args.input = srt.parse(
                            f.read(), ignore_errors=args.ignore_parsing_errors
                        )
            else:
                args.output = w_enc(open(args.output, "wb"))


def compose_suggest_on_fail(subs, strict=True):
    try:
        return srt.compose(subs, strict=strict, eol=os.linesep, in_place=True)
    except srt.SRTParseError as thrown_exc:
        # Since `subs` is actually a generator
        log.critical(
            "Parsing failed, maybe you need to pass a different encoding "
            "with --encoding?"
        )
        raise


def sliding_window(seq, width=2, inclusive=True):
    """
    If inclusive is True, we also include final elements where len(sliced) <
    width.
    """
    seq_iter = iter(seq)

    # Consume seq_iter up to width
    sliced = tuple(itertools.islice(seq_iter, width))

    if not inclusive and len(sliced) != width:
        return

    yield sliced

    for elem in seq_iter:
        sliced = sliced[1:] + (elem,)
        yield sliced

    if inclusive:
        for idx in range(len(sliced)):
            if idx != 0:
                yield sliced[idx:]
