TRAIN_WLS=(tpcds job syn stats)

# Start with the first element…
joined="${TRAIN_WLS[0]}"

# …then append “-element” for each remaining entry
for elt in "${TRAIN_WLS[@]:1}"; do
  joined+="-$elt"
done

echo "$joined"
# → tpcds-job-syn-stats
