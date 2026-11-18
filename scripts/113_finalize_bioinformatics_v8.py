"""Apply author-year citations and the enlarged runtime benchmark."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v7.md"
OUTPUT = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v8.md"


CITATIONS = {
    "[3,4]": "(Barrett et al., 2013; Clough and Barrett, 2016)",
    "[1,2]": "(Ambroise and McLachlan, 2002; Ioannidis, 2005)",
    "[5-8,15-19]": "(Aran et al., 2015, 2017; Finotello et al., 2019; Gagnon-Bartsch and Speed, 2012; Johnson et al., 2007; Leek and Storey, 2007; Newman et al., 2015; Sturm et al., 2019; Yoshihara et al., 2013)",
    "[9,10]": "(Collins et al., 2015; Moons et al., 2019)",
    "[11]": "(Riley et al., 2020)",
    "[5-7]": "(Gagnon-Bartsch and Speed, 2012; Johnson et al., 2007; Leek and Storey, 2007)",
    "[12-14]": "(Arjovsky et al., 2019; Rothenhäusler et al., 2021; Sagawa et al., 2020)",
    "[15-19]": "(Aran et al., 2015, 2017; Finotello et al., 2019; Newman et al., 2015; Sturm et al., 2019; Yoshihara et al., 2013)",
    "[20]": "(Efron and Tibshirani, 1993)",
    "[21]": "(DerSimonian and Laird, 1986)",
    "[22]": "(Harrell et al., 1996)",
}

REFERENCES = """## References

Ambroise C, McLachlan GJ (2002) Selection bias in gene extraction on the basis of microarray gene-expression data. *Proceedings of the National Academy of Sciences of the United States of America* 99:6562-6566.

Aran D, Hu Z, Butte AJ (2017) xCell: digitally portraying the tissue cellular heterogeneity landscape. *Genome Biology* 18:220.

Aran D, Sirota M, Butte AJ (2015) Systematic pan-cancer analysis of tumour purity. *Nature Communications* 6:8971.

Arjovsky M, Bottou L, Gulrajani I, Lopez-Paz D (2019) Invariant risk minimization. *arXiv*:1907.02893.

Barrett T, Wilhite SE, Ledoux P et al. (2013) NCBI GEO: archive for functional genomics data sets-update. *Nucleic Acids Research* 41:D991-D995.

Clough E, Barrett T (2016) The Gene Expression Omnibus Database. *Methods in Molecular Biology* 1418:93-110.

Collins GS, Reitsma JB, Altman DG, Moons KGM (2015) Transparent reporting of a multivariable prediction model for individual prognosis or diagnosis (TRIPOD). *Annals of Internal Medicine* 162:55-63.

DerSimonian R, Laird N (1986) Meta-analysis in clinical trials. *Controlled Clinical Trials* 7:177-188.

Efron B, Tibshirani RJ (1993) *An Introduction to the Bootstrap*. New York: Chapman & Hall.

Finotello F, Mayer C, Plattner C et al. (2019) Molecular and pharmacological modulators of the tumor immune contexture revealed by deconvolution of RNA-seq data. *Genome Medicine* 11:34.

Gagnon-Bartsch JA, Speed TP (2012) Using control genes to correct for unwanted variation in microarray data. *Biostatistics* 13:539-552.

Harrell FE Jr, Lee KL, Mark DB (1996) Multivariable prognostic models: issues in developing models, evaluating assumptions and adequacy, and measuring and reducing errors. *Statistics in Medicine* 15:361-387.

Ioannidis JPA (2005) Why most published research findings are false. *PLoS Medicine* 2:e124.

Johnson WE, Li C, Rabinovic A (2007) Adjusting batch effects in microarray expression data using empirical Bayes methods. *Biostatistics* 8:118-127.

Leek JT, Storey JD (2007) Capturing heterogeneity in gene expression studies by surrogate variable analysis. *PLoS Genetics* 3:e161.

Moons KGM, Wolff RF, Riley RD et al. (2019) PROBAST: a tool to assess risk of bias and applicability of prediction model studies. *Annals of Internal Medicine* 170:51-58.

Newman AM, Liu CL, Green MR et al. (2015) Robust enumeration of cell subsets from tissue expression profiles. *Nature Methods* 12:453-457.

Riley RD, Ensor J, Snell KIE et al. (2020) Calculating the sample size required for developing a clinical prediction model. *BMJ* 368:m441.

