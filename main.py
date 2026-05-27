#!/usr/bin/env python3
"""AgentWorld Async — single entry point. World-agnostic.

  python main.py                               # multi-agent test (60s)
  python main.py --runtime 180 --validate      # 3min + validation
  python main.py --demo --world config/world_friends.yaml
  python main.py --eval-report trace.json
  python main.py --dashboard 8766              # data monitor
  python main.py --visual 8767                 # pixel frontend
"""
import sys, os, asyncio, argparse

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, "src"))


def parse_args():
    parser = argparse.ArgumentParser(description="AgentWorld Async")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--runtime", type=int, default=60)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--output", type=str, default="")
    parser.add_argument("--persist", type=str, default="")
    parser.add_argument("--validate-config", action="store_true")
    parser.add_argument("--world", type=str, default="")
    parser.add_argument("--eval-report", type=str, default="")
    parser.add_argument("--api-port", type=int, default=0)
    parser.add_argument("--dashboard", type=int, default=0, dest="dashboard_port")
    parser.add_argument("--visual", type=int, default=0, dest="visual_port")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose engine logging")
    return parser.parse_args()


def _cmd_eval(args):
    from eval import run_eval
    r = run_eval(args.eval_report)
    print(r.to_table())
    if args.output: r.save(args.output)


def _cmd_validate(args):
    from cli.commands import cmd_validate_config
    cmd_validate_config(args)


async def _cmd_demo(args):
    from cli.commands import cmd_demo
    await cmd_demo(args)


async def _cmd_test(args):
    from cli.commands import cmd_test
    await cmd_test(args)


# Registry: [(predicate, handler, is_async)]
_COMMANDS = [
    (lambda a: bool(a.eval_report),    _cmd_eval,    False),
    (lambda a: a.validate_config,       _cmd_validate, False),
    (lambda a: a.demo,                  _cmd_demo,    True),
    (lambda a: True,                    _cmd_test,    True),
]


async def main():
    args = parse_args()
    for predicate, handler, is_async in _COMMANDS:
        if predicate(args):
            if is_async:
                await handler(args)
            else:
                handler(args)
            return


if __name__ == "__main__":
    asyncio.run(main())
