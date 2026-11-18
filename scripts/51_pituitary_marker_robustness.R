root <- normalizePath(".", winslash = "/", mustWork = TRUE)

external_expr <- readRDS(file.path(
  root,
  "codex_output",
  "pituitary-project",
  "data",
  "processed",
  "GSE147786-lineage-expression.rds"
))
external_meta <- readRDS(file.path(
  root,
  "codex_output",
  "pituitary-project",
  "data",
  "processed",
  "GSE147786-lineage-metadata.rds"
))
discovery_expr <- readRDS(file.path(
  root,
  "codex_output",
  "pituitary-project",
  "data",
  "processed",
  "GSE213527-lineage-expression.rds"
))
discovery_meta <- readRDS(file.path(
  root,
  "codex_output",
  "pituitary-project",
  "data",
  "processed",
  "GSE213527-lineage-metadata.rds"
))
signature <- read.csv(file.path(
  root,
  "codex_output",
  "endocrine-transport-project",
  "results",
  "RATA_v5_pituitary_lineage_signature_genes.csv"
), check.names = FALSE)

score_signature <- function(expr, up, down) {
  z <- t(scale(t(expr)))
  common_up <- intersect(up, rownames(z))
  common_down <- intersect(down, rownames(z))
  colMeans(z[common_up, , drop = FALSE], na.rm = TRUE) -
    colMeans(z[common_down, , drop = FALSE], na.rm = TRUE)
}

auc_binary <- function(score, label) {
  pos <- score[label == "GH"]
  neg <- score[label == "NFPA"]
  pairs <- outer(pos, neg, "-")
  (sum(pairs > 0) + 0.5 * sum(pairs == 0)) / length(pairs)
}

up_all <- signature$gene[signature$direction == "positive"]
down_all <- signature$gene[signature$direction == "negative"]
up_external <- intersect(up_all, rownames(external_expr))
down_external <- intersect(down_all, rownames(external_expr))

discovery_score_200 <- score_signature(discovery_expr, up_all, down_all)
discovery_score_186 <- score_signature(
  discovery_expr,
  up_external,
  down_external
)
score_correlation <- cor(
  discovery_score_200,
  discovery_score_186,
  method = "pearson"
)
score_correlation_spearman <- cor(
  discovery_score_200,
  discovery_score_186,
  method = "spearman"
)

marker_up <- c("GH1", "POU1F1", "DLK1", "SLIT1")
marker_down <- c("NR5A1", "FSHB", "GATA3")
marker_present_up <- intersect(marker_up, rownames(external_expr))
marker_present_down <- intersect(marker_down, rownames(external_expr))
marker_score <- score_signature(
  external_expr,
  marker_present_up,
  marker_present_down
)

external_tumor <- external_meta$lineage %in% c("GH", "NFPA")
external_labels <- external_meta$lineage[external_tumor]
external_samples <- external_meta$sample[external_tumor]
marker_score_tumor <- marker_score[external_samples]

out <- file.path(
  root,
  "codex_output",
  "endocrine-transport-project",
  "results"
)
write.csv(
  data.frame(
    sample = external_samples,
    lineage = external_labels,
    marker_score = as.numeric(marker_score_tumor),
    check.names = FALSE
  ),
  file.path(out, "RATA_v5_pituitary_7marker_external_scores.csv"),
  row.names = FALSE
)

summary <- data.frame(
  marker_up = paste(marker_present_up, collapse = ";"),
  marker_down = paste(marker_present_down, collapse = ";"),
  marker_count = length(marker_present_up) + length(marker_present_down),
  marker_external_auc = auc_binary(marker_score_tumor, external_labels),
  signature_200_genes = length(unique(c(up_all, down_all))),
  external_covered_up = length(up_external),
  external_covered_down = length(down_external),
  external_covered_total = length(unique(c(up_external, down_external))),
  discovery_score_pearson_200_vs_186 = score_correlation,
  discovery_score_spearman_200_vs_186 = score_correlation_spearman,
  check.names = FALSE
)
write.csv(
  summary,
  file.path(out, "RATA_v5_pituitary_marker_robustness.csv"),
  row.names = FALSE
)
cat("marker AUC:", summary$marker_external_auc, "\n")
cat("200-vs-186 Pearson:", score_correlation, "\n")
cat("200-vs-186 Spearman:", score_correlation_spearman, "\n")
