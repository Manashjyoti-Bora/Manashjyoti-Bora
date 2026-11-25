# Security policy

This repository is a profile: Markdown, hand-coded SVG and GitHub Actions.
There is no server, no database and no secret in it — the workflows use the
repository's own `GITHUB_TOKEN` and nothing else.

## Reporting something

If you find a problem here — a workflow that could be made to run someone
else's code, an SVG that leaks data, a script that trusts input it should
not — please report it privately first:

- Email **manashjyotibora122@gmail.com** with `security:` in the subject, or
- Send a direct message on [LinkedIn](https://www.linkedin.com/in/manashjyoti-bora-323b97405).

I will confirm within 24 hours and credit you on the page if you want to be
named. Please do not open a public issue for an unfixed problem.

## Scope

| In scope | Out of scope |
|----------|--------------|
| This repository's workflows and scripts | The Vercel-hosted apps (see their own repos) |
| The SVG output in `assets/` | Third-party badges and stat cards linked from the README |
| The signature-margin issue workflow | Denial of service via opening issues |

The signature margin is deliberately hardened: logins are stripped to
`[A-Za-z0-9-]`, notes to printable ASCII, and the drawing escapes everything
before it reaches the SVG. If you can get markup through that filter, that is
a real finding — tell me.

## The one bug I already shipped

A client-side price was trusted on NexusMart and a developer bought
headphones for ₹1. It was fixed within hours and the server now rebuilds every
order from database prices only. That is why this page says *never trust the
frontend* — it is a lesson, not a slogan.
