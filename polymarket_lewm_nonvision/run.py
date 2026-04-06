import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from polymarket_lewm.backtest import run_backtest
from polymarket_lewm.collect import run_collection
from polymarket_lewm.finetune import run_finetune
from polymarket_lewm.realtime import run_realtime_signals
from polymarket_lewm.infer import run_inference


parser = argparse.ArgumentParser()
parser.add_argument("command", choices=["collect", "finetune", "backtest", "infer", "signals", "selfcheck"])
args = parser.parse_args()

if args.command == "collect":
    result = run_collection()
elif args.command == "finetune":
    result = run_finetune()
elif args.command == "backtest":
    result = run_backtest()
elif args.command == "infer":
    result = run_inference()
elif args.command == "signals":
    result = run_realtime_signals()
else:
    import selfcheck
    selfcheck.main()
    raise SystemExit(0)

print(json.dumps(result, ensure_ascii=False, indent=2))
