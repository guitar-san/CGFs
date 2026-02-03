# Classical Guitar Fingering Dataset

## Overview
This repository contains fingering annotations for classical guitar etudes, encoded in MusicXML format with derived CSV tables for computational analysis. The dataset supports comparative analysis of fingering practices between existing published editions and contemporary professional performers.

For details on the dataset construction and preliminary findings, please refer to our publications listed below.

## Contents
- `fingering_data/` - CSV tables extracted from MusicXML
- `musicxml2csv/` - Python extraction pipeline using music21 and ElementTree

## Sample Data
This repository currently provides sample data for five etudes from the full dataset of 40 etudes. The complete dataset will be released upon completion of ongoing research.

## Usage Restrictions
**Important:** This dataset is provided for reference purposes only.

- ✅ Viewing and inspecting the data
- ✅ Citing in academic publications
- ❌ Using the data for training machine learning models
- ❌ Incorporating into other datasets or projects
- ❌ Redistribution in any form

If you wish to use this dataset for research purposes beyond reference, please contact the authors to discuss collaboration opportunities.

## Citation
If you refer to this dataset, please cite:
```
Iino, N., & Iino, A. (2025). Fingering Prediction for Classical Guitar: Dataset Creation and Model Development. 
In I. Ide et al. (Eds.), MMM 2025, LNCS (Vol. 15524, pp. 134–141). Springer.
https://doi.org/10.1007/978-981-96-2074-6_14

Iino, N., & Iino, A. (2026). Expert Fingering Variation in Classical Guitar Etudes: Creation of Dataset for Comparative Analysis. 
In Music Encoding Conference 2026 Book of Abstracts. Tokyo, Japan.
```

## Contact
For inquiries about the dataset or collaboration opportunities:
- Nami Iino - niino@slis.tsukuba.ac.jp

## Acknowledgements
This work was supported by JSPS KAKENHI Grant Number JP22K18016.
