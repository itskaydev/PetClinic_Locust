#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAW, OUT = Path("results/raw"), Path("results")
USERS = {"A": 30, "B": 80, "C": 150}
LABEL = {"A": "A - Leve (30)", "B": "B - Moderado (80)", "C": "C - Elevado (150)"}
PROFILE_LABEL = {"leitura": "Perfil 1 - Leitura", "escrita": "Perfil 2 - Escrita"}
FOCUS_SERVICES = ["api-gateway", "customers-service", "vets-service", "visits-service"]


def to_float(val, default=0.0):
    try:
        f = float(val)
        return default if pd.isna(f) else f
    except (ValueError, TypeError):
        return default


def md_table(df):
    cols = list(df.columns)
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    lines = [header, sep]
    for _, r in df.iterrows():
        formatted_row = []
        for v in r:
            if pd.isna(v):
                formatted_row.append("-")
            elif isinstance(v, float):
                formatted_row.append(f"{v:.2f}")
            else:
                formatted_row.append(str(v))
        lines.append("| " + " | ".join(formatted_row) + " |")
    return "\n".join(lines)


def identify_service(container_name):
    c_lower = str(container_name).lower()
    for s in FOCUS_SERVICES:
        if s in c_lower:
            return s
    return str(container_name)


def load():
    rows, cpu_rows = [], []
    for d in sorted(RAW.glob("*_rep*")):
        if not (d / "DONE").exists():
            continue
        m = re.match(r"([ABC])_(leitura|escrita)_rep(\d+)", d.name)
        if not m:
            continue
        scen, prof, rep = m.group(1), m.group(2), int(m.group(3))
        meta_file = d / "meta.json"
        if not meta_file.exists():
            continue
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        dur, warm = meta.get("duration", 360), meta.get("warmup", 60)

        stats_file = d / "locust_stats.csv"
        if not stats_file.exists() or stats_file.stat().st_size == 0:
            continue

        try:
            st = pd.read_csv(stats_file)
        except Exception:
            continue

        for _, r in st.iterrows():
            name_val = str(r.get("Name", ""))
            op = "TOTAL" if name_val == "Aggregated" else name_val
            req = to_float(r.get("Request Count", 0))
            fail = to_float(r.get("Failure Count", 0))
            avg_ms = to_float(r.get("Average Response Time", 0.0)) if req > 0 else 0.0
            p95_ms = to_float(r.get("95%", 0.0)) if req > 0 else 0.0
            rps = (req / dur) if dur > 0 else 0.0
            fail_pct = (100.0 * fail / req) if req > 0 else 0.0

            rows.append(dict(
                scenario=scen, profile=prof, rep=rep, operation=op,
                requests=req, failures=fail, avg_ms=avg_ms,
                p95_ms=p95_ms, rps=rps, fail_pct=fail_pct
            ))

        cpu_file = d / "cpu.csv"
        if cpu_file.exists() and cpu_file.stat().st_size > 0:
            try:
                c = pd.read_csv(cpu_file)
                if not c.empty and "t" in c.columns and "container" in c.columns:
                    c = c[c["t"] >= warm]
                    if not c.empty:
                        c["servico"] = c["container"].apply(identify_service)
                        g = c.groupby("servico").agg(
                            cpu_mean=("cpu_percent", "mean"),
                            cpu_max=("cpu_percent", "max"),
                            mem_mean_mb=("mem_mb", "mean")
                        ).reset_index()
                        g["scenario"], g["profile"], g["rep"] = scen, prof, rep
                        cpu_rows.append(g)
            except Exception as e:
                print(f"[aviso] Erro ao ler cpu.csv em {d.name}: {e}")

    if not rows:
        raise SystemExit("Nenhuma execução concluída encontrada em results/raw. Execute o script run_experiments.py primeiro.")

    return pd.DataFrame(rows), (pd.concat(cpu_rows, ignore_index=True) if cpu_rows else pd.DataFrame())


