root <- normalizePath(".", winslash = "/", mustWork = TRUE)
metadata <- readRDS(file.path(
  root,
  "codex_output",
  "pituitary-project",
  "data",
  "processed",
  "GSE260487-metadata.rds"
))
table_data <- table(metadata$lineage, metadata$invasion)
test_corrected <- chisq.test(table_data)
test_uncorrected <- chisq.test(table_data, correct = FALSE)
cramers_v <- sqrt(
  test_uncorrected$statistic /
    (sum(table_data) * (min(dim(table_data)) - 1))
)

out <- file.path(
  root,
  "codex_output",
  "endocrine-transport-project",
  "results"
)
write.csv(
  as.data.frame.matrix(table_data),
  file.path(out, "RATA_v5_GSE260487_invasion_lineage_table.csv")
)
summary <- data.frame(
  cohort = "GSE260487",
  n = sum(table_data),
  chi_square_uncorrected = as.numeric(test_uncorrected$statistic),
  p_value_uncorrected = test_uncorrected$p.value,
  p_value_yates = test_corrected$p.value,
  df = as.numeric(test_uncorrected$parameter),
  cramers_v = as.numeric(cramers_v),
  identifiability = "not_identifiable_perfect_lineage_confounding",
  adjusted_auc_status = "not_estimable_no_within_lineage_overlap",
  check.names = FALSE
)
write.csv(
  summary,
  file.path(out, "RATA_v5_GSE260487_invasion_lineage_confounding.csv"),
  row.names = FALSE
)
print(table_data)
print(summary)
