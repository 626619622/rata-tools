root <- normalizePath(".", winslash = "/", mustWork = TRUE)

expr <- readRDS(file.path(
  root,
  "codex_output",
  "pituitary-project",
  "data",
  "processed",
  "GSE147786-lineage-expression.rds"
))
meta <- readRDS(file.path(
  root,
  "codex_output",
  "pituitary-project",
  "data",
  "processed",
  "GSE147786-lineage-metadata.rds"
))
score_df <- read.csv(file.path(
  root,
  "codex_output",
  "pituitary-project",
  "results",
  "GSE147786-lineage-signature-scores.csv"
), check.names = FALSE)

zscore <- function(x) {
  sx <- stats::sd(x)
  if (!is.finite(sx) || sx == 0) {
    return(rep(0, length(x)))
  }
  (x - mean(x)) / sx
}

sex_genes <- intersect(c("XIST", "RPS4Y1", "UTY"), rownames(expr))
male_score <- rep(NA_real_, ncol(expr))
names(male_score) <- colnames(expr)
if ("RPS4Y1" %in% sex_genes) {
  male_score <- zscore(expr["RPS4Y1", ])
}
if ("UTY" %in% sex_genes) {
  male_score <- male_score + zscore(expr["UTY", ])
}
if ("XIST" %in% sex_genes) {
  male_score <- male_score - zscore(expr["XIST", ])
}
inferred_sex <- ifelse(male_score > 0, "inferred_male", "inferred_female")

variable <- order(apply(expr, 1, stats::var), decreasing = TRUE)[1:min(5000, nrow(expr))]
pca_input <- t(scale(t(expr[variable, , drop = FALSE])))
pca_input <- pca_input[apply(pca_input, 1, function(x) all(is.finite(x))), , drop = FALSE]
pca <- stats::prcomp(t(pca_input), center = FALSE, scale. = FALSE, rank. = 5)
pcs <- pca$x[, 1:5, drop = FALSE]

tumor <- score_df$lineage %in% c("GH", "NFPA")
samples <- score_df$sample[tumor]
score <- score_df$score[tumor]

proxy_rows <- list()
if (length(sex_genes) > 0) {
  proxy_rows[[length(proxy_rows) + 1]] <- data.frame(
    proxy = "inferred_sex_male_score",
    genes = paste(sex_genes, collapse = ";"),
    pearson_r = cor(score, male_score[samples], method = "pearson"),
    spearman_rho = cor(score, male_score[samples], method = "spearman"),
    check.names = FALSE
  )
}

for (pc in colnames(pcs)) {
  proxy_rows[[length(proxy_rows) + 1]] <- data.frame(
    proxy = pc,
    genes = "top5000_variable_expression_PC",
    pearson_r = cor(score, pcs[samples, pc], method = "pearson"),
    spearman_rho = cor(score, pcs[samples, pc], method = "spearman"),
    check.names = FALSE
  )
}
proxy_table <- do.call(rbind, proxy_rows)

label <- score_df$lineage[tumor]
sex_table <- table(
  inferred_sex = inferred_sex[samples],
  lineage = label
)
sex_auc <- {
  pos <- score[inferred_sex[samples] == "inferred_male"]
  neg <- score[inferred_sex[samples] == "inferred_female"]
  pairs <- outer(pos, neg, "-")
  (sum(pairs > 0) + 0.5 * sum(pairs == 0)) / length(pairs)
}
sex_residual_score <- resid(lm(score ~ male_score[samples]))
sex_residual_auc <- {
  pos <- sex_residual_score[label == "GH"]
  neg <- sex_residual_score[label == "NFPA"]
  pairs <- outer(pos, neg, "-")
  (sum(pairs > 0) + 0.5 * sum(pairs == 0)) / length(pairs)
}

pc_residual_model <- lm(
  score ~ pcs[samples, c("PC2", "PC3", "PC4", "PC5")]
)
pc_residual_score <- resid(pc_residual_model)
pc_residual_r2 <- summary(pc_residual_model)$r.squared
pc_residual_adjusted_r2 <- summary(pc_residual_model)$adj.r.squared
pc1_model <- lm(score ~ pcs[samples, "PC1"])
pc1_r2 <- summary(pc1_model)$r.squared
pc1_pc234_model <- lm(
  score ~ pcs[samples, c("PC1", "PC2", "PC3", "PC4", "PC5")]
)
pc1_pc234_r2 <- summary(pc1_pc234_model)$r.squared
pc_residual_auc <- {
  pos <- pc_residual_score[label == "GH"]
  neg <- pc_residual_score[label == "NFPA"]
  pairs <- outer(pos, neg, "-")
  (sum(pairs > 0) + 0.5 * sum(pairs == 0)) / length(pairs)
}

sensitivity <- data.frame(
  sex_auc_signature_vs_inferred_male = sex_auc,
  sex_residual_auc = sex_residual_auc,
  pc234_residual_auc = pc_residual_auc,
  pc234_r2_for_signature_score = pc_residual_r2,
  pc234_adjusted_r2_for_signature_score = pc_residual_adjusted_r2,
  pc1_r2_for_signature_score = pc1_r2,
  pc234_incremental_r2_over_pc1 = pc1_pc234_r2 - pc1_r2,
  check.names = FALSE
)

out <- file.path(
  root,
  "codex_output",
  "endocrine-transport-project",
  "results"
)
write.csv(
  proxy_table,
  file.path(out, "RATA_v5_pituitary_expression_proxy_negative_controls.csv"),
  row.names = FALSE
)
write.csv(
  sensitivity,
  file.path(
    out,
    "RATA_v5_pituitary_proxy_sensitivity_models.csv"
  ),
  row.names = FALSE
)
write.csv(
  as.data.frame.matrix(sex_table),
  file.path(
    out,
    "RATA_v5_pituitary_inferred_sex_by_lineage.csv"
  )
)

summary_lines <- c(
  sprintf("sex_genes_available=%s", paste(sex_genes, collapse = ";")),
  sprintf("inferred_male_n=%d", sum(inferred_sex[samples] == "inferred_male")),
  sprintf("inferred_female_n=%d", sum(inferred_sex[samples] == "inferred_female")),
  "age_available=false",
  "explicit_batch_available=false",
  "pc_proxy_warning=PCs may reflect lineage biology rather than technical batch"
)
writeLines(
  summary_lines,
  file.path(out, "RATA_v5_pituitary_expression_proxy_negative_controls.txt")
)
print(proxy_table)
print(sex_table)
print(sensitivity)
print(summary_lines)