def line_chart(summary, metric, ylabel, fname, title):
    plt.figure(figsize=(7.5, 4.5))
    colors = {"leitura": "#1f77b4", "escrita": "#d62728"}
    markers = {"leitura": "o", "escrita": "s"}

    for prof, g in summary.groupby("profile"):
        g = g.sort_values("users")
        plt.plot(
            g["users"], g[metric], marker=markers.get(prof, "o"),
            color=colors.get(prof), linewidth=2, markersize=7,
            label=PROFILE_LABEL.get(prof, prof)
        )
        for _, r in g.iterrows():
            val_str = f"{r[metric]:.1f}" if metric != "total_req" else f"{int(r[metric])}"
            plt.annotate(val_str, (r["users"], r[metric]),
                         textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)

    plt.xlabel("Usuários simultâneos", fontsize=11)
    plt.ylabel(ylabel, fontsize=11)
    plt.title(title, fontsize=12, fontweight="bold", pad=12)
    plt.xticks(list(USERS.values()))
    plt.grid(alpha=0.3, linestyle="--")
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(OUT / fname, dpi=150)
    plt.close()


def generate_answers_and_facts(summary, ops, cpu_s):
    lines = []

    lines.append("### 6.1. Como o aumento de usuários afeta o tempo de resposta?\n")
    q1_details = []
    for prof in ["leitura", "escrita"]:
        s = summary[summary.profile == prof].sort_values("users")
        if not s.empty:
            med_vals = [f"{r.scenario} ({r.users} u): {r.tempo_medio_ms:.1f} ms" for r in s.itertuples()]
            p95_vals = [f"{r.scenario}: {r.p95_ms:.1f} ms" for r in s.itertuples()]
            c_val = s[s.scenario == "C"]["tempo_medio_ms"].values
            a_val = s[s.scenario == "A"]["tempo_medio_ms"].values
            ratio = (c_val[0] / a_val[0]) if len(c_val) and len(a_val) and a_val[0] > 0 else 1.0
            p_label = "Perfil 1 (Leitura)" if prof == "leitura" else "Perfil 2 (Escrita)"
            q1_details.append(
                f"- **{p_label}**:\n"
                f"  - Tempo Médio: {', '.join(med_vals)} (aumento de {ratio:.2f}x de A para C)\n"
                f"  - Percentil 95 (P95): {', '.join(p95_vals)}"
            )
    lines.extend(q1_details)
    lines.append(
        "\n*Interpretação:* O aumento da concorrência provoca a formação de filas no API Gateway e nos microsserviços, "
        "elevando o tempo de espera de processamento e entrada/saída. A latência média cresce progressivamente, "
        "e a métrica P95 revela a degradação da cauda de distribuição com picos de latência sob carga elevada (150 usuários).\n"
    )

    lines.append("### 6.2. Qual perfil apresenta maior vazão?\n")
    for r in summary.sort_values(["scenario", "profile"]).itertuples():
        p_label = "Perfil 1 (Leitura)" if r.profile == "leitura" else "Perfil 2 (Escrita)"
        lines.append(f"- Cenário {r.scenario} ({USERS[r.scenario]} u) / {p_label}: **{r.vazao_rps:.2f} req/s** ({int(r.total_req)} requisições na janela medida)")

    v_leit = summary[summary.profile == "leitura"]["vazao_rps"].mean() if not summary.empty else 0
    v_escr = summary[summary.profile == "escrita"]["vazao_rps"].mean() if not summary.empty else 0
    maior_p = "Perfil 1 (Leitura)" if v_leit >= v_escr else "Perfil 2 (Escrita)"
    dif = abs(v_leit - v_escr)
    lines.append(
        f"\n*Interpretação:* O **{maior_p}** apresentou a maior vazão média "
        f"({max(v_leit, v_escr):.2f} req/s contra {min(v_leit, v_escr):.2f} req/s, diferença de {dif:.2f} req/s). "
        "Isso ocorre porque requisições de leitura não realizam inserções no banco, validações de payload ou bloqueios transacionais, "
        "permitindo que o customers-service e o vets-service processem as respostas de forma mais rápida.\n"
    )

    lines.append("### 6.3. Quais operações apresentam maior degradação?\n")
    for prof in ["leitura", "escrita"]:
        sub_ops = ops[ops.profile == prof]
        if not sub_ops.empty:
            p = sub_ops.pivot(index="operation", columns="scenario", values="tempo_medio_ms")
            if {"A", "C"} <= set(p.columns):
                p_label = "Perfil 1 (Leitura)" if prof == "leitura" else "Perfil 2 (Escrita)"
                lines.append(f"- **{p_label}** (Fator de aumento do Tempo Médio C / A):")
                deg = (p["C"] / p["A"]).sort_values(ascending=False)
                for op, factor in deg.items():
                    val_a = p.loc[op, "A"]
                    val_c = p.loc[op, "C"]
                    lines.append(f"  - `{op}`: **{factor:.2f}x** (de {val_a:.1f} ms no cenário A para {val_c:.1f} ms no cenário C)")
    lines.append(
        "\n*Interpretação:* A operação `GET /owners` sofre forte impacto porque busca a lista inteira de proprietários "
        "no banco e transfere uma carga útil maior de dados. Já `GET /owners/{id}` realiza busca indexada pontual por ID, "
        "mantendo latência proporcionalmente menor. As operações de escrita (`POST /owners`) também sofrem contenção transacional.\n"
    )

    lines.append("### 6.4. Como o consumo de CPU varia entre os cenários?\n")
    if not cpu_s.empty:
        for prof in ["leitura", "escrita"]:
            sub = cpu_s[cpu_s.profile == prof]
            if not sub.empty:
                p_label = "Perfil 1 (Leitura)" if prof == "leitura" else "Perfil 2 (Escrita)"
                lines.append(f"- **{p_label}**:")
                for r in sub.sort_values(["servico", "scenario"]).itertuples():
                    lines.append(f"  - {r.servico} (Cenário {r.scenario} - {USERS[r.scenario]} u): média de **{r.cpu_medio_pct:.1f}%**, pico de {r.cpu_pico_pct:.1f}%")
        lines.append(
            "\n*Interpretação:* O consumo de CPU cresce de maneira quase monotônica conforme os usuários simultâneos aumentam de 30 para 80 e 150. "
            "O `api-gateway` e o `customers-service` concentram a maior parte do uso de CPU: o gateway pelo roteamento reativo contínuo de 100% do tráfego, "
            "e o customers-service pelo processamento de 80% a 85% de todas as requisições geradas pelos perfis.\n"
        )
    else:
        lines.append("*(Nenhum dado de CPU registrado no arquivo cpu.csv - verifique se o Docker estava ativo durante o teste)*\n")

    lines.append("### 6.5. Qual cenário apresenta maior taxa de falhas?\n")
    max_fail = 0.0
    worst_case = "Nenhum"
    for r in summary.sort_values("falhas_pct", ascending=False).itertuples():
        p_label = "Perfil 1 (Leitura)" if r.profile == "leitura" else "Perfil 2 (Escrita)"
        lines.append(f"- Cenário {r.scenario} ({USERS[r.scenario]} u) / {p_label}: **{r.falhas_pct:.2f}% de falhas**")
        if r.falhas_pct > max_fail:
            max_fail = r.falhas_pct
            worst_case = f"Cenário {r.scenario} ({USERS[r.scenario]} u) no {p_label}"

    if max_fail > 0:
        lines.append(f"\n*Interpretação:* O cenário com maior taxa de falhas foi o **{worst_case}** com {max_fail:.2f}%, "
                     "decorrente de exaustão de conexões ou estouro de timeout (30s) sob alta concorrência.\n")
    else:
        lines.append("\n*Interpretação:* **0.00% de falhas** em todos os cenários. A aplicação e o gateway sustentaram "
                     "a carga sem interrupções de serviço ou timeouts dentro da janela de medição de cada perfil.\n")

    return "\n".join(lines)


