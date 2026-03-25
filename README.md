# CGFs (Classical Guitar Fingerings Dataset)

## Overview
This repository contains fingering annotations for classical guitar etudes, encoded as CSV tables derived from MusicXML files.

The annotations are based on published classical guitar editions and additional fingering revisions by a contemporary professional guitarist, allowing simple comparison between different fingering approaches.

For details on the dataset construction and analysis, please refer to the publications listed below.

## Contents
- fingering_data/ - CSV tables extracted from annotated scores
- musicxml2csv/ - Python extraction pipeline using music21 and ElementTree

## Sample Data
This repository currently contains 40 etudes. Additional data may be added in future updates.

## License
This dataset is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Only derived note-level annotations (CSV files) and analysis scripts are distributed in this repository.  
MusicXML files are excluded because they are based on copyrighted published scores.

The authors are not responsible for any errors in the dataset or for any consequences arising from its use.

## Usage Guidelines
While the CC BY 4.0 license permits reuse with attribution, we would appreciate being informed when using the dataset for:

- Using the data for training machine learning models
- Incorporating it into other datasets or projects
- Using it beyond simple reference or citation

This helps us understand usage and may support future collaboration.

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
