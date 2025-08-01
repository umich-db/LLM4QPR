# Query Plans Data

This folder contains the pre-generated query plans used in the LLM4QPR experiments.

## Download

Due to size constraints (1.42 GB), the query plans are hosted externally:

**Google Drive**: [Download queryPlans.zip](https://drive.google.com/file/d/YOUR_FILE_ID/view?usp=sharing)

## Usage

1. Download the `queryPlans.zip` file from the Google Drive link above
2. Extract it to this directory (`LLM4QPR/queryPlans/`)
3. The extracted folder should contain subdirectories for each dataset:
   - `tpch/`
   - `tpcds/`
   - `imdb/`
   - `stats/`

## Structure

```
queryPlans/
├── tpch/          # TPC-H query plans
├── tpcds/         # TPC-DS query plans  
├── imdb/          # IMDB query plans
└── stats/         # STATS query plans
```

## Note

If you need to reproduce these query plans from scratch, see the "Reproducing Query Plans" section in the main README. 