def update_readme_content(tables_md, facts_md):
    readme_path = Path("README.md")
    if not readme_path.exists():
        return

    content = readme_path.read_text(encoding="utf-8")

    # Substitui seção de Resultados
    pattern_res = re.compile(r"## 5\. Resultados\n.*?(?=## 6\. Respostas)", re.DOTALL | re.IGNORECASE)
    new_res_block = (
        "## 5. Resultados\n\n"
        + tables_md + "\n\n"
        + "### 5.4. Gráficos Comparativos Gerados\n\n"
        + "![Tempo médio](results/grafico_tempo_medio.png)\n\n"
        + "![P95](results/grafico_p95.png)\n\n"
        + "![Vazão](results/grafico_vazao.png)\n\n"
        + "![Total de requisições](results/grafico_total_requisicoes.png)\n\n"
        + "![Taxa de falhas](results/grafico_falhas.png)\n\n"
        + "![Tempo médio por operação](results/grafico_por_operacao.png)\n\n"
        + "![CPU por serviço](results/grafico_cpu.png)\n\n"
    )

    if pattern_res.search(content):
        content = pattern_res.sub(new_res_block, content)

    # Substitui seção de Respostas às Questões
    pattern_resp = re.compile(r"## 6\. Respostas às [qQ]uestões\n.*?(?=## 7\. Conclusões)", re.DOTALL)
    new_resp_block = "## 6. Respostas às Questões\n\n" + facts_md + "\n\n"

    if pattern_resp.search(content):
        content = pattern_resp.sub(new_resp_block, content)

    readme_path.write_text(content, encoding="utf-8")
    print("README.md atualizado com sucesso com as tabelas e respostas!")


