#!/usr/bin/env python3
import argparse
import csv
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path

SCENARIOS = {"A": 30, "B": 80, "C": 150}
PROFILES = {"leitura": "ReadProfile", "escrita": "WriteProfile"}
RAW = Path("results/raw")


def get_python_exe():
    try:
        import locust  # noqa: F401
        return sys.executable
    except ImportError:
        pass

    venv_py = Path(__file__).resolve().parent / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def wait_until_ready(host, timeout=300):
    urls = [f"{host}/api/customer/owners/1", f"{host}/api/vet/vets"]
    deadline, streak = time.time() + timeout, 0
    while time.time() < deadline:
        try:
            good = all(urllib.request.urlopen(u, timeout=5).status == 200 for u in urls)
        except Exception:
            good = False
        streak = streak + 1 if good else 0
        if streak >= 3:
            return True
        time.sleep(3)
    return False


def restart_customers_service():
    print("  reiniciando customers-service...")
    try:
        res = subprocess.run(["docker", "restart", "customers-service"], capture_output=True, text=True)
        if res.returncode == 0:
            time.sleep(8)
            return True

        ps = subprocess.run(
            ["docker", "ps", "--filter", "name=customers-service", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        names = [n.strip() for n in ps.stdout.strip().splitlines() if n.strip()]
        if names:
            subprocess.run(["docker", "restart", names[0]], capture_output=True)
            time.sleep(8)
            return True
        else:
            print("  [aviso] Container 'customers-service' nao encontrado em docker ps.")
            return False
    except FileNotFoundError:
        sys.exit("ERRO: comando `docker` nao encontrado. Abra o Docker Desktop e um novo terminal.")


def parse_mem_mb(text):
    used = text.split("/")[0].strip()
    for unit, factor in (("GiB", 1024), ("MiB", 1), ("KiB", 1 / 1024), ("B", 1 / 1048576)):
        if used.endswith(unit):
            try:
                return round(float(used[: -len(unit)]) * factor, 1)
            except ValueError:
                return 0.0
    return 0.0


def monitor_docker(stop, path, t0):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["t", "container", "cpu_percent", "mem_mb"])
        while not stop.is_set():
            try:
                out = subprocess.run(
                    ["docker", "stats", "--no-stream", "--format", "{{.Name}};{{.CPUPerc}};{{.MemUsage}}"],
                    capture_output=True, text=True, timeout=30,
                ).stdout
            except Exception:
                out = ""
            t = round(time.time() - t0, 1)
            for line in out.strip().splitlines():
                try:
                    parts = line.split(";")
                    if len(parts) >= 3:
                        name, cpu, mem = parts[0], parts[1], parts[2]
                        cpu_val = float(cpu.strip().rstrip("%"))
                        mem_val = parse_mem_mb(mem)
                        w.writerow([t, name, cpu_val, mem_val])
                except (ValueError, IndexError):
                    continue
            f.flush()
            stop.wait(1)


def run_one(scenario, profile, rep, args, py_exe):
    users = SCENARIOS[scenario]
    outdir = RAW / f"{scenario}_{profile}_rep{rep:02d}"
    if (outdir / "DONE").exists():
        print(f"[skip] {outdir.name} ja concluida")
        return
    outdir.mkdir(parents=True, exist_ok=True)

    should_restart = False
    if args.restart_policy == "always":
        should_restart = True
    elif args.restart_policy == "escrita_only" and profile == "escrita":
        should_restart = True

    if should_restart:
        restart_customers_service()

    if not wait_until_ready(args.host):
        sys.exit("ERRO: aplicacao nao ficou pronta (confira `docker ps` e http://localhost:8761).")

    total = args.warmup + args.duration
    meta = dict(
        scenario=scenario, profile=profile, rep=rep, users=users,
        warmup=args.warmup, duration=args.duration, host=args.host,
        start=datetime.now().isoformat(timespec="seconds")
    )
    (outdir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    cmd = [
        py_exe, "-m", "locust", "-f", "locustfile.py", PROFILES[profile], "--headless",
        "-u", str(users), "-r", str(args.spawn_rate), "--run-time", f"{total}s",
        "--host", args.host, "--csv", str(outdir / "locust"), "--only-summary"
    ]
    env = {**os.environ, "WARMUP_SECONDS": str(args.warmup)}

    stop, t0 = threading.Event(), time.time()
    th = threading.Thread(target=monitor_docker, args=(stop, outdir / "cpu.csv", t0), daemon=True)
    th.start()
    try:
        with open(outdir / "locust.log", "w", encoding="utf-8") as log:
            subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
    finally:
        stop.set()
        th.join(timeout=40)

    if (outdir / "locust_stats.csv").exists():
        (outdir / "DONE").write_text("ok", encoding="utf-8")
        print(f"  ok -> {outdir}")
    else:
        print(f"  FALHOU (veja {outdir/'locust.log'})")


def main():
    ap = argparse.ArgumentParser(description="Executa os testes de carga do Spring PetClinic com Locust.")
    ap.add_argument("--reps", type=int, default=10, help="Quantidade de repetições por configuração (padrão: 10)")
    ap.add_argument("--scenarios", nargs="+", default=list(SCENARIOS), choices=list(SCENARIOS), help="Cenários a executar (A, B, C)")
    ap.add_argument("--profiles", nargs="+", default=list(PROFILES), choices=list(PROFILES), help="Perfis a executar (leitura, escrita)")
    ap.add_argument("--host", default="http://localhost:8080", help="URL do API Gateway (padrão: http://localhost:8080)")
    ap.add_argument("--warmup", type=int, default=60, help="Duração do aquecimento em segundos (padrão: 60s)")
    ap.add_argument("--duration", type=int, default=360, help="Duração medida em segundos (padrão: 360s)")
    ap.add_argument("--spawn-rate", type=int, default=10, help="Taxa de criação de usuários por segundo (padrão: 10)")
    ap.add_argument("--cooldown", type=int, default=20, help="Pausa entre execuções em segundos (padrão: 20s)")
    ap.add_argument("--restart-policy", choices=["always", "escrita_only", "none"], default="always",
                    help="Política de reinicialização do customers-service: 'always', 'escrita_only' ou 'none'")
    ap.add_argument("--no-restart", action="store_true", help="Atalho para --restart-policy none")
    args = ap.parse_args()

    if args.no_restart:
        args.restart_policy = "none"

    py_exe = get_python_exe()
    runs = [(r, s, p) for r in range(1, args.reps + 1) for s in args.scenarios for p in args.profiles]
    est_h = len(runs) * (args.warmup + args.duration + args.cooldown + 10) / 3600
    print(f"Python: {py_exe}")
    print(f"{len(runs)} execuções planejadas (~{est_h:.1f} h).")

    try:
        for i, (rep, scen, prof) in enumerate(runs, 1):
            print(f"[{i}/{len(runs)}] Cenário {scen} ({SCENARIOS[scen]} usuários) | Perfil {prof} | Repetição {rep}")
            run_one(scen, prof, rep, args, py_exe)
            time.sleep(args.cooldown)
        print("\nExecuções finalizadas com sucesso.")
    except KeyboardInterrupt:
        print("\n\nExecução interrompida pelo usuário.")
        sys.exit(0)


if __name__ == "__main__":
    main()
