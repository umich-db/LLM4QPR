# DeepDB Augmented Query Plans

This folder contains query plans for cross-workload experiments, sourced from the paper:

**"Zero-Shot Cost Models for Out-of-the-box Learned Cost Prediction"**

## Download

The query plans can be downloaded from: [Google Drive](https://drive.google.com/file/d/1Sjsj2cmQUzfEnJ6mSXy_KD-_05akBqeA/view?usp=sharing) 

## Usage

These query plans are used in the cross-workload experiments to test model generalization capabilities. The experiments train models on a subset of workloads and evaluate performance on held-out workloads.

## Citation

If you use these query plans in your research, please cite:

```
@article{DBLP:journals/pvldb/HilprechtB22,
  author       = {Benjamin Hilprecht and
                  Carsten Binnig},
  title        = {Zero-Shot Cost Models for Out-of-the-box Learned Cost Prediction},
  journal      = {Proc. {VLDB} Endow.},
  volume       = {15},
  number       = {11},
  pages        = {2361--2374},
  year         = {2022},
  url          = {https://www.vldb.org/pvldb/vol15/p2361-hilprecht.pdf},
  doi          = {10.14778/3551793.3551799},
  timestamp    = {Sun, 04 Aug 2024 19:47:54 +0200},
  biburl       = {https://dblp.org/rec/journals/pvldb/HilprechtB22.bib},
  bibsource    = {dblp computer science bibliography, https://dblp.org}
}
```