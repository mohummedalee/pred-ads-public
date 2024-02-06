## Structure of Folders
- `regressions/` contains regression analyses broken down by RQs, focusing on RQ1 and RQ2
- `fullstudy/` contains Jupyter notebooks attempting to do misc. descriptive analyses on data from the study itself, and not some pilot data. Many of these focus on RQ3 (targeting), e.g. `overall-targeting-differences.ipynb`
- `finegrained/` contains analyses comparing contextual (sensitive) vs. global (scam, prohibited, clickbait) harms


## Preparing Data for Regression
**N.B.** Most likely the data you need to re-run analyses is already in the repository, here are data prep instructions regardless.

Data that has been read directly from the database is available inside `db-processing`, e.g., files like
`ad_codes.tsv` or `survey_responses.tsv`. Based on which analysis you're planning on replicating, please
make sure you prepare by running the `prep_*.py` file that will take data from `db-processing` and turn it into
an R-friendly format.

**Example**: Run `prep_dislike_regression_data.py` to have fresh data to run `regressions/rq1/dislike_analysis.Rmd`.

I will continue to commit updated data files here in the repository as well to avoid everyone having to prep their own data.