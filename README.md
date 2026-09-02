# RSI List

A cited directory of the organizations working toward recursive self-improvement — AI that improves the process of building AI.

**Live page:** https://rsi-list.com

## What it covers

No company has closed that loop yet, and claims in this field tend to run ahead of evidence, so every entry is graded on what it has publicly demonstrated rather than what it says. Alongside the ultimate goal of RSI, the list includes the adjacent areas some people count as RSI too:

| Category | What the loop does |
| --- | --- |
| **Auto research** | AI runs the whole research loop. |
| **Self-improvement** | The output flows back into the system itself, as training signal, memory, or better workflows. |
| **RSI** | What the output improves is the model's ability to improve itself. |

Ranked entries (#1–15) clear a scale / recognized-evidence / team bar; earlier-stage teams sit on the radar (◎) unranked. Every figure carries a confidence tag — ● confirmed, ◐ reported, ○ estimated — and a dated source linked from the entry.

## Repository

`index.html` is the entire site: one self-contained file with no build step and no dependencies. Open it directly in a browser, or serve the directory statically.

The data lives in the `DATA` array in the inline script at the bottom of the file. Each entry carries its own sources, so a change to a number should come with a change to the source beside it.

## Tagging

The table carries a **Tag** column so entries can be classified by what the company actually builds. Five tags, any number per company:

| Tag | What it covers |
| --- | --- |
| **Model** | Frontier / foundation model work |
| **Harness** | Agents, scaffolds, the loop around the model |
| **Infra** | Compute and training infrastructure |
| **Data/Eval** | Data pipelines, benchmarks, evaluation |
| **Applications** | Products built on top of the models |

Click the chips in the row to tag. Where the tags land depends on how the page is served:

```
python3 tools/tagserver.py --port 10045     # then open http://localhost:10045/
```

Served that way, every click is written through to the server — current state in `data/tags.json`, and one append-only line per change (who, when, before, after) in `data/tags-log.jsonl`. Opened any other way — from the filesystem, or off a plain static host — the page falls back to per-browser `localStorage` and says so under the table. The line under the count also takes a name, which is recorded with each change.

## Contributing

Corrections and additions are welcome — please open an issue or a pull request that includes a dated primary source for anything quantitative.

## Credits

Built and maintained by [Jinyan Su](https://jinyansu1.github.io), [Jiabin Tang](https://tjb-tech.github.io/), and [Yu Shi](https://x.com/chadshi_1).

Format inspired by [RL List](https://www.rl-list.com).

## License

Code is released under the [MIT License](LICENSE). The dataset — entries, figures, timelines, sources, and tags — is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); attribute as "RSI List (rsi-list.com)".
