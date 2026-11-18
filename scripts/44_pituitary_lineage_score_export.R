root <- normalizePath(".", winslash = "/", mustWork = TRUE)

expr_file <- file.path(
  root,
  "codex_output",
  "pituitary-project",
  "data",
  "processed",
  "GSE213527-lineage-expression.rds"
)
meta_file <- file.path(
  root,
  "codex_output",
  "pituitary-project",
  "data",
  "processed",
  "GSE213527-lineage-metadata.rds"
)
de_file <- file.path(
  root,
  "codex_output",
  "pituitary-project",
  "results",
  "GSE213527-GH-vs-NFPA-DE.csv"
)

expression <- readRDS(expr_file)
metadata <- readRDS(meta_file)
de <- read.csv(de_file, check.names = FALSE)

de <- de[
  de$gene %in% rownames(expression)
  & !is.na(de$adj.P.Val)
  & de$adj.P.Val < 0.05
  & !is.na(de$logFC),
]
positive <- de[order(de$logFC, decreasing = TRUE), ][1:100, ]
negative <- de[order(de$logFC, decreasing = FALSE), ][1:100, ]

zscore_rows <- function(x) {
  t(scale(t(x)))
}

z_expression <- zscore_rows(expression)
positive_score <- colMeans(z_expression[positive$gene, , drop = FALSE])
negative_score <- colMeans(z_expression[negative$gene, , drop = FALSE])
score <- positive_score - negative_score

metadata$sample <- as.character(metadata$sample)
score_df <- data.frame(
  sample = metadata$sample,
  lineage = metadata$lineage,
  score = as.numeric(score[metadata$sample]),
  check.names = FALSE
)
score_df <- score_df[score_df$lineage %in% c("GH", "NFPA"), ]

results_dir <- file.path(
  root,
  "codex_output",
  "endocrine-transport-project",
  "results"
)
dir.create(results_dir, recursive = TRUE, showWarnings = FALSE)
write.csv(
  score_df,
  file.path(results_dir, "RATA_v5_pituitary_lineage_discovery_scores.csv"),
  row.names = FALSE
)

genes <- data.frame(
  direction = c(rep("positive", nrow(positive)), rep("negative", nrow(negative))),
  gene = c(positive$gene, negative$gene),
  discovery_logFC = c(positive$logFC, negative$logFC),
  discovery_FDR = c(positive$adj.P.Val, negative$adj.P.Val),
  check.names = FALSE
)
write.csv(
  genes,
  file.path(results_dir, "RATA_v5_pituitary_lineage_signature_genes.csv"),
  row.names = FALSE
)

candidate_expression <- expression[de$gene, , drop = FALSE]
candidate_export <- data.frame(
  gene = rownames(candidate_expression),
  candidate_expression,
  check.names = FALSE
)
write.csv(
  candidate_export,
  file.path(results_dir, "RATA_v5_pituitary_lineage_candidate_expression.csv"),
  row.names = FALSE
)

cat("samples:", nrow(score_df), "\n")
cat("positive genes:", nrow(positive), "\n")
cat("negative genes:", nrow(negative), "\n")
cat("candidate genes:", nrow(de), "\n")
