import json
from pathlib import Path
from handoff_runtime import verify_handoff_result

logs = Path('/logs/agent')
out = Path('/logs/verifier')
out.mkdir(parents=True, exist_ok=True)
receipt = {'passed': False, 'valid': False, 'error_type': None}
try:
    case = json.loads(Path('/tests/case.json').read_text())
    result = json.loads((logs / 'handoff-result.json').read_text())
    handoff = json.loads((logs / 'handoff.json').read_text())
    finalized = json.loads((logs / 'runtime-finalized.json').read_text())
    oracle = verify_handoff_result(case, result, handoff)
    native = result['native_verify']
    valid = result['valid'] is True and finalized['exports_complete'] is True
    passed = valid and oracle['passed'] and bool(native) and native[-1]['action'] == 'turn.verify.passed' and native[-1].get('success') is True
    receipt.update(passed=bool(passed), valid=valid, oracle=oracle, native_verify=native)
except Exception as error:
    receipt['error_type'] = type(error).__name__
(out / 'verifier-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2))
(out / 'reward.txt').write_text('1' if receipt['passed'] else '0')
