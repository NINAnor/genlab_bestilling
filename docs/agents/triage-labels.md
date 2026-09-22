# Triage Labels

The skills speak in terms of five canonical triage roles. In this repo's tracker (ClickUp, list `901520431481` in the IT Utvikling space), those roles map to **tags** — ClickUp has no separate "label" concept.

| Role in mattpocock/skills | Tag in ClickUp    | Meaning                                  |
| ------------------------- | ------------------ | ----------------------------------------- |
| `needs-triage`             | `needs-triage`     | Maintainer needs to evaluate this issue   |
| `needs-info`               | `needs-info`       | Waiting on reporter for more information  |
| `ready-for-agent`          | `ready-for-agent`  | Fully specified, ready for an AFK agent   |
| `ready-for-human`          | `ready-for-human`  | Requires human implementation             |
| `wontfix`                  | `wontfix`          | Will not be actioned (pair with status `aborted`) |

Apply/remove with `clickup_add_tag_to_task` / `clickup_remove_tag_from_task`.

## Prerequisite: create the tags once

ClickUp tags must already exist in a space before they can be applied to a task — there is no "create tag" operation exposed through the MCP tools here. Before `/triage` is used for the first time, create these 5 tags manually in **Space Settings → Tags** for the **IT Utvikling** space:

`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`

Edit the right-hand column above if the space ends up using different tag names.
