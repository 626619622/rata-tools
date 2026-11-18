suppressPackageStartupMessages({
  library(AnnotationDbi)
  library(hgu133plus2.db)
})

root <- normalizePath(".", winslash = "/", mustWork = TRUE)
out_file <- file.path(
  root,
  "codex_output",
  "endocrine-transport-project",
  "data",
  "platforms",
  "GPL570_probe_to_symbol_20261109.csv"
)

probe_ids <- keys(hgu133plus2.db, keytype = "PROBEID")
mapping <- AnnotationDbi::select(
  hgu133plus2.db,
  keys = probe_ids,
  columns = c("SYMBOL", "ENTREZID"),
  keytype = "PROBEID"
)
mapping <- mapping[!is.na(mapping$SYMBOL) & nzchar(mapping$SYMBOL), ]
mapping <- unique(mapping)

dir.create(dirname(out_file), recursive = TRUE, showWarnings = FALSE)
utils::write.csv(mapping, out_file, row.names = FALSE, na = "")
cat("mapped_probes:", nrow(mapping), "\n")
cat("output:", out_file, "\n")
