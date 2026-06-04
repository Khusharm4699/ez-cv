# Quantification Playbook

A strong engineering resume lives and dies on impact in numbers. For every
achievement, drive toward at least one of these axes:

| Axis | Question to ask the owner | Example |
|---|---|---|
| Time | Before vs after duration? | 30 min -> 4 min deploys |
| Percent | % faster / cheaper / more coverage? | 45% p99 latency cut |
| Count | How many users / requests / tests / bugs? | 12B+ events/day |
| Scale | How big is the data / fleet / cluster? | 2M writes/sec |
| Adoption | Who/how many teams use it? Is it mandated? | 300+ teams onboarded |
| Money | Cost / license / hours saved? | 38% storage cost cut |
| Reach | Audience for a talk / doc? | 180+ engineers taught |

## Rules

- Pair a metric with a mechanism: *how* you got the number (parallelization,
  caching, rate-limit tuning, sharding, etc.). Strong readers want the how.
- Prefer hard numbers; if unknown, ask. Only use `~` estimates with the owner's OK.
- One strong number per bullet beats three weak ones.
- Lead the bullet with the result, then the method: "Cut p99 ~45% by ...".

## Bullet shape (XYZ / STAR-lite)

> **[Action verb]** + **[what]** + **[quantified result]** + **[how / so that]**.

Good: "Cut settlement-service p99 from 820ms to 450ms (~45%) by batching writes
and adding a read-through Redis cache."

Weak: "Worked on improving service performance."
