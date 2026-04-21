"""PocketLang CLI entry point.

Usage:
    python pocketlang.py run prog.pcalc
    python pocketlang.py run prog.pcalc --no-opt
    python pocketlang.py run prog.pcalc --debug
    python pocketlang.py run prog.pcalc --debug=tokens,ast,symtab,ir,opt
"""

from __future__ import annotations

import argparse
import sys

ALL_PHASES = ("tokens", "ast", "symtab", "ir", "opt")


def _parse_debug(value: str | None) -> set[str]:
    if value is None:
        return set()
    if value == "":  # bare --debug
        return set(ALL_PHASES)
    parts = {p.strip() for p in value.split(",") if p.strip()}
    unknown = parts - set(ALL_PHASES)
    if unknown:
        print(f"Unknown debug phase(s): {', '.join(sorted(unknown))}", file=sys.stderr)
        print(f"Available: {', '.join(ALL_PHASES)}", file=sys.stderr)
        sys.exit(2)
    return parts


def cmd_run(args) -> int:
    from src.cli.debug_dump import dump_ast, dump_ir, dump_symtab, dump_tokens
    from src.errors import PocketError, format_error
    from src.interpreter import VM
    from src.ir import IRGenerator
    from src.lexer import Lexer
    from src.optimizer import optimize
    from src.parser import Parser
    from src.semantic import SemanticAnalyzer

    debug = _parse_debug(args.debug)

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        print(f"error: cannot read {args.file}: {e}", file=sys.stderr)
        return 1

    try:
        lexer = Lexer(source, filename=args.file)
        tokens = lexer.tokenize()
        if "tokens" in debug:
            print(dump_tokens(tokens))

        parser = Parser(tokens, filename=args.file)
        program = parser.parse()
        if "ast" in debug:
            print(dump_ast(program))

        analyzer = SemanticAnalyzer()
        analyzer.analyze(program)
        if "symtab" in debug:
            print(dump_symtab(analyzer.symtab))

        irgen = IRGenerator()
        instrs, func_table = irgen.generate(program)
        if "ir" in debug:
            print(dump_ir(instrs, title="TAC (unoptimized)"))

        no_opt = getattr(args, "no_opt", False)
        if not no_opt:
            if "opt" in debug:
                def sink(pass_name: str, cur: list) -> None:
                    print(dump_ir(cur, title=f"TAC after {pass_name}"))

                instrs = optimize(instrs, debug_sink=sink)
            else:
                instrs = optimize(instrs)

        if "ir" in debug and not no_opt:
            print(dump_ir(instrs, title="TAC (optimized)"))

        vm = VM()
        vm.run(instrs, func_table)
        return 0

    except PocketError as e:
        print(format_error(e, args.file, source), file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pocketlang", description="PocketLang compiler/interpreter")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run a .pcalc program")
    run_p.add_argument("file", help="Path to .pcalc source file")
    run_p.add_argument(
        "--no-opt",
        action="store_true",
        help="Skip optimization (run unoptimized TAC; useful for tests / comparisons).",
    )
    run_p.add_argument(
        "--debug",
        nargs="?",
        const="",
        default=None,
        help="Enable debug dumps. Bare --debug enables all; or pass comma-separated list: "
        "tokens,ast,symtab,ir,opt",
    )
    run_p.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
