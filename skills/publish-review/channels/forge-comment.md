# Channel: forge comment (GitHub, GitLab)

One comment on the PR/MR or issue, posted as the operator's authenticated CLI user. That is what makes its markers trusted: review-change's `rounds.py fetch` keeps only markers from the operator.

## Posting

Write the rendered comment to a scratch file, then post it with the forge's REST API (GraphQL-backed CLI commands may be unavailable):

| Target | Command |
| --- | --- |
| GitHub PR or issue | `gh api repos/<owner>/<repo>/issues/<n>/comments -F body=@<file>` (PR conversation comments are issue comments) |
| GitLab MR | `glab api projects/<project>/merge_requests/<n>/notes -F body=@<file>` |
| GitLab issue | `glab api projects/<project>/issues/<n>/notes -F body=@<file>` |

`<project>` is the numeric ID or the URL-encoded path (`group%2Frepo`). If the installed `glab api` does not read `@file` for fields, send a JSON body with `--input` instead; check `glab api --help` rather than guessing.

The response carries the comment's URL (`html_url` on GitHub; build it from `id` on GitLab). Report it.

## Verifying

`rounds.py fetch github --repo <owner>/<repo> --pr <n>` (or `--issue`, or the GitLab form). This round must appear with its head and the decisions just posted, and nothing must be listed under `ignored` that came from the operator. If the comment posted but the markers do not come back, say so — the next review would miss this round's decisions.

## Size

GitHub comments are limited to 65,536 characters. If the rendering exceeds about 60,000, move Minor and Observation details out of the comment: post them as a second comment first, then the main comment linking to it with the markers. Never drop the markers or the decisions table to fit.

## Linked work item

When the target is an MR and the report names a work item, post only on the MR. Review-change reads rounds from both places, so the work item needs no copy, and a second copy would split later decision updates between two threads.
