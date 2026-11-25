# Security policy

This repository is a self-updating GitHub profile: Markdown, generated SVG, and
Python that runs only inside GitHub Actions. It has no server, no database and
no user accounts. The Live Repository still gets the normal care.

## Reporting

Email **manashjyotibora122@gmail.com** with `security` in the subject, or use
GitHub's private *Report a vulnerability* tab. Please do not open a public
issue for something exploitable.

| what | in scope | notes |
| --- | --- | --- |
| `.github/scripts/*.py` | yes | automation that writes to this repository |
| GitHub Action workflows | yes | especially token permissions and `pull_request_target` misuse |
| Generated SVG | yes | must never carry `<script>`, `<foreignObject>` or an external reference |
| Content on the profile page | no | typo reports are just issues, and welcome |

## The ₹1 story, in short

I once pushed a checkout that trusted a client-supplied price. It took a ₹1
test order to prove it. The fix was to compute totals on the server and
validate them against the database before charging. Same rule applies here:
**nothing a workflow writes is trusted until `doctor.py` has parsed it.**