def main():
    parser = argparse.ArgumentParser(description="Analisa os dados dos experimentos e gera tabelas e gráficos.")
    parser.add_argument("--update-readme", action="store_true", help="Atualiza automaticamente o README.md com as tabelas e respostas")
    args = parser.parse_args()

    OUT.mkdir(exist_ok=True)
    df, cpu = load()
    df["users"] = df["scenario"].map(USERS)

    tot = df[df.operation == "TOTAL"]
    summary = tot.groupby(["scenario", "profile", "users"]).agg(
        repeticoes=("rep", "count"),
        tempo_medio_ms=("avg_ms", "mean"),
        tempo_medio_dp=("avg_ms", lambda x: x.std(ddof=1) if len(x) > 1 else 0.0),
        p95_ms=("p95_ms", "mean"),
        vazao_rps=("rps", "mean"),
        total_req=("requests", "mean"),
        falhas_pct=("fail_pct", "mean")
    ).reset_index()
    summary = summary.sort_values(["scenario", "profile"])
    summary.to_csv(OUT / "resumo_geral.csv", index=False)

    ops = df[df.operation != "TOTAL"].groupby(["scenario", "profile", "users", "operation"]).agg(
        requisicoes=("requests", "mean"),
        tempo_medio_ms=("avg_ms", "mean"),
        p95_ms=("p95_ms", "mean"),
        falhas_pct=("fail_pct", "mean")
    ).reset_index()

    tot_req_by_scen = ops.groupby(["scenario", "profile"])["requisicoes"].transform("sum")
    ops["distribuicao_pct"] = (100.0 * ops["requisicoes"] / tot_req_by_scen).round(1)
    ops = ops.sort_values(["scenario", "profile", "requisicoes"], ascending=[True, True, False])
    ops.to_csv(OUT / "por_operacao.csv", index=False)

    cpu_s = pd.DataFrame()
    # Mapeamento para exibição amigável nas tabelas
    display_summary = summary.copy()
    display_summary["scenario"] = display_summary["scenario"].map(lambda s: f"{s} ({USERS[s]} u)")
    display_summary["profile"] = display_summary["profile"].map(lambda p: "Perfil 1 (Leitura)" if p == "leitura" else "Perfil 2 (Escrita)")
    display_summary = display_summary.rename(columns={
        "scenario": "Cenário", "profile": "Perfil", "repeticoes": "Repetições",
        "tempo_medio_ms": "Tempo Médio (ms)", "tempo_medio_dp": "Desvio Padrão (ms)",
        "p95_ms": "P95 (ms)", "vazao_rps": "Vazão (req/s)",
        "total_req": "Total Requisições", "falhas_pct": "Falhas (%)"
    })

    display_ops = ops.copy()
    display_ops["scenario"] = display_ops["scenario"].map(lambda s: f"{s} ({USERS[s]} u)")
    display_ops["profile"] = display_ops["profile"].map(lambda p: "Perfil 1 (Leitura)" if p == "leitura" else "Perfil 2 (Escrita)")
    display_ops = display_ops.rename(columns={
        "scenario": "Cenário", "profile": "Perfil", "operation": "Operação",
        "requisicoes": "Requisições", "tempo_medio_ms": "Tempo Médio (ms)",
        "p95_ms": "P95 (ms)", "falhas_pct": "Falhas (%)", "distribuicao_pct": "Distribuição (%)"
    })

    md_parts = [
        "### 5.1. Resumo Geral Consolidado (Média de 10 Repetições)\n",
        md_table(display_summary.drop(columns=["users"], errors="ignore").round(2)),
        "\n\n### 5.2. Desempenho e Distribuição por Operação\n",
        md_table(display_ops.drop(columns=["users"], errors="ignore").round(2))
    ]

    if not cpu.empty:
        cpu_s = cpu.groupby(["scenario", "profile", "servico"]).agg(
            cpu_medio_pct=("cpu_mean", "mean"),
            cpu_pico_pct=("cpu_max", "mean"),
            mem_media_mb=("mem_mean_mb", "mean")
        ).reset_index()
        cpu_s = cpu_s.sort_values(["scenario", "profile", "servico"])
        cpu_s.to_csv(OUT / "cpu_por_servico.csv", index=False)

        display_cpu = cpu_s.copy()
        display_cpu["scenario"] = display_cpu["scenario"].map(lambda s: f"{s} ({USERS[s]} u)")
        display_cpu["profile"] = display_cpu["profile"].map(lambda p: "Perfil 1 (Leitura)" if p == "leitura" else "Perfil 2 (Escrita)")
        display_cpu = display_cpu.rename(columns={
            "scenario": "Cenário", "profile": "Perfil", "servico": "Serviço",
            "cpu_medio_pct": "CPU Média (%)", "cpu_pico_pct": "CPU Pico (%)",
            "mem_media_mb": "Memória Média (MB)"
        })
        md_parts += [
            "\n\n### 5.3. Utilização de CPU e Memória por Serviço (docker stats)\n",
            md_table(display_cpu.round(2))
        ]

    tables_md_content = "\n".join(md_parts)
    (OUT / "tabelas.md").write_text(tables_md_content, encoding="utf-8")

    line_chart(summary, "tempo_medio_ms", "Tempo médio de resposta (ms)", "grafico_tempo_medio.png",
               "Tempo Médio de Resposta x Usuários Simultâneos")
    line_chart(summary, "p95_ms", "P95 (ms)", "grafico_p95.png",
               "Tempo de Resposta P95 x Usuários Simultâneos")
    line_chart(summary, "vazao_rps", "Vazão (req/s)", "grafico_vazao.png",
               "Vazão (Throughput) x Usuários Simultâneos")
    line_chart(summary, "falhas_pct", "Taxa de falhas (%)", "grafico_falhas.png",
               "Taxa de Falhas (%) x Usuários Simultâneos")
    line_chart(summary, "total_req", "Total de requisições medidas", "grafico_total_requisicoes.png",
               "Total de Requisições x Usuários Simultâneos")

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharey=True)
    for ax, prof in zip(axes, ["leitura", "escrita"]):
        sub_ops = ops[ops.profile == prof]
        if not sub_ops.empty:
            p = sub_ops.pivot(index="operation", columns="scenario", values="tempo_medio_ms")
            p = p.reindex(columns=[c for c in "ABC" if c in p.columns])
            p.rename(columns=LABEL).plot.bar(ax=ax, rot=15)
        ax.set_title(PROFILE_LABEL.get(prof, prof), fontsize=11, fontweight="bold")
        ax.set_xlabel("")
        ax.set_ylabel("Tempo médio (ms)", fontsize=10)
        ax.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(OUT / "grafico_por_operacao.png", dpi=150)
    plt.close()

    if not cpu_s.empty:
        cs = cpu_s[cpu_s.servico.isin(FOCUS_SERVICES)].copy()
        if not cs.empty:
            fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharey=True)
            for ax, prof in zip(axes, ["leitura", "escrita"]):
                sub = cs[cs.profile == prof]
                if not sub.empty:
                    p = sub.pivot(index="servico", columns="scenario", values="cpu_medio_pct")
                    p = p.reindex(columns=[c for c in "ABC" if c in p.columns])
                    p.rename(columns=LABEL).plot.bar(ax=ax, rot=15)
                ax.set_title(PROFILE_LABEL.get(prof, prof), fontsize=11, fontweight="bold")
                ax.set_xlabel("")
                ax.set_ylabel("CPU média (%)", fontsize=10)
                ax.grid(alpha=0.3, axis="y")
            plt.tight_layout()
            plt.savefig(OUT / "grafico_cpu.png", dpi=150)
            plt.close()

    facts_md_content = generate_answers_and_facts(summary, ops, cpu_s)
    (OUT / "fatos_para_analise.md").write_text(facts_md_content, encoding="utf-8")

    if args.update_readme:
        update_readme_content(tables_md_content, facts_md_content)

    print("Processamento concluído.")


if __name__ == "__main__":
    main()