Rothenhäusler D, Meinshausen N, Bühlmann P, Peters J (2021) Anchor regression: heterogeneous data meets causality. *Journal of Machine Learning Research* 22:1-55.

Sagawa S, Koh PW, Hashimoto TB, Liang P (2020) Distributionally robust neural networks for group shifts. *Proceedings of ICLR*.

Sturm G, Finotello F, Petitprez F et al. (2019) Comprehensive evaluation of transcriptome-based cell-type quantification methods for immuno-oncology. *Bioinformatics* 35:i436-i445.

Yoshihara K, Shahmoradgoli M, Martínez E et al. (2013) Inferring tumour purity and stromal and immune cell admixture from expression data. *Nature Communications* 4:2612.
"""

TABLE4 = """### Table 4. Runtime benchmark for `rata-tools` 0.2.0

| Task | Synthetic size | Repeats | Median time | Peak process RSS |
|---|---:|---:|---:|---:|
| Evidence capacity | 1,000 claims, 10 clusters | 100 | <0.001 s | 245.9 MB |
| Selection-null decision | 5,000 null values | 1,000 | <0.001 s | 246.1 MB |
| Multi-cohort binary gate | 10 cohorts | 1,000 | <0.001 s | 246.1 MB |
| Survival transport gate | 500 samples, 10 cohorts | 5 | 0.287 s | 246.8 MB |
| Selection-aware CV | 500 samples, 1,000 features, 5 folds, k=3 | 3 | 0.030 s | 249.1 MB |
| Selection-aware CV | 500 samples, 20,000 features, 5 folds, k=3 | 3 | 0.448 s | 250.2 MB |

Timings exclude data download, expression preprocessing and plotting.
"""


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for old, new in CITATIONS.items():
        if old not in text:
            raise ValueError(f"Citation token not found: {old}")
        text = text.replace(old, new)

    text = text.replace(
        "A 500-sample, 1,000-feature selection benchmark ran in 0.040 s.",
        "A five-fold, 500-sample selection benchmark with 1,000 features ran in 0.030 s.",
        1,
    )
    text = text.replace(
        "runs the 500-sample, 10-cohort survival gate in 0.269 s.",
        "runs the 500-sample, 10-cohort survival gate in 0.287 s.",
        1,
    )

    old_runtime = (
        "Table 4 reports local benchmarks for release 0.2.0. Evidence-capacity calculation for 1,000 claims across 10 clusters required 0.0002 s per call. A 10-cohort binary rule required 0.00001 s. A cohort-stratified survival gate with 500 samples and 10 cohorts required a median 0.269 s. A five-fold selection-aware AUC with 500 samples and 1,000 features required 0.040 s. Peak process memory across the benchmark remained approximately 169-173 MB. These timings describe software overhead on synthetic inputs and are not estimates of expression preprocessing or data download time. The benchmark environment, vignette and release checks are provided in Supplementary Table S4."
    )
    new_runtime = (
        "Table 4 reports local benchmarks for release 0.2.0. Evidence-capacity calculation for 1,000 claims across 10 clusters and the smaller decision primitives completed in less than 0.001 s per call. A cohort-stratified survival gate with 500 samples and 10 cohorts required a median 0.287 s. Five-fold selection-aware AUC with 500 samples and 1,000 features required 0.030 s; expanding the candidate matrix to 20,000 features increased the median to 0.448 s. Peak process memory remained approximately 246-250 MB. These timings describe software overhead on synthetic inputs and are not estimates of expression preprocessing or data download time. The benchmark environment, vignette and release checks are provided in Supplementary Table S4."
    )
    if old_runtime not in text:
        raise ValueError("Runtime paragraph not found")
    text = text.replace(old_runtime, new_runtime, 1)

    text = re.sub(
        r"### Table 4\. Runtime benchmark.*?(?=## Figure legends)",
        TABLE4 + "\n",
        text,
        count=1,
        flags=re.S,
    )
    text = re.sub(r"## References.*$", REFERENCES, text, count=1, flags=re.S)
    OUTPUT.write_text(text, encoding="utf-8")

    abstract = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    words = len(re.findall(r"\b[\w]+\b", abstract))
    print(OUTPUT)
    print(f"Abstract words: {words}")


if __name__ == "__main__":
    main()
