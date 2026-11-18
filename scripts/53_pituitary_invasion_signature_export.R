root <- normalizePath(".", winslash = "/", mustWork = TRUE)
processed <- file.path(root, "codex_output", "pituitary-project", "data", "processed")
out_dir <- file.path(root, "codex_output", "endocrine-transport-project", "results")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

cohorts <- c("GSE169498", "GSE136781", "GSE260487")

load_cohort <- function(cohort) {
  expression <- readRDS(file.path(
    processed,
    paste0(cohort, "-expression.rds")
  ))
  metadata <- readRDS(file.path(
    processed,
    paste0(cohort, "-metadata.rds")
  ))
  if (cohort == "GSE260487") {
    metadata$invasion_binary <- ifelse(
      grepl("non-invasive", metadata$invasion, ignore.case = TRUE),
      0L,
      1L
    )
    metadata$sample <- as.character(metadata$sample)
  }
  list(expression = expression, metadata = metadata)
}

data <- setNames(lapply(cohorts, load_cohort), cohorts)
discovery <- data[["GSE169498"]]
labels <- discovery$metadata$invasion_binary
stopifnot(length(unique(labels)) == 2)

y <- labels
x <- discovery$expression[, discovery$metadata$sample, drop = FALSE]
row_tests <- genefilter::rowttests(x, factor(y))
statistics <- setNames(-row_tests$statistic, rownames(x))
p_values <- setNames(row_tests$p.value, rownames(x))
fdr <- p.adjust(p_values, method = "BH")
eligible <- names(fdr)[fdr < 0.05]
ranked <- statistics[eligible]
up <- head(names(sort(ranked[ranked > 0], decreasing = TRUE)), 100)
down <- head(names(sort(ranked[ranked < 0], decreasing = FALSE)), 100)

zscore_rows <- function(expr) {
  t(scale(t(expr)))
}

score_signature <- function(expr, up, down) {
  z <- zscore_rows(expr)
  common_up <- intersect(up, rownames(z))
  common_down <- intersect(down, rownames(z))
  colMeans(z[common_up, , drop = FALSE], na.rm = TRUE) -
    colMeans(z[common_down, , drop = FALSE], na.rm = TRUE)
}

score_rows <- list()
for (cohort in cohorts) {
  item <- data[[cohort]]
  score <- score_signature(item$expression, up, down)
  samples <- intersect(item$metadata$sample, names(score))
  labels_cohort <- item$metadata$invasion_binary[
    match(samples, item$metadata$sample)
  ]
  score_rows[[cohort]] <- data.frame(
    cohort = cohort,
    sample = samples,
    invasion_binary = labels_cohort,
    score = as.numeric(score[samples]),
    check.names = FALSE
  )
}
scores <- do.call(rbind, score_rows)
write.csv(
  scores,
  file.path(out_dir, "RATA_v5_pituitary_invasion_scores.csv"),
  row.names = FALSE
)

genes <- data.frame(
  direction = c(rep("positive", length(up)), rep("negative", length(down))),
  gene = c(up, down),
  discovery_t = c(statistics[up], statistics[down]),
  check.names = FALSE
)
write.csv(
  genes,
  file.path(out_dir, "RATA_v5_pituitary_invasion_signature_genes.csv"),
  row.names = FALSE
)

metadata <- data.frame(
  cohort = cohorts,
  n = c(73, 42, 32),
  invasive = c(49, 23, 15),
  non_invasive = c(24, 19, 17),
  check.names = FALSE
)
write.csv(
  metadata,
  file.path(out_dir, "RATA_v5_pituitary_invasion_cohort_counts.csv"),
  row.names = FALSE
)
candidate_export <- data.frame(
  gene = rownames(x),
  x,
  check.names = FALSE
)
write.csv(
  candidate_export,
  gzfile(file.path(
    out_dir,
    "RATA_v5_pituitary_invasion_discovery_expression.csv.gz"
  )),
  row.names = FALSE
)
write.csv(
  data.frame(
    sample = discovery$metadata$sample,
    invasion_binary = discovery$metadata$invasion_binary,
    check.names = FALSE
  ),
  file.path(out_dir, "RATA_v5_pituitary_invasion_discovery_labels.csv"),
  row.names = FALSE
)
cat("eligible genes:", length(eligible), "\n")
cat("up:", length(up), "down:", length(down), "\n")
print(metadata)
