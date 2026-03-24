# CGFs (Classical Guitar Fingerings Dataset)

## Overview
This repository contains fingering annotations for classical guitar etudes, encoded in MusicXML format with derived CSV tables for computational analysis. The dataset supports comparative analysis of fingering practices between existing published editions and contemporary professional performers.

For details on the dataset construction and preliminary findings, please refer to our publications listed below.

## Contents
- `fingering_data/` - CSV tables extracted from MusicXML
- `musicxml2csv/` - Python extraction pipeline using music21 and ElementTree

## Sample Data
This repository currently contains 40 etudes. More data will be added as the research progresses.

## License
This dataset is licensed under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/).

## Usage Guidelines
While the CC BY-NC-ND 4.0 license permits non-commercial use, we kindly request that you contact the authors before:

- Using the data for training machine learning models
- Incorporating into other datasets or projects
- Any use beyond viewing and citing

This allows us to track usage and discuss potential collaboration opportunities.

## Citation
```
Iino, N., & Iino, A.: Fingering Prediction for Classical Guitar: Dataset Creation and Model Development. 
In Proceedings of the 31st International Conference on Multimedia Modeling, MMM 2025, LNCS (Vol. 15524, pp. 134–141). (2025)
https://doi.org/10.1007/978-981-96-2074-6_14

Iino, N., & Iino, A.: Expert Fingering Variation in Classical Guitar Etudes: Creation of Dataset for Comparative Analysis. 
In Music Encoding Conference, MEC 2026 (2026)
```

## Contact
For inquiries about the dataset or collaboration opportunities:
- Nami Iino - niino@slis.tsukuba.ac.jp

## Acknowledgements
This work was supported by JSPS KAKENHI Grant Number JP22K18016.
