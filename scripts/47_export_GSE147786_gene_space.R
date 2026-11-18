root <- normalizePath(".", winslash = "/", mustWork = TRUE)
expression <- readRDS(file.path(
  root,
  "codex_output",
  "pituitary-project",
  "data",
  "processed",
  "GSE147786-lineage-expression.rds"
))
out <- file.path(
  root,
  "codex_output",
  "endocrine-transport-project",
  "results",
  "RATA_v5_GSE147786_gene_space.csv"
)
write.csv(
  data.frame(gene = rownames(expression), check.names = FALSE),
  out,
  row.names = FALSE
)
cat("genes:", nrow(expression), "\n")
cat("samples:", ncol(expression), "\n")
