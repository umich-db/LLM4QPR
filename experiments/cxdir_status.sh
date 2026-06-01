#!/bin/bash
# Read-only snapshot of the cross-attn-direction / mode-7 bert4/syn runs.
# Grouped into RUNNING (live training) and STOPPED (frozen last values).
# Each row also shows [LIVE]/[----] from the log's mtime (modified < 4 min ago = live).
DIR="logs/duckdb/logs_Train_job_Test_syn_ours"
D3="/home/dougdong/LLM4QPR/experiments/$DIR"
D2="/root/LLM4QPR/experiments/$DIR"
DL="/root/LLM4QPR/experiments/$DIR"

# emit a self-contained shell command (runs locally or via ssh) for one row.
# args: <dir> <glob> <skip_first(0/1)>
snip() {
  local dir="$1" glob="$2" tc=""
  [ "$3" = "1" ] && tc="|tail -n +2"
  cat <<EOF
L=\$(ls -t ${dir}/*${glob} 2>/dev/null|grep -v inference|head -1)
[ -n "\$L" ] && [ -n "\$(find "\$L" -mmin -4 2>/dev/null)" ] && ST="[LIVE]" || ST="[----]"
D=\$(awk -f /tmp/xt.awk "\$L" 2>/dev/null${tc})
echo "   \$ST \$(grep -oE '\\[Train\\] Epoch [0-9]+ Batch [0-9]+' "\$L" 2>/dev/null|tail -1) | tests: \$(printf '%s\\n' "\$D"|grep -c '[0-9]')"
printf '%s\\n' "\$D"|nl -v0|awk 'NF>=5{printf "      ep%-3s p90=%-8s p95=%-8s max=%-9s (p50=%s)\\n",\$1,\$3,\$4,\$5,\$2}'
EOF
}
L_() { bash -c "$(snip "$DL" "$1" "${2:-0}")"; }
D3_() { timeout 20 ssh -o ConnectTimeout=12 dougdong@dbresearch3.eecs.umich.edu "$(snip "$D3" "$1" "${2:-0}")" 2>&1; }
D2_() { timeout 30 ssh -o ConnectTimeout=12 -J dougdong@dbresearch2.eecs.umich.edu root@10.84.37.249 "$(snip "$D2" "$1" "${2:-0}")" 2>&1; }

echo "============ cross-attn direction / mode-7 (bert4 / duckdb-syn / seed42 / e30) ============"
echo
echo "################################## RUNNING ##################################"
echo "== LOCAL evalfrz    -> cx4 frozen + mlpFirst + EVAL-mode blocks (dropout off; expect ~2.37) =="; L_ 'cx4_finfl_frzAll999_mlpFirst_evalFrz_e30_seed42.log'
echo "== db3   cxdir_even -> LLM attends to PRICE (only ODD active) =="; D3_ 'frzEven999*pLR2e-05*seed42.log'
echo "== db2   cxdir_all  -> no cross-attn (cx4 frozen + pwm5/pLR) =="; D2_ 'frzAll999*pLR2e-05*seed42.log'
echo
echo "######################## STOPPED / reference (frozen, not updating) ########################"
echo "== db3   mode7 CONVERGED ref (1.53, stale auto-resumed ckpt -- NOT a run) =="
timeout 20 ssh -o ConnectTimeout=12 dougdong@dbresearch3.eecs.umich.edu 'L=$(ls -t '"$D3"'/*priceNor_randInit_e30_seed42.log 2>/dev/null|grep -v inference|head -1); awk -f /tmp/xt.awk "$L" 2>/dev/null|head -1|awk "{printf \"      p90=%-8s p95=%-8s max=%-9s (p50=%s)\n\",\$2,\$3,\$4,\$1}"' 2>&1
echo "== db3   mode7_fresh (JointPrice 512 retrain; STOPPED) =="; D3_ 'priceNor_randInit_e30_seed42.log' 1
echo "== LOCAL cxdir_odd (PRICE attends to LLM; STOPPED -- worst direction ~8-10) =="; L_ 'frzOdd999*pLR2e-05*seed42.log'
echo "== db3   mlpFirst (cx4 + mlpFirst, dropout ON -> stayed cx4-range ~6.5-8.4; STOPPED) =="; D3_ 'cx4_finfl_frzAll999_mlpFirst_e30_seed42.log'
echo "== db3   iso_cx4 (cx4 frozen, NO mlpFirst -> init-shifted ~4.0; STOPPED) =="; D3_ 'cx4_finfl_frzAll999_e30_seed42.log'
echo "== db3   MODE7+inflate (cx0, PRICE 768; STOPPED) =="; D3_ 'inflatePRICE_randInit_cx0_finfl_e30_seed42.log'
echo "== db3   MODE7+finfl+512 control (cx0, PRICE 512; STOPPED) =="; D3_ 'cx0_finfl_pod512_e30_seed42.log'